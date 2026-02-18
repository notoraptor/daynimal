"""Image cache service for downloading and serving images locally."""

import hashlib
import logging
import time
from datetime import UTC, datetime
from pathlib import Path

import httpx

from daynimal.config import settings
from daynimal.db.models import ImageCacheModel
from daynimal.schemas import CommonsImage
from daynimal.sources.base import retry_with_backoff

logger = logging.getLogger(__name__)


class ImageCacheService:
    """Downloads and caches images locally for offline use."""

    def __init__(
        self,
        session,
        cache_dir: Path | None = None,
        max_size_mb: int | None = None,
        cache_hd: bool | None = None,
    ):
        self._session = session
        self._cache_dir = cache_dir or settings.image_cache_dir
        self._max_size_bytes = (
            (max_size_mb or settings.image_cache_max_size_mb) * 1024 * 1024
        )
        self._cache_hd = cache_hd if cache_hd is not None else settings.image_cache_hd
        self._client: httpx.Client | None = None
        self._cache_dir.mkdir(parents=True, exist_ok=True)
        # Ensure table exists (for existing databases without this table)
        ImageCacheModel.__table__.create(bind=session.get_bind(), checkfirst=True)

    @property
    def client(self) -> httpx.Client:
        if self._client is None:
            self._client = httpx.Client(
                timeout=settings.httpx_timeout,
                headers={
                    "User-Agent": "Daynimal/1.0 (https://github.com/notoraptor/daynimal)"
                },
                follow_redirects=True,
            )
        return self._client

    def close(self):
        if self._client is not None:
            self._client.close()
            self._client = None

    @staticmethod
    def _url_to_path(url: str, cache_dir: Path) -> Path:
        """Convert URL to local file path using SHA256 hash."""
        url_hash = hashlib.sha256(url.encode()).hexdigest()
        # Extract extension from URL
        ext = ".jpg"
        url_lower = url.lower()
        for candidate in (".png", ".gif", ".svg", ".webp", ".jpeg", ".tiff"):
            if candidate in url_lower:
                ext = candidate
                break
        subdir = cache_dir / url_hash[:2]
        return subdir / f"{url_hash}{ext}"

    def cache_images(self, images: list[CommonsImage]) -> None:
        """Download and cache images locally."""
        # Collect all URLs to download
        all_downloads: list[tuple[str, bool]] = []
        for image in images:
            if image.thumbnail_url:
                all_downloads.append((image.thumbnail_url, True))
            if self._cache_hd:
                all_downloads.append((image.url, False))
            elif not image.thumbnail_url:
                all_downloads.append((image.url, False))

        # Download with rate limiting to avoid 429 from Wikimedia
        for i, (url, is_thumb) in enumerate(all_downloads):
            if i > 0:
                time.sleep(0.5)
            self._download_and_store(url, is_thumb)

        # Purge if over limit
        cache_size = self.get_cache_size()
        if cache_size > self._max_size_bytes:
            self.purge_lru(self._max_size_bytes)

    def _download_and_store(self, url: str, is_thumbnail: bool) -> Path | None:
        """Download a single image and store it in cache."""
        # Check if already cached
        existing = (
            self._session.query(ImageCacheModel)
            .filter(ImageCacheModel.url == url)
            .first()
        )
        if existing:
            return Path(existing.local_path)

        # Download
        try:
            response = retry_with_backoff(lambda u=url: self.client.get(u))
            if response is None or response.status_code != 200:
                logger.warning(f"Failed to download image: {url}")
                return None

            data = response.content
        except Exception as e:
            logger.warning(f"Error downloading image {url}: {e}")
            return None

        # Save to disk
        local_path = self._url_to_path(url, self._cache_dir)
        local_path.parent.mkdir(parents=True, exist_ok=True)
        local_path.write_bytes(data)

        # Save to DB
        try:
            cache_entry = ImageCacheModel(
                url=url,
                local_path=str(local_path),
                size_bytes=len(data),
                downloaded_at=datetime.now(UTC),
                last_accessed_at=datetime.now(UTC),
                is_thumbnail=is_thumbnail,
            )
            self._session.add(cache_entry)
            self._session.commit()
        except Exception:
            self._session.rollback()
            # Remove file if DB insert failed
            local_path.unlink(missing_ok=True)
            raise

        return local_path

    def get_local_path(self, url: str) -> Path | None:
        """Get local path for a cached image, updating last_accessed_at."""
        entry = (
            self._session.query(ImageCacheModel)
            .filter(ImageCacheModel.url == url)
            .first()
        )
        if not entry:
            return None

        local_path = Path(entry.local_path)
        if not local_path.exists():
            # File was deleted externally, remove DB entry
            self._session.delete(entry)
            self._session.commit()
            return None

        # Update last accessed time
        entry.last_accessed_at = datetime.now(UTC)
        self._session.commit()
        return local_path

    def get_cache_size(self) -> int:
        """Get total cache size in bytes from DB."""
        from sqlalchemy import func

        result = self._session.query(func.sum(ImageCacheModel.size_bytes)).scalar()
        return result or 0

    def purge_lru(self, target_size_bytes: int) -> int:
        """Remove least recently accessed images until cache is under target size."""
        current_size = self.get_cache_size()
        if current_size <= target_size_bytes:
            return 0

        removed = 0
        # Get entries ordered by least recently accessed
        entries = (
            self._session.query(ImageCacheModel)
            .order_by(ImageCacheModel.last_accessed_at.asc())
            .all()
        )

        for entry in entries:
            if current_size <= target_size_bytes:
                break

            # Delete file
            local_path = Path(entry.local_path)
            local_path.unlink(missing_ok=True)

            current_size -= entry.size_bytes
            self._session.delete(entry)
            removed += 1

        self._session.commit()
        return removed

    def clear(self) -> int:
        """Clear all cached images."""
        entries = self._session.query(ImageCacheModel).all()
        count = len(entries)

        for entry in entries:
            Path(entry.local_path).unlink(missing_ok=True)
            self._session.delete(entry)

        self._session.commit()

        # Try to remove empty subdirectories
        if self._cache_dir.exists():
            for subdir in self._cache_dir.iterdir():
                if subdir.is_dir():
                    try:
                        subdir.rmdir()
                    except OSError:
                        pass

        return count
