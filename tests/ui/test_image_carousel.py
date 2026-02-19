"""Tests pour daynimal/ui/components/image_carousel.py — Carousel d'images.

Couvre: ImageCarousel (build, navigation, empty state, cached paths,
PhyloPic badge, credit text).

Stratégie: on crée un ImageCarousel avec des CommonsImage mockées et
un mock d'ImageCacheService. On vérifie la structure des contrôles
retournés par build() et le comportement des handlers de navigation.
"""

from unittest.mock import MagicMock

import pytest

from daynimal.schemas import CommonsImage, License, ImageSource


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def sample_images():
    """Crée une liste de CommonsImage pour les tests."""
    # todo: retourner 3 CommonsImage avec des URLs et thumbnails variées
    pass


@pytest.fixture
def mock_image_cache():
    """Crée un mock d'ImageCacheService."""
    # todo: MagicMock avec get_local_path retournant None par défaut
    pass


# =============================================================================
# SECTION 1 : Build avec images
# =============================================================================


class TestImageCarouselBuild:
    """Tests pour ImageCarousel.build()."""

    def test_no_images_shows_empty_state(self, mock_image_cache):
        """Vérifie que build() avec images=[] retourne un container
        d'état vide contenant l'icône HIDE_IMAGE et le texte
        'Aucune image disponible'."""
        # todo
        pass

    def test_single_image_disables_navigation(self, mock_image_cache):
        """Vérifie que build() avec une seule image désactive les boutons
        précédent/suivant (disabled=True) puisqu'il n'y a qu'une image."""
        # todo
        pass

    def test_multiple_images_shows_counter(self, mock_image_cache, sample_images):
        """Vérifie que build() avec 3 images affiche un compteur '1 / 3'
        (format: index+1 / total)."""
        # todo
        pass

    def test_multiple_images_enables_navigation(self, mock_image_cache, sample_images):
        """Vérifie que les boutons précédent/suivant sont activés
        (disabled=False) quand il y a plusieurs images."""
        # todo
        pass

    def test_uses_cached_local_path(self, mock_image_cache, sample_images):
        """Vérifie que build() appelle image_cache.get_local_path()
        pour l'image courante et utilise le chemin local retourné
        comme source de ft.Image au lieu de l'URL distante."""
        # todo
        pass

    def test_fallback_to_url_when_not_cached(self, mock_image_cache, sample_images):
        """Vérifie que quand get_local_path retourne None,
        l'URL de l'image (thumbnail_url ou url) est utilisée directement."""
        # todo
        pass


# =============================================================================
# SECTION 2 : PhyloPic badge et crédits
# =============================================================================


class TestImageCarouselBadgeAndCredits:
    """Tests pour l'affichage du badge PhyloPic et des crédits."""

    def test_phylopic_badge_shown(self, mock_image_cache):
        """Vérifie que quand image.image_source == ImageSource.PHYLOPIC,
        un badge 'Silhouette PhyloPic' est affiché sous l'image."""
        # todo
        pass

    def test_phylopic_badge_hidden_for_commons(self, mock_image_cache):
        """Vérifie que le badge PhyloPic n'est PAS affiché pour les images
        de source COMMONS."""
        # todo
        pass

    def test_credit_text_shown_with_author(self, mock_image_cache):
        """Vérifie que le texte de crédit (auteur + licence) est affiché
        quand l'image a un author non-vide."""
        # todo
        pass

    def test_credit_text_hidden_without_author(self, mock_image_cache):
        """Vérifie que le texte de crédit n'est pas affiché quand
        l'image n'a pas d'auteur (author=None ou '')."""
        # todo
        pass


# =============================================================================
# SECTION 3 : Navigation
# =============================================================================


class TestImageCarouselNavigation:
    """Tests pour _on_prev et _on_next."""

    def test_on_prev_decrements_index(self, mock_image_cache, sample_images):
        """Vérifie que _on_prev avec index=1 appelle on_index_change(0)."""
        # todo
        pass

    def test_on_prev_wraps_to_last(self, mock_image_cache, sample_images):
        """Vérifie que _on_prev avec index=0 et 3 images appelle
        on_index_change(2) (modulo wrap)."""
        # todo
        pass

    def test_on_next_increments_index(self, mock_image_cache, sample_images):
        """Vérifie que _on_next avec index=0 appelle on_index_change(1)."""
        # todo
        pass

    def test_on_next_wraps_to_first(self, mock_image_cache, sample_images):
        """Vérifie que _on_next avec index=2 et 3 images appelle
        on_index_change(0) (modulo wrap)."""
        # todo
        pass


# =============================================================================
# SECTION 4 : Error content
# =============================================================================


class TestImageCarouselErrorContent:
    """Tests pour _build_error_content."""

    def test_error_content_shows_broken_image_icon(self, mock_image_cache):
        """Vérifie que _build_error_content retourne un container avec
        une icône BROKEN_IMAGE."""
        # todo
        pass

    def test_error_content_truncates_long_url(self, mock_image_cache):
        """Vérifie que _build_error_content tronque les URLs très longues
        dans le texte d'erreur."""
        # todo
        pass
