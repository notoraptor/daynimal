"""Tests for ImageCacheService."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import httpx
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from daynimal.db.models import Base, ImageCacheModel
from daynimal.image_cache import ImageCacheService
from daynimal.schemas import CommonsImage


@pytest.fixture
def db_session():
    """Create an in-memory SQLite session for testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    yield session
    session.close()
    engine.dispose()


@pytest.fixture
def cache_dir(tmp_path):
    """Create a temporary cache directory."""
    return tmp_path / "cache" / "images"


@pytest.fixture
def service(db_session, cache_dir):
    """Create an ImageCacheService for testing."""
    svc = ImageCacheService(
        session=db_session, cache_dir=cache_dir, max_size_mb=10, cache_hd=False
    )
    yield svc
    svc.close()


@pytest.fixture
def sample_image():
    return CommonsImage(
        filename="Test.jpg",
        url="https://upload.wikimedia.org/wikipedia/commons/a/ab/Test.jpg",
        thumbnail_url="https://upload.wikimedia.org/wikipedia/commons/thumb/a/ab/Test.jpg/800px-Test.jpg",
    )


def _mock_response(content=b"fake image data", status_code=200):
    resp = MagicMock(spec=httpx.Response)
    resp.status_code = status_code
    resp.content = content
    return resp


class TestUrlToPath:
    def test_jpg_extension(self, cache_dir):
        path = ImageCacheService._url_to_path(
            "https://example.com/photo.jpg", cache_dir
        )
        assert path.suffix == ".jpg"
        assert len(path.parent.name) == 2

    def test_png_extension(self, cache_dir):
        path = ImageCacheService._url_to_path(
            "https://example.com/photo.png", cache_dir
        )
        assert path.suffix == ".png"

    def test_deterministic(self, cache_dir):
        url = "https://example.com/photo.jpg"
        path1 = ImageCacheService._url_to_path(url, cache_dir)
        path2 = ImageCacheService._url_to_path(url, cache_dir)
        assert path1 == path2


class TestCacheImages:
    @patch("daynimal.image_cache.retry_with_backoff")
    def test_cache_thumbnail(self, mock_retry, service, sample_image, db_session):
        mock_retry.return_value = _mock_response()

        service.cache_images([sample_image])

        entries = db_session.query(ImageCacheModel).all()
        # cache_hd=False, so only thumbnail is cached
        assert len(entries) == 1
        assert entries[0].is_thumbnail is True
        assert Path(entries[0].local_path).exists()

    @patch("daynimal.image_cache.retry_with_backoff")
    def test_cache_hd(self, mock_retry, db_session, cache_dir, sample_image):
        mock_retry.return_value = _mock_response()
        svc = ImageCacheService(
            session=db_session, cache_dir=cache_dir, max_size_mb=10, cache_hd=True
        )

        svc.cache_images([sample_image])

        entries = db_session.query(ImageCacheModel).all()
        # HD mode: thumbnail + original
        assert len(entries) == 2
        svc.close()

    @patch("daynimal.image_cache.retry_with_backoff")
    def test_skip_already_cached(self, mock_retry, service, sample_image, db_session):
        mock_retry.return_value = _mock_response()

        service.cache_images([sample_image])
        service.cache_images([sample_image])

        entries = db_session.query(ImageCacheModel).all()
        assert len(entries) == 1
        # retry_with_backoff called only once (not on second cache_images)
        assert mock_retry.call_count == 1

    @patch("daynimal.image_cache.retry_with_backoff")
    def test_failed_download(self, mock_retry, service, sample_image, db_session):
        mock_retry.return_value = None

        service.cache_images([sample_image])

        entries = db_session.query(ImageCacheModel).all()
        assert len(entries) == 0


class TestGetLocalPath:
    @patch("daynimal.image_cache.retry_with_backoff")
    def test_returns_path_if_cached(
        self, mock_retry, service, sample_image, db_session
    ):
        mock_retry.return_value = _mock_response()
        service.cache_images([sample_image])

        path = service.get_local_path(sample_image.thumbnail_url)
        assert path is not None
        assert path.exists()

    def test_returns_none_if_not_cached(self, service):
        path = service.get_local_path("https://example.com/nonexistent.jpg")
        assert path is None

    @patch("daynimal.image_cache.retry_with_backoff")
    def test_updates_last_accessed(self, mock_retry, service, sample_image, db_session):
        mock_retry.return_value = _mock_response()
        service.cache_images([sample_image])

        entry_before = db_session.query(ImageCacheModel).first()
        old_accessed = entry_before.last_accessed_at

        # Access again
        service.get_local_path(sample_image.thumbnail_url)

        db_session.refresh(entry_before)
        assert entry_before.last_accessed_at >= old_accessed


class TestCacheSize:
    @patch("daynimal.image_cache.retry_with_backoff")
    def test_cache_size(self, mock_retry, service, db_session):
        data = b"x" * 1000
        mock_retry.return_value = _mock_response(content=data)

        image = CommonsImage(
            filename="Test.jpg",
            url="https://example.com/test.jpg",
            thumbnail_url="https://example.com/test_thumb.jpg",
        )
        service.cache_images([image])

        assert service.get_cache_size() == 1000

    def test_empty_cache_size(self, service):
        assert service.get_cache_size() == 0


class TestPurgeLru:
    @patch("daynimal.image_cache.retry_with_backoff")
    def test_purge_oldest(self, mock_retry, service, db_session):
        mock_retry.return_value = _mock_response(content=b"x" * 500)

        for i in range(5):
            img = CommonsImage(
                filename=f"Test{i}.jpg",
                url=f"https://example.com/img{i}.jpg",
                thumbnail_url=f"https://example.com/thumb{i}.jpg",
            )
            service.cache_images([img])

        # Total: 5 * 500 = 2500 bytes
        assert service.get_cache_size() == 2500

        removed = service.purge_lru(1500)
        assert removed == 2
        assert service.get_cache_size() == 1500


class TestClear:
    @patch("daynimal.image_cache.retry_with_backoff")
    def test_clear(self, mock_retry, service, db_session):
        mock_retry.return_value = _mock_response()

        for i in range(3):
            img = CommonsImage(
                filename=f"Test{i}.jpg",
                url=f"https://example.com/img{i}.jpg",
                thumbnail_url=f"https://example.com/thumb{i}.jpg",
            )
            service.cache_images([img])

        count = service.clear()
        assert count == 3
        assert service.get_cache_size() == 0
        assert db_session.query(ImageCacheModel).count() == 0


class TestCacheSingleImage:
    @patch("daynimal.image_cache.retry_with_backoff")
    def test_caches_thumbnail(self, mock_retry, service, sample_image, db_session):
        mock_retry.return_value = _mock_response()

        service.cache_single_image(sample_image)

        entries = db_session.query(ImageCacheModel).all()
        assert len(entries) == 1
        assert entries[0].is_thumbnail is True

    @patch("daynimal.image_cache.retry_with_backoff")
    def test_caches_url_when_no_thumbnail(self, mock_retry, service, db_session):
        mock_retry.return_value = _mock_response()
        image = CommonsImage(
            filename="Test.jpg", url="https://example.com/test.jpg", thumbnail_url=None
        )

        service.cache_single_image(image)

        entries = db_session.query(ImageCacheModel).all()
        assert len(entries) == 1
        assert entries[0].is_thumbnail is False


class TestAreAllCached:
    @patch("daynimal.image_cache.retry_with_backoff")
    def test_returns_true_when_all_cached(
        self, mock_retry, service, sample_image, db_session
    ):
        mock_retry.return_value = _mock_response()
        service.cache_images([sample_image])

        assert service.are_all_cached([sample_image]) is True

    def test_returns_false_when_not_cached(self, service, sample_image):
        assert service.are_all_cached([sample_image]) is False

    def test_returns_true_for_empty_list(self, service):
        assert service.are_all_cached([]) is True

    @patch("daynimal.image_cache.retry_with_backoff")
    def test_returns_false_when_partially_cached(self, mock_retry, service, db_session):
        mock_retry.return_value = _mock_response()
        img1 = CommonsImage(
            filename="A.jpg",
            url="https://example.com/a.jpg",
            thumbnail_url="https://example.com/a_thumb.jpg",
        )
        img2 = CommonsImage(
            filename="B.jpg",
            url="https://example.com/b.jpg",
            thumbnail_url="https://example.com/b_thumb.jpg",
        )
        service.cache_images([img1])

        assert service.are_all_cached([img1, img2]) is False


class TestCacheImagesWithProgress:
    @patch("daynimal.image_cache.retry_with_backoff")
    def test_calls_on_progress(self, mock_retry, service, db_session):
        mock_retry.return_value = _mock_response()
        images = [
            CommonsImage(
                filename=f"Test{i}.jpg",
                url=f"https://example.com/img{i}.jpg",
                thumbnail_url=f"https://example.com/thumb{i}.jpg",
            )
            for i in range(3)
        ]

        progress_calls = []
        service.cache_images_with_progress(
            images, on_progress=lambda c, t: progress_calls.append((c, t))
        )

        assert len(progress_calls) == 3
        assert progress_calls[-1] == (3, 3)

    @patch("daynimal.image_cache.retry_with_backoff")
    def test_caches_all_images(self, mock_retry, service, db_session):
        mock_retry.return_value = _mock_response()
        images = [
            CommonsImage(
                filename=f"Test{i}.jpg",
                url=f"https://example.com/img{i}.jpg",
                thumbnail_url=f"https://example.com/thumb{i}.jpg",
            )
            for i in range(3)
        ]

        service.cache_images_with_progress(images)

        entries = db_session.query(ImageCacheModel).all()
        assert len(entries) == 3


# =============================================================================
# SECTION ÉTENDUE : Couverture lignes manquantes (88% → ~95%)
# Lignes: 82, 100, 102, 115, 124, 144, 155, 176-178, 197-201, 218-220, 238, 280-281
# =============================================================================


class TestImageCacheClientLifecycle:
    """Tests pour le cycle de vie du client HTTP (lazy init, close)."""

    def test_client_lazy_initialization(self, mock_retry, service):
        """Vérifie que le client HTTP n'est créé que lors du premier accès
        à service.client (lazy init). Avant l'accès, _client est None."""
        # todo
        pass

    def test_client_returns_same_instance(self, mock_retry, service):
        """Vérifie que deux accès consécutifs à service.client retournent
        le même objet httpx.Client."""
        # todo
        pass

    def test_close_closes_client(self, mock_retry, service):
        """Vérifie que service.close() appelle _client.close() si un client
        a été initialisé. Après close(), un nouvel accès à client devrait
        créer une nouvelle instance."""
        # todo
        pass


class TestDownloadAndStoreEdgeCases:
    """Tests pour _download_and_store — cas limites."""

    def test_non_200_response(self, mock_retry, service, db_session):
        """Vérifie que _download_and_store retourne None quand
        retry_with_backoff retourne None (échec HTTP après retries).
        Aucune entrée ne doit être ajoutée en DB."""
        # todo
        pass

    def test_db_insert_failure_rolls_back(self, mock_retry, service, db_session):
        """Vérifie que si l'insertion en DB échoue (ex: IntegrityError),
        le fichier téléchargé est supprimé et la session est rollback.
        L'exception ne doit pas se propager."""
        # todo
        pass

    def test_already_cached_returns_existing_path(self, mock_retry, service, db_session):
        """Vérifie que si l'URL est déjà dans le cache (entrée DB existante),
        _download_and_store retourne le chemin existant sans télécharger."""
        # todo
        pass


class TestGetLocalPathEdgeCases:
    """Tests pour get_local_path — cas limites."""

    def test_file_deleted_removes_db_entry(self, mock_retry, service, db_session):
        """Vérifie que si un fichier local a été supprimé du disque mais
        existe encore en DB, get_local_path supprime l'entrée DB et
        retourne None."""
        # todo
        pass


class TestClearEdgeCases:
    """Tests pour clear — gestion des erreurs OS."""

    def test_clear_handles_oserror_on_subdir_removal(self, mock_retry, service, db_session, tmp_path):
        """Vérifie que clear() ne plante pas si la suppression d'un
        sous-répertoire échoue (OSError). Les fichiers individuels sont
        supprimés et les sous-répertoires non-vides sont ignorés."""
        # todo
        pass


class TestCacheImagesHdMode:
    """Tests pour le mode HD du cache."""

    def test_hd_mode_downloads_thumbnail_and_original(self, mock_retry, db_session, tmp_path):
        """Vérifie qu'en mode cache_hd=True, _download_and_store est appelé
        deux fois par image: une fois pour le thumbnail et une fois pour
        l'URL originale."""
        # todo
        pass
