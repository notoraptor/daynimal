"""
First-launch setup: download distribution from GitHub Releases, build minimal DB.

This module handles:
- Database resolution (find existing DB or fallback via .daynimal_config)
- Downloading compressed TSV files from GitHub Releases
- Verifying checksums
- Building the minimal SQLite database
- Initializing FTS5 search index
"""

import gzip
import hashlib
import json
import shutil
import sqlite3
from pathlib import Path
from typing import Callable, Optional

import httpx

from daynimal.config import settings


# Type for progress callback: (stage_name, progress_float_or_None)
ProgressCallback = Callable[[str, Optional[float]], None]

# Config file that stores path to active DB when default is absent
DB_CONFIG_FILENAME = ".daynimal_config"


def _get_db_path_from_url() -> Path:
    """Extract database file path from settings.database_url."""
    url = settings.database_url
    # "sqlite:///daynimal.db" -> "daynimal.db"
    if url.startswith("sqlite:///"):
        return Path(url[len("sqlite:///"):])
    return Path(url)


def _get_config_file_path() -> Path:
    """Get path to .daynimal_config file (same directory as default DB)."""
    db_path = _get_db_path_from_url()
    return db_path.parent / DB_CONFIG_FILENAME


def is_db_valid(db_path: Path) -> bool:
    """Check if a database file exists and contains taxa data.

    Args:
        db_path: Path to SQLite database file.

    Returns:
        True if the file exists and the taxa table has rows.
    """
    if not db_path.exists() or db_path.stat().st_size == 0:
        return False
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.execute("SELECT COUNT(*) FROM taxa")
        count = cursor.fetchone()[0]
        conn.close()
        return count > 0
    except Exception:
        return False


def save_db_config(db_path: Path) -> None:
    """Save the active database path to .daynimal_config.

    Args:
        db_path: Path to the active database file.
    """
    config_path = _get_config_file_path()
    config_path.write_text(
        json.dumps({"database_path": str(db_path)}, indent=2),
        encoding="utf-8",
    )


def resolve_database() -> Optional[Path]:
    """Find the active database, updating settings if needed.

    Resolution order:
    1. Default path from settings.database_url (e.g. daynimal.db)
    2. Path from .daynimal_config (e.g. daynimal_minimal.db)
    3. None (setup required)

    If resolved via .daynimal_config, settings.database_url is updated at runtime.

    Returns:
        Path to valid database, or None if setup is needed.
    """
    # 1. Try default path
    default_path = _get_db_path_from_url()
    if is_db_valid(default_path):
        return default_path

    # 2. Try .daynimal_config
    config_path = _get_config_file_path()
    if config_path.exists():
        try:
            config = json.loads(config_path.read_text(encoding="utf-8"))
            alt_path = Path(config["database_path"])
            if is_db_valid(alt_path):
                settings.database_url = f"sqlite:///{alt_path}"
                return alt_path
        except Exception:
            pass

    # 3. No valid DB found
    return None


def verify_checksum(file_path: Path, expected_sha256: str) -> bool:
    """Verify SHA256 checksum of a file.

    Args:
        file_path: Path to file to verify.
        expected_sha256: Expected hex digest.

    Returns:
        True if checksum matches.
    """
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            sha256.update(chunk)
    return sha256.hexdigest() == expected_sha256


def download_file(
    url: str,
    dest: Path,
    progress_callback: Optional[Callable[[int, Optional[int]], None]] = None,
) -> Path:
    """Download a file with streaming and optional progress reporting.

    Args:
        url: URL to download.
        dest: Destination file path.
        progress_callback: Called with (downloaded_bytes, total_bytes_or_None).

    Returns:
        Path to downloaded file.
    """
    with httpx.stream("GET", url, follow_redirects=True, timeout=60.0) as response:
        response.raise_for_status()
        total = int(response.headers.get("content-length", 0)) or None
        downloaded = 0
        with open(dest, "wb") as f:
            for chunk in response.iter_bytes(chunk_size=65536):
                f.write(chunk)
                downloaded += len(chunk)
                if progress_callback:
                    progress_callback(downloaded, total)
    return dest


def download_and_setup_db(
    progress_callback: Optional[ProgressCallback] = None,
) -> None:
    """Download distribution files and build the minimal database.

    Args:
        progress_callback: Called with (stage, progress).
            Stages: "download_manifest", "download_taxa", "download_vernacular",
                    "decompress", "build_db", "build_fts", "cleanup"
            Progress: 0.0-1.0 for downloads, None for indeterminate stages.

    Raises:
        Exception: On any failure (partial DB is cleaned up).
    """
    base_url = settings.distribution_base_url
    tmp_dir = Path("tmp")
    db_filename = "daynimal_minimal.db"
    db_path = Path(db_filename)

    def _progress(stage: str, progress: Optional[float] = None):
        if progress_callback:
            progress_callback(stage, progress)

    def _download_progress(stage: str):
        """Return a download progress callback for a given stage."""
        def callback(downloaded: int, total: Optional[int]):
            if total:
                _progress(stage, downloaded / total)
            else:
                _progress(stage, None)
        return callback

    try:
        # Create tmp directory
        tmp_dir.mkdir(exist_ok=True)

        # 1. Download manifest
        _progress("download_manifest", 0.0)
        manifest_path = tmp_dir / "manifest.json"
        download_file(f"{base_url}/manifest.json", manifest_path)
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        checksums = {f["name"]: f["sha256"] for f in manifest["files"]}
        _progress("download_manifest", 1.0)

        # 2. Download taxa
        taxa_gz = "animalia_taxa_minimal.tsv.gz"
        _progress("download_taxa", 0.0)
        taxa_gz_path = tmp_dir / taxa_gz
        download_file(
            f"{base_url}/{taxa_gz}",
            taxa_gz_path,
            _download_progress("download_taxa"),
        )
        if taxa_gz in checksums and not verify_checksum(taxa_gz_path, checksums[taxa_gz]):
            raise ValueError(f"Checksum mismatch for {taxa_gz}")

        # 3. Download vernacular
        vern_gz = "animalia_vernacular_minimal.tsv.gz"
        _progress("download_vernacular", 0.0)
        vern_gz_path = tmp_dir / vern_gz
        download_file(
            f"{base_url}/{vern_gz}",
            vern_gz_path,
            _download_progress("download_vernacular"),
        )
        if vern_gz in checksums and not verify_checksum(vern_gz_path, checksums[vern_gz]):
            raise ValueError(f"Checksum mismatch for {vern_gz}")

        # 4. Decompress
        _progress("decompress", None)
        taxa_tsv_path = tmp_dir / "animalia_taxa_minimal.tsv"
        vern_tsv_path = tmp_dir / "animalia_vernacular_minimal.tsv"

        for gz_path, tsv_path in [(taxa_gz_path, taxa_tsv_path), (vern_gz_path, vern_tsv_path)]:
            with gzip.open(gz_path, "rb") as f_in, open(tsv_path, "wb") as f_out:
                shutil.copyfileobj(f_in, f_out)

        # 5. Build database
        _progress("build_db", None)
        from daynimal.db.build_db import build_database
        build_database(taxa_tsv_path, vern_tsv_path, db_filename)

        # 6. Init FTS
        _progress("build_fts", None)
        from daynimal.db.init_fts import init_fts
        init_fts(db_path=db_filename)

        # 7. Save config
        save_db_config(db_path)

        # 8. Cleanup tmp
        _progress("cleanup", None)
        shutil.rmtree(tmp_dir, ignore_errors=True)

    except Exception:
        # Cleanup partial DB on failure
        if db_path.exists():
            db_path.unlink(missing_ok=True)
        raise
