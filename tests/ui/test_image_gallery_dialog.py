"""Tests pour daynimal/ui/components/image_gallery_dialog.py — Dialog galerie.

Couvre: ImageGalleryDialog (open, download, carousel, navigation).

Strategie: on mock ImageCacheService et ft.Page. On verifie que open()
branche correctement entre le mode cached et download, que la progress
bar est mise a jour, et que la navigation fonctionne.
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import flet as ft
import pytest

from daynimal.schemas import CommonsImage, License, ImageSource
from daynimal.ui.components.image_gallery_dialog import ImageGalleryDialog


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def sample_images():
    """Cree une liste de CommonsImage pour les tests."""
    return [
        CommonsImage(
            filename="animal1.jpg",
            url="https://upload.wikimedia.org/animal1.jpg",
            thumbnail_url="https://upload.wikimedia.org/thumb/animal1.jpg",
            width=800,
            height=600,
            author="Alice",
            license=License.CC_BY_SA,
            description="First animal image",
            image_source=ImageSource.COMMONS,
            source_page_url="https://commons.wikimedia.org/wiki/File:animal1.jpg",
        ),
        CommonsImage(
            filename="animal2.jpg",
            url="https://upload.wikimedia.org/animal2.jpg",
            thumbnail_url="https://upload.wikimedia.org/thumb/animal2.jpg",
            width=1024,
            height=768,
            author="Bob",
            license=License.CC_BY,
            description="Second animal image",
            image_source=ImageSource.GBIF,
            source_page_url="https://gbif.org/image/animal2.jpg",
        ),
        CommonsImage(
            filename="animal3.jpg",
            url="https://upload.wikimedia.org/animal3.jpg",
            thumbnail_url="https://upload.wikimedia.org/thumb/animal3.jpg",
            width=640,
            height=480,
            author="Charlie",
            license=License.CC0,
            description="Third animal image",
            image_source=ImageSource.PHYLOPIC,
            source_page_url="https://phylopic.org/image/animal3",
        ),
    ]


@pytest.fixture
def mock_image_cache():
    """Cree un mock d'ImageCacheService."""
    cache = MagicMock()
    cache.are_all_cached = MagicMock(return_value=False)
    cache.get_local_path = MagicMock(return_value=None)
    cache.cache_images_with_progress = MagicMock()
    return cache


@pytest.fixture
def mock_page():
    """Cree un mock de ft.Page."""
    page = MagicMock(spec=ft.Page)
    page.show_dialog = MagicMock()
    page.pop_dialog = MagicMock()
    page.run_task = MagicMock()
    page.update = MagicMock()
    return page


# =============================================================================
# SECTION 1 : open()
# =============================================================================


class TestImageGalleryDialogOpen:
    """Tests pour ImageGalleryDialog.open()."""

    def test_all_cached_shows_carousel_directly(
        self, mock_page, mock_image_cache, sample_images
    ):
        """Verifie que quand image_cache.are_all_cached(images) retourne True,
        open() appelle _show_carousel_dialog() directement (pas de telechargement).
        On verifie que page.show_dialog est appele avec un AlertDialog
        contenant les controles carousel."""
        mock_image_cache.are_all_cached.return_value = True
        mock_image_cache.get_local_path.return_value = Path("/fake/cache/image.jpg")

        gallery = ImageGalleryDialog(
            images=sample_images,
            image_cache=mock_image_cache,
            page=mock_page,
            animal_display_name="Test Animal",
        )
        gallery.open()

        # are_all_cached was checked
        mock_image_cache.are_all_cached.assert_called_once_with(sample_images)

        # show_dialog was called (carousel dialog, not download dialog)
        mock_page.show_dialog.assert_called_once()

        # run_task should NOT have been called (no download needed)
        mock_page.run_task.assert_not_called()

        # Verify the dialog is an AlertDialog with carousel content
        shown_dialog = mock_page.show_dialog.call_args[0][0]
        assert isinstance(shown_dialog, ft.AlertDialog)
        assert shown_dialog.title.value == "Galerie d'images"

        # The content column should have carousel controls (Image counter, ft.Image, etc.)
        content_column = shown_dialog.content.content
        assert isinstance(content_column, ft.Column)
        # First control should be the image counter text
        counter_text = content_column.controls[0]
        assert isinstance(counter_text, ft.Text)
        assert "1/3" in counter_text.value

    def test_not_cached_shows_download_dialog(
        self, mock_page, mock_image_cache, sample_images
    ):
        """Verifie que quand are_all_cached retourne False, open() appelle
        _show_download_dialog() qui affiche un dialog avec une progress bar
        et lance le telechargement en arriere-plan via page.run_task."""
        mock_image_cache.are_all_cached.return_value = False

        gallery = ImageGalleryDialog(
            images=sample_images,
            image_cache=mock_image_cache,
            page=mock_page,
            animal_display_name="Test Animal",
        )
        gallery.open()

        # are_all_cached was checked
        mock_image_cache.are_all_cached.assert_called_once_with(sample_images)

        # show_dialog was called with download dialog
        mock_page.show_dialog.assert_called_once()

        # run_task was called to start the background download
        mock_page.run_task.assert_called_once()

        # The argument to run_task should be the _download_all coroutine function
        run_task_arg = mock_page.run_task.call_args[0][0]
        assert callable(run_task_arg)

        # Verify the dialog contains a progress bar
        shown_dialog = mock_page.show_dialog.call_args[0][0]
        assert isinstance(shown_dialog, ft.AlertDialog)
        content_column = shown_dialog.content.content
        assert isinstance(content_column, ft.Column)
        # Should contain progress text and progress bar
        control_types = [type(c) for c in content_column.controls]
        assert ft.Text in control_types
        assert ft.ProgressBar in control_types


# =============================================================================
# SECTION 2 : Download dialog
# =============================================================================


class TestDownloadDialog:
    """Tests pour _show_download_dialog et _download_all."""

    def test_download_dialog_has_progress_bar(
        self, mock_page, mock_image_cache, sample_images
    ):
        """Verifie que le dialog de telechargement contient une ProgressBar
        et un texte indiquant le nombre d'images a telecharger."""
        mock_image_cache.are_all_cached.return_value = False

        gallery = ImageGalleryDialog(
            images=sample_images, image_cache=mock_image_cache, page=mock_page
        )
        gallery._show_download_dialog()

        shown_dialog = mock_page.show_dialog.call_args[0][0]
        content_column = shown_dialog.content.content

        # Find progress bar
        progress_bars = [
            c for c in content_column.controls if isinstance(c, ft.ProgressBar)
        ]
        assert len(progress_bars) == 1
        assert progress_bars[0].value == 0

        # Find text with image count
        texts = [c for c in content_column.controls if isinstance(c, ft.Text)]
        assert len(texts) >= 1
        # Text should mention the number of images (3)
        progress_text = texts[0]
        assert "0/3" in progress_text.value
        assert "chargement" in progress_text.value.lower()

    def test_download_dialog_has_cancel_button(
        self, mock_page, mock_image_cache, sample_images
    ):
        """Verifie que le dialog a un bouton 'Fermer' qui ferme le dialog
        via page.pop_dialog."""
        mock_image_cache.are_all_cached.return_value = False

        gallery = ImageGalleryDialog(
            images=sample_images, image_cache=mock_image_cache, page=mock_page
        )
        gallery._show_download_dialog()

        shown_dialog = mock_page.show_dialog.call_args[0][0]

        # Check actions contain a close button
        assert shown_dialog.actions is not None
        assert len(shown_dialog.actions) >= 1

        close_button = shown_dialog.actions[0]
        assert isinstance(close_button, ft.Button)
        assert (
            getattr(close_button, "text", None) == "Fermer"
            or getattr(close_button, "content", None) == "Fermer"
        )

        # Simulate clicking the button - it should call page.pop_dialog
        close_button.on_click(MagicMock())
        mock_page.pop_dialog.assert_called_once()

    @pytest.mark.asyncio
    async def test_download_all_updates_progress(
        self, mock_page, mock_image_cache, sample_images
    ):
        """Verifie que _download_all appelle cache_images_with_progress
        en thread et met a jour _progress_bar.value progressivement.
        Mock: asyncio.to_thread execute la fonction synchronement."""
        mock_image_cache.are_all_cached.return_value = False

        gallery = ImageGalleryDialog(
            images=sample_images, image_cache=mock_image_cache, page=mock_page
        )
        # Initialize the download dialog state (creates _progress_bar, etc.)
        gallery._show_download_dialog()

        # Make cache_images_with_progress simulate progress callbacks
        def fake_cache_with_progress(images, on_progress):
            total = len(images)
            for i in range(1, total + 1):
                on_progress(i, total)

        mock_image_cache.cache_images_with_progress.side_effect = (
            fake_cache_with_progress
        )

        # Mock asyncio.to_thread to run synchronously
        with patch(
            "daynimal.ui.components.image_gallery_dialog.asyncio.to_thread"
        ) as mock_to_thread:

            async def run_sync(func, *args):
                func(*args)

            mock_to_thread.side_effect = run_sync

            await gallery._download_all()

        # cache_images_with_progress was called with images and a callback
        mock_image_cache.cache_images_with_progress.assert_called_once()
        call_args = mock_image_cache.cache_images_with_progress.call_args
        assert call_args[0][0] is sample_images

        # After completion, progress bar should be at 1.0 (3/3)
        assert gallery._progress_bar.value == 1.0

        # Progress text should show final state
        assert "3/3" in gallery._progress_text.value

        # page.update was called during progress updates and after switch to carousel
        assert mock_page.update.call_count >= 1

    @pytest.mark.asyncio
    async def test_download_all_switches_to_carousel(
        self, mock_page, mock_image_cache, sample_images
    ):
        """Verifie qu'apres le telechargement, _download_all remplace
        le contenu du dialog par les controles carousel et appelle
        page.update()."""
        mock_image_cache.are_all_cached.return_value = False
        mock_image_cache.get_local_path.return_value = Path("/fake/cache/img.jpg")

        gallery = ImageGalleryDialog(
            images=sample_images, image_cache=mock_image_cache, page=mock_page
        )
        gallery._show_download_dialog()

        # Mock asyncio.to_thread to run synchronously (no actual download)
        with patch(
            "daynimal.ui.components.image_gallery_dialog.asyncio.to_thread"
        ) as mock_to_thread:

            async def run_sync(func, *args):
                func(*args)

            mock_to_thread.side_effect = run_sync
            await gallery._download_all()

        # After download, the dialog content should have carousel controls
        controls = gallery._dialog_content.controls
        # Carousel controls start with image counter text
        counter_text = controls[0]
        assert isinstance(counter_text, ft.Text)
        assert "1/3" in counter_text.value

        # Should have an ft.Image control
        images_in_controls = [c for c in controls if isinstance(c, ft.Image)]
        assert len(images_in_controls) == 1

        # Should have navigation row (since we have 3 images > 1)
        rows = [c for c in controls if isinstance(c, ft.Row)]
        assert len(rows) >= 1

        # page.update was called at the end
        mock_page.update.assert_called()


# =============================================================================
# SECTION 3 : Carousel dialog
# =============================================================================


class TestCarouselDialog:
    """Tests pour _show_carousel_dialog et _build_carousel_controls."""

    def test_carousel_dialog_has_close_button(
        self, mock_page, mock_image_cache, sample_images
    ):
        """Verifie que le dialog carousel a un bouton 'Fermer' qui appelle
        page.pop_dialog."""
        mock_image_cache.are_all_cached.return_value = True
        mock_image_cache.get_local_path.return_value = None

        gallery = ImageGalleryDialog(
            images=sample_images, image_cache=mock_image_cache, page=mock_page
        )
        gallery._show_carousel_dialog()

        shown_dialog = mock_page.show_dialog.call_args[0][0]
        assert isinstance(shown_dialog, ft.AlertDialog)
        assert len(shown_dialog.actions) >= 1

        close_button = shown_dialog.actions[0]
        assert isinstance(close_button, ft.Button)
        assert (
            getattr(close_button, "text", None) == "Fermer"
            or getattr(close_button, "content", None) == "Fermer"
        )

        # Click the close button
        close_button.on_click(MagicMock())
        mock_page.pop_dialog.assert_called_once()

    def test_build_carousel_controls_shows_counter(
        self, mock_page, mock_image_cache, sample_images
    ):
        """Verifie que _build_carousel_controls affiche un compteur
        'Image 1 / 3' (ou equivalent) base sur current_index et len(images)."""
        mock_image_cache.get_local_path.return_value = None

        gallery = ImageGalleryDialog(
            images=sample_images, image_cache=mock_image_cache, page=mock_page
        )

        # Test at index 0
        gallery.current_index = 0
        controls = gallery._build_carousel_controls()
        counter = controls[0]
        assert isinstance(counter, ft.Text)
        assert "1/3" in counter.value

        # Test at index 1
        gallery.current_index = 1
        controls = gallery._build_carousel_controls()
        counter = controls[0]
        assert "2/3" in counter.value

        # Test at index 2
        gallery.current_index = 2
        controls = gallery._build_carousel_controls()
        counter = controls[0]
        assert "3/3" in counter.value

    def test_build_carousel_controls_uses_cached_path(
        self, mock_page, mock_image_cache, sample_images
    ):
        """Verifie que _build_carousel_controls appelle get_local_path
        pour l'image courante et utilise le chemin local si disponible."""
        fake_local_path = Path("/fake/cache/ab/abc123.jpg")
        mock_image_cache.get_local_path.return_value = fake_local_path

        gallery = ImageGalleryDialog(
            images=sample_images, image_cache=mock_image_cache, page=mock_page
        )
        gallery.current_index = 0

        controls = gallery._build_carousel_controls()

        # get_local_path should have been called for the current image's URLs
        mock_image_cache.get_local_path.assert_called()

        # The ft.Image should use the local path
        image_controls = [c for c in controls if isinstance(c, ft.Image)]
        assert len(image_controls) == 1
        assert str(fake_local_path) in image_controls[0].src


# =============================================================================
# SECTION 4 : Navigation dans la galerie
# =============================================================================


class TestGalleryNavigation:
    """Tests pour _on_prev, _on_next, _refresh_carousel."""

    def test_on_prev_wraps_modulo(self, mock_page, mock_image_cache, sample_images):
        """Verifie que _on_prev avec current_index=0 et 3 images passe a
        current_index=2 (modulo). Appelle ensuite _refresh_carousel."""
        mock_image_cache.get_local_path.return_value = None

        gallery = ImageGalleryDialog(
            images=sample_images, image_cache=mock_image_cache, page=mock_page
        )
        # Initialize _dialog_content so _refresh_carousel works
        gallery._dialog_content = ft.Column(controls=[])
        gallery.current_index = 0

        gallery._on_prev(MagicMock())

        # Should wrap to the last image
        assert gallery.current_index == 2

        # page.update should have been called by _refresh_carousel
        mock_page.update.assert_called()

    def test_on_next_wraps_modulo(self, mock_page, mock_image_cache, sample_images):
        """Verifie que _on_next avec current_index=2 et 3 images passe a
        current_index=0 (modulo). Appelle _refresh_carousel."""
        mock_image_cache.get_local_path.return_value = None

        gallery = ImageGalleryDialog(
            images=sample_images, image_cache=mock_image_cache, page=mock_page
        )
        # Initialize _dialog_content so _refresh_carousel works
        gallery._dialog_content = ft.Column(controls=[])
        gallery.current_index = 2

        gallery._on_next(MagicMock())

        # Should wrap to the first image
        assert gallery.current_index == 0

        # page.update should have been called by _refresh_carousel
        mock_page.update.assert_called()

    def test_refresh_carousel_updates_dialog(
        self, mock_page, mock_image_cache, sample_images
    ):
        """Verifie que _refresh_carousel reconstruit les controles carousel
        et appelle page.update() pour rafraichir l'affichage."""
        mock_image_cache.get_local_path.return_value = None

        gallery = ImageGalleryDialog(
            images=sample_images, image_cache=mock_image_cache, page=mock_page
        )
        gallery._dialog_content = ft.Column(controls=[ft.Text("old content")])
        gallery.current_index = 1

        gallery._refresh_carousel()

        # Controls should have been rebuilt (no longer "old content")
        controls = gallery._dialog_content.controls
        assert len(controls) > 1
        # First control should be the counter for image 2/3
        counter = controls[0]
        assert isinstance(counter, ft.Text)
        assert "2/3" in counter.value

        # page.update was called
        mock_page.update.assert_called_once()
