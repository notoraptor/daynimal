"""Tests pour daynimal/ui/components/image_carousel.py -- Carousel d'images.

Couvre: ImageCarousel (build, navigation, empty state, cached paths,
PhyloPic badge, credit text).

Strategie: on cree un ImageCarousel avec des CommonsImage mockees et
un mock d'ImageCacheService. On verifie la structure des controles
retournes par build() et le comportement des handlers de navigation.
"""

from unittest.mock import MagicMock

import flet as ft
import pytest

from daynimal.schemas import CommonsImage, ImageSource, License
from daynimal.ui.components.image_carousel import ImageCarousel


# =============================================================================
# Helpers
# =============================================================================


def _find_controls_of_type(control, control_type, results=None):
    """Recursively find all controls of a given type in a control tree."""
    if results is None:
        results = []
    if isinstance(control, control_type):
        results.append(control)
    # Check .controls attribute (Column, Row, etc.)
    if hasattr(control, "controls") and control.controls:
        for child in control.controls:
            _find_controls_of_type(child, control_type, results)
    # Check .content attribute (Container, etc.)
    if hasattr(control, "content") and control.content:
        _find_controls_of_type(control.content, control_type, results)
    return results


def _find_texts(control):
    """Find all ft.Text controls in a tree."""
    return _find_controls_of_type(control, ft.Text)


def _find_icon_buttons(control):
    """Find all ft.IconButton controls in a tree."""
    return _find_controls_of_type(control, ft.IconButton)


def _find_icons(control):
    """Find all ft.Icon controls in a tree."""
    return _find_controls_of_type(control, ft.Icon)


def _find_images(control):
    """Find all ft.Image controls in a tree."""
    return _find_controls_of_type(control, ft.Image)


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def sample_images():
    """Cree une liste de CommonsImage pour les tests."""
    return [
        CommonsImage(
            filename="Animal1.jpg",
            url="https://upload.wikimedia.org/wikipedia/commons/Animal1.jpg",
            thumbnail_url="https://upload.wikimedia.org/wikipedia/commons/thumb/Animal1.jpg",
            author="Alice Photo",
            license=License.CC_BY_SA,
            description="First image",
            image_source=ImageSource.COMMONS,
        ),
        CommonsImage(
            filename="Animal2.jpg",
            url="https://upload.wikimedia.org/wikipedia/commons/Animal2.jpg",
            thumbnail_url="https://upload.wikimedia.org/wikipedia/commons/thumb/Animal2.jpg",
            author="Bob Photo",
            license=License.CC_BY,
            description="Second image",
            image_source=ImageSource.COMMONS,
        ),
        CommonsImage(
            filename="Animal3.jpg",
            url="https://upload.wikimedia.org/wikipedia/commons/Animal3.jpg",
            thumbnail_url="https://upload.wikimedia.org/wikipedia/commons/thumb/Animal3.jpg",
            author="Carol Photo",
            license=License.CC0,
            description="Third image",
            image_source=ImageSource.COMMONS,
        ),
    ]


@pytest.fixture
def mock_image_cache():
    """Cree un mock d'ImageCacheService."""
    cache = MagicMock()
    cache.get_local_path.return_value = None
    return cache


# =============================================================================
# SECTION 1 : Build avec images
# =============================================================================


class TestImageCarouselBuild:
    """Tests pour ImageCarousel.build()."""

    def test_no_images_shows_empty_state(self, mock_image_cache):
        """Verifie que build() avec images=[] retourne un container
        d'etat vide contenant l'icone IMAGE et le texte
        'Aucune image disponible'."""
        carousel = ImageCarousel(images=[], image_cache=mock_image_cache)
        result = carousel.build()

        # Should be a Container (empty state)
        assert isinstance(result, ft.Container)

        # Find the icon
        icons = _find_icons(result)
        assert len(icons) >= 1
        assert icons[0].icon == ft.Icons.IMAGE

        # Find the text
        texts = _find_texts(result)
        text_values = [t.value for t in texts]
        assert any("Aucune image disponible" in v for v in text_values)

    def test_single_image_disables_navigation(self, mock_image_cache):
        """Verifie que build() avec une seule image n'affiche pas de
        boutons de navigation (remplaces par un Container vide)."""
        single_image = CommonsImage(
            filename="Solo.jpg",
            url="https://example.com/solo.jpg",
            thumbnail_url="https://example.com/thumb/solo.jpg",
            author="Photographer",
            license=License.CC_BY,
            image_source=ImageSource.COMMONS,
        )
        carousel = ImageCarousel(images=[single_image], image_cache=mock_image_cache)
        result = carousel.build()

        # With a single image, total_images <= 1, so we get a Container()
        # instead of Row with navigation buttons
        icon_buttons = _find_icon_buttons(result)
        assert len(icon_buttons) == 0

    def test_multiple_images_shows_counter(self, mock_image_cache, sample_images):
        """Verifie que build() avec 3 images affiche un compteur '1/3'
        (format: index+1/total)."""
        carousel = ImageCarousel(images=sample_images, image_cache=mock_image_cache)
        result = carousel.build()

        texts = _find_texts(result)
        text_values = [t.value for t in texts]
        # Counter should show "Image 1/3"
        assert any("1/3" in v for v in text_values)

    def test_multiple_images_enables_navigation(self, mock_image_cache, sample_images):
        """Verifie que les boutons precedent/suivant sont actives
        (disabled=False) quand il y a plusieurs images."""
        carousel = ImageCarousel(images=sample_images, image_cache=mock_image_cache)
        result = carousel.build()

        icon_buttons = _find_icon_buttons(result)
        assert len(icon_buttons) == 2
        for btn in icon_buttons:
            assert btn.disabled is False

    def test_uses_cached_local_path(self, mock_image_cache, sample_images):
        """Verifie que build() appelle image_cache.get_local_path()
        pour l'image courante et utilise le chemin local retourne
        comme source de ft.Image au lieu de l'URL distante."""
        local = "/cache/images/Animal1_thumb.jpg"
        # get_local_path returns local path for the thumbnail URL
        mock_image_cache.get_local_path.side_effect = lambda url: (
            local if "thumb/Animal1" in url else None
        )

        carousel = ImageCarousel(
            images=sample_images, current_index=0, image_cache=mock_image_cache
        )
        result = carousel.build()

        images = _find_images(result)
        assert len(images) >= 1
        assert images[0].src == local

    def test_fallback_to_url_when_not_cached(self, mock_image_cache, sample_images):
        """Verifie que quand get_local_path retourne None,
        l'URL de l'image (url) est utilisee directement."""
        # mock_image_cache already returns None by default
        carousel = ImageCarousel(
            images=sample_images, current_index=0, image_cache=mock_image_cache
        )
        result = carousel.build()

        images = _find_images(result)
        assert len(images) >= 1
        # Should fall back to the original URL
        assert images[0].src == sample_images[0].url


# =============================================================================
# SECTION 2 : PhyloPic badge et credits
# =============================================================================


class TestImageCarouselBadgeAndCredits:
    """Tests pour l'affichage du badge PhyloPic et des credits."""

    def test_phylopic_badge_shown(self, mock_image_cache):
        """Verifie que quand image.image_source == ImageSource.PHYLOPIC,
        un badge 'Silhouette' est affiche sous l'image."""
        phylopic_image = CommonsImage(
            filename="phylopic_abc.svg",
            url="https://images.phylopic.org/images/abc/vector.svg",
            thumbnail_url="https://images.phylopic.org/images/abc/vector.svg",
            author="Artist Name",
            license=License.CC0,
            image_source=ImageSource.PHYLOPIC,
            source_page_url="https://www.phylopic.org/images/abc",
            mime_type="image/svg+xml",
        )
        carousel = ImageCarousel(images=[phylopic_image], image_cache=mock_image_cache)
        result = carousel.build()

        texts = _find_texts(result)
        text_values = [t.value for t in texts]
        assert any("Silhouette" in v for v in text_values)

    def test_phylopic_badge_hidden_for_commons(self, mock_image_cache):
        """Verifie que le badge PhyloPic n'est PAS affiche pour les images
        de source COMMONS."""
        commons_image = CommonsImage(
            filename="CommonPhoto.jpg",
            url="https://upload.wikimedia.org/wikipedia/commons/CommonPhoto.jpg",
            thumbnail_url="https://upload.wikimedia.org/wikipedia/commons/thumb/CommonPhoto.jpg",
            author="Photographer",
            license=License.CC_BY_SA,
            image_source=ImageSource.COMMONS,
        )
        carousel = ImageCarousel(images=[commons_image], image_cache=mock_image_cache)
        result = carousel.build()

        texts = _find_texts(result)
        text_values = [t.value for t in texts if t.value]
        # "Silhouette" should NOT appear for Commons images
        assert not any("Silhouette" in v for v in text_values)

    def test_credit_text_shown_with_author(self, mock_image_cache):
        """Verifie que le texte de credit (auteur + source_label) est affiche
        quand l'image a un author non-vide."""
        image = CommonsImage(
            filename="Credited.jpg",
            url="https://example.com/credited.jpg",
            thumbnail_url="https://example.com/thumb/credited.jpg",
            author="Jane Doe",
            license=License.CC_BY,
            image_source=ImageSource.COMMONS,
        )
        carousel = ImageCarousel(images=[image], image_cache=mock_image_cache)
        result = carousel.build()

        texts = _find_texts(result)
        # Should find a credit text containing the author name
        credit_texts = [t for t in texts if t.value and "Jane Doe" in t.value]
        assert len(credit_texts) >= 1
        credit = credit_texts[0]
        assert credit.italic is True
        # Should also mention the source label
        assert image.source_label in credit.value

    def test_credit_text_hidden_without_author(self, mock_image_cache):
        """Verifie que le texte de credit n'est pas affiche quand
        l'image n'a pas d'auteur (author=None ou '')."""
        image = CommonsImage(
            filename="NoAuthor.jpg",
            url="https://example.com/noauthor.jpg",
            thumbnail_url="https://example.com/thumb/noauthor.jpg",
            author=None,
            license=License.CC_BY,
            image_source=ImageSource.COMMONS,
        )
        carousel = ImageCarousel(images=[image], image_cache=mock_image_cache)
        result = carousel.build()

        texts = _find_texts(result)
        # No text should contain "Cr\u00e9dit:" since author is None
        credit_texts = [t for t in texts if t.value and "dit:" in t.value]
        assert len(credit_texts) == 0


# =============================================================================
# SECTION 3 : Navigation
# =============================================================================


class TestImageCarouselNavigation:
    """Tests pour _on_prev et _on_next."""

    def test_on_prev_decrements_index(self, mock_image_cache, sample_images):
        """Verifie que _on_prev avec index=1 appelle on_index_change(0)."""
        callback = MagicMock()
        carousel = ImageCarousel(
            images=sample_images,
            current_index=1,
            on_index_change=callback,
            image_cache=mock_image_cache,
        )

        carousel._on_prev(None)

        callback.assert_called_once_with(0)
        assert carousel.current_index == 0

    def test_on_prev_wraps_to_last(self, mock_image_cache, sample_images):
        """Verifie que _on_prev avec index=0 et 3 images appelle
        on_index_change(2) (modulo wrap)."""
        callback = MagicMock()
        carousel = ImageCarousel(
            images=sample_images,
            current_index=0,
            on_index_change=callback,
            image_cache=mock_image_cache,
        )

        carousel._on_prev(None)

        callback.assert_called_once_with(2)
        assert carousel.current_index == 2

    def test_on_next_increments_index(self, mock_image_cache, sample_images):
        """Verifie que _on_next avec index=0 appelle on_index_change(1)."""
        callback = MagicMock()
        carousel = ImageCarousel(
            images=sample_images,
            current_index=0,
            on_index_change=callback,
            image_cache=mock_image_cache,
        )

        carousel._on_next(None)

        callback.assert_called_once_with(1)
        assert carousel.current_index == 1

    def test_on_next_wraps_to_first(self, mock_image_cache, sample_images):
        """Verifie que _on_next avec index=2 et 3 images appelle
        on_index_change(0) (modulo wrap)."""
        callback = MagicMock()
        carousel = ImageCarousel(
            images=sample_images,
            current_index=2,
            on_index_change=callback,
            image_cache=mock_image_cache,
        )

        carousel._on_next(None)

        callback.assert_called_once_with(0)
        assert carousel.current_index == 0


# =============================================================================
# SECTION 4 : Error content
# =============================================================================


class TestImageCarouselErrorContent:
    """Tests pour _build_error_content."""

    def test_error_content_shows_image_icon(self, mock_image_cache):
        """Verifie que _build_error_content retourne un container avec
        une icone IMAGE et le texte 'Erreur de chargement'."""
        image = CommonsImage(
            filename="Broken.jpg",
            url="https://example.com/broken.jpg",
            thumbnail_url="https://example.com/thumb/broken.jpg",
            author="Someone",
            license=License.CC_BY,
            image_source=ImageSource.COMMONS,
        )
        carousel = ImageCarousel(
            images=[image],
            animal_display_name="Test Animal",
            animal_taxon_id=42,
            image_cache=mock_image_cache,
        )
        error_content = carousel._build_error_content(image)

        assert isinstance(error_content, ft.Container)
        icons = _find_icons(error_content)
        assert len(icons) >= 1
        assert icons[0].icon == ft.Icons.IMAGE

        texts = _find_texts(error_content)
        text_values = [t.value for t in texts]
        assert any("Erreur de chargement" in v for v in text_values)

    def test_error_content_truncates_long_url(self, mock_image_cache):
        """Verifie que _build_error_content tronque les URLs tres longues
        dans le texte d'erreur (80 premiers caracteres + '...')."""
        long_url = "https://example.com/" + "a" * 200 + ".jpg"
        image = CommonsImage(
            filename="LongUrl.jpg",
            url=long_url,
            thumbnail_url=None,
            author="Someone",
            license=License.CC_BY,
            image_source=ImageSource.COMMONS,
        )
        carousel = ImageCarousel(
            images=[image],
            animal_display_name="Long URL Animal",
            animal_taxon_id=99,
            image_cache=mock_image_cache,
        )
        error_content = carousel._build_error_content(image)

        texts = _find_texts(error_content)
        url_texts = [t for t in texts if t.value and "URL:" in t.value]
        assert len(url_texts) >= 1
        url_text = url_texts[0].value
        # The URL should be truncated: first 80 chars + "..."
        assert url_text.endswith("...")
        # The full long_url should NOT be in the text
        assert long_url not in url_text
        # But the first 80 chars should be
        assert long_url[:80] in url_text
