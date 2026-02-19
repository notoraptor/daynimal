"""Tests pour daynimal/ui/views/today_view.py — Vue Aujourd'hui.

Couvre: TodayView (build, _load_today_animal, _load_random_animal,
_load_animal_for_today_view, _display_animal, _on_favorite_toggle,
_open_gallery, _on_copy_text, _on_open_wikipedia).

Note: test_sharing.py teste déjà _build_share_text (5 tests). Ce fichier
couvre le reste de TodayView (103 lignes manquantes).

Stratégie: on mock AppState.repository et ft.Page. Pour les méthodes
async, on utilise pytest-asyncio. On vérifie que les handlers appellent
les bonnes méthodes du repository et mettent à jour l'UI.
"""

import asyncio
from unittest.mock import MagicMock, patch, AsyncMock, PropertyMock

import flet as ft
import pytest

from daynimal.schemas import AnimalInfo, Taxon, TaxonomicRank


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def mock_page():
    """Mock de ft.Page."""
    # todo
    pass


@pytest.fixture
def mock_app_state():
    """Mock d'AppState avec repository, image_cache, is_online."""
    # todo
    pass


@pytest.fixture
def mock_debugger():
    """Mock de FletDebugger."""
    # todo
    pass


@pytest.fixture
def sample_animal():
    """Crée un AnimalInfo pour les tests d'affichage."""
    # todo
    pass


# =============================================================================
# SECTION 1 : TodayView.build
# =============================================================================


class TestTodayViewBuild:
    """Tests pour TodayView.build()."""

    def test_shows_welcome_when_no_animal(self, mock_page, mock_app_state, mock_debugger):
        """Vérifie que build() sans current_animal dans app_state affiche
        un message de bienvenue (texte contenant 'Bienvenue' ou 'Découvrez')
        dans today_animal_container."""
        # todo
        pass

    def test_restores_animal_if_cached(self, mock_page, mock_app_state, mock_debugger, sample_animal):
        """Vérifie que build() avec app_state.current_animal défini appelle
        _display_animal pour restaurer l'affichage de l'animal en cours."""
        # todo
        pass

    def test_has_today_button(self, mock_page, mock_app_state, mock_debugger):
        """Vérifie que build() crée un bouton 'Animal du jour' avec l'icône
        TODAY et le handler _load_today_animal."""
        # todo
        pass

    def test_has_random_button(self, mock_page, mock_app_state, mock_debugger):
        """Vérifie que build() crée un bouton 'Animal aléatoire' avec l'icône
        SHUFFLE et le handler _load_random_animal."""
        # todo
        pass


# =============================================================================
# SECTION 2 : Loading animals
# =============================================================================


class TestTodayViewLoadAnimal:
    """Tests pour _load_today_animal et _load_random_animal."""

    @pytest.mark.asyncio
    async def test_load_today_animal_calls_get_animal_of_the_day(
        self, mock_page, mock_app_state, mock_debugger, sample_animal
    ):
        """Vérifie que _load_today_animal appelle
        repo.get_animal_of_the_day() via asyncio.to_thread.
        Mock: repo.get_animal_of_the_day retourne sample_animal."""
        # todo
        pass

    @pytest.mark.asyncio
    async def test_load_today_animal_adds_to_history(
        self, mock_page, mock_app_state, mock_debugger, sample_animal
    ):
        """Vérifie que après le chargement, repo.add_to_history est
        appelé avec (taxon_id, command='today')."""
        # todo
        pass

    @pytest.mark.asyncio
    async def test_load_random_animal_calls_get_random(
        self, mock_page, mock_app_state, mock_debugger, sample_animal
    ):
        """Vérifie que _load_random_animal appelle repo.get_random()
        via asyncio.to_thread."""
        # todo
        pass

    @pytest.mark.asyncio
    async def test_load_random_animal_adds_to_history(
        self, mock_page, mock_app_state, mock_debugger, sample_animal
    ):
        """Vérifie que repo.add_to_history est appelé avec command='random'."""
        # todo
        pass

    @pytest.mark.asyncio
    async def test_shows_loading_during_fetch(
        self, mock_page, mock_app_state, mock_debugger, sample_animal
    ):
        """Vérifie que pendant le chargement, today_animal_container.controls
        contient un LoadingWidget."""
        # todo
        pass

    @pytest.mark.asyncio
    async def test_error_shows_error_widget(
        self, mock_page, mock_app_state, mock_debugger
    ):
        """Vérifie que si repo.get_animal_of_the_day lève une exception,
        un ErrorWidget est affiché dans today_animal_container."""
        # todo
        pass

    @pytest.mark.asyncio
    async def test_none_result_shows_error(
        self, mock_page, mock_app_state, mock_debugger
    ):
        """Vérifie que si le repository retourne None,
        un message d'erreur est affiché."""
        # todo
        pass

    @pytest.mark.asyncio
    async def test_calls_on_load_complete(
        self, mock_page, mock_app_state, mock_debugger, sample_animal
    ):
        """Vérifie que on_load_complete() est appelé après le chargement
        réussi (callback optionnel défini par AppController)."""
        # todo
        pass


# =============================================================================
# SECTION 3 : Display animal
# =============================================================================


class TestTodayViewDisplayAnimal:
    """Tests pour _display_animal."""

    def test_shows_animal_display_controls(
        self, mock_page, mock_app_state, mock_debugger, sample_animal
    ):
        """Vérifie que _display_animal ajoute les contrôles de AnimalDisplay
        dans today_animal_container (titre, classification, etc.)."""
        # todo
        pass

    def test_shows_favorite_button(
        self, mock_page, mock_app_state, mock_debugger, sample_animal
    ):
        """Vérifie qu'un bouton favori (IconButton avec FAVORITE/FAVORITE_BORDER)
        est créé. Si l'animal est favori, l'icône est FAVORITE (plein),
        sinon FAVORITE_BORDER (contour)."""
        # todo
        pass

    def test_shows_share_buttons(
        self, mock_page, mock_app_state, mock_debugger, sample_animal
    ):
        """Vérifie que les boutons de partage (copier texte, ouvrir Wikipedia)
        sont présents dans les contrôles."""
        # todo
        pass

    def test_shows_image_when_available(
        self, mock_page, mock_app_state, mock_debugger
    ):
        """Vérifie que quand l'animal a des images, un ft.Image est affiché
        avec l'URL/chemin local de la première image."""
        # todo
        pass

    def test_no_images_no_gallery_button(
        self, mock_page, mock_app_state, mock_debugger
    ):
        """Vérifie que quand images est vide, le bouton 'Plus d'images'
        n'est PAS affiché."""
        # todo
        pass

    def test_multiple_images_shows_gallery_button(
        self, mock_page, mock_app_state, mock_debugger
    ):
        """Vérifie que quand l'animal a plus d'une image, un bouton
        'Plus d'images' est affiché pour ouvrir la galerie."""
        # todo
        pass

    def test_updates_app_state_current_animal(
        self, mock_page, mock_app_state, mock_debugger, sample_animal
    ):
        """Vérifie que _display_animal met à jour app_state.current_animal
        avec l'animal affiché."""
        # todo
        pass


# =============================================================================
# SECTION 4 : Favorite toggle
# =============================================================================


class TestTodayViewFavoriteToggle:
    """Tests pour _on_favorite_toggle."""

    def test_calls_callback_with_correct_args(
        self, mock_page, mock_app_state, mock_debugger, sample_animal
    ):
        """Vérifie que _on_favorite_toggle appelle on_favorite_toggle_callback
        avec (taxon_id, is_favorite). Le callback est fourni par AppController."""
        # todo
        pass

    def test_refreshes_display_after_toggle(
        self, mock_page, mock_app_state, mock_debugger, sample_animal
    ):
        """Vérifie que après le toggle, _display_animal est rappelé pour
        mettre à jour l'icône favori (plein ↔ contour)."""
        # todo
        pass


# =============================================================================
# SECTION 5 : Gallery and sharing
# =============================================================================


class TestTodayViewGalleryAndSharing:
    """Tests pour _open_gallery, _on_copy_text, _on_open_wikipedia."""

    def test_open_gallery_creates_dialog(
        self, mock_page, mock_app_state, mock_debugger, sample_animal
    ):
        """Vérifie que _open_gallery instancie ImageGalleryDialog avec
        les images de l'animal et appelle dialog.open()."""
        # todo
        pass

    @pytest.mark.asyncio
    async def test_on_copy_text_copies_to_clipboard(
        self, mock_page, mock_app_state, mock_debugger, sample_animal
    ):
        """Vérifie que _on_copy_text crée un ft.Clipboard et appelle
        clipboard.set(text) avec le texte de partage formaté.
        Puis un SnackBar 'Copié' est affiché."""
        # todo
        pass

    def test_on_open_wikipedia_launches_url(
        self, mock_page, mock_app_state, mock_debugger, sample_animal
    ):
        """Vérifie que _on_open_wikipedia appelle page.run_task avec
        ft.UrlLauncher().launch_url et l'URL Wikipedia de l'animal."""
        # todo
        pass

    def test_on_open_wikipedia_no_article(
        self, mock_page, mock_app_state, mock_debugger
    ):
        """Vérifie que _on_open_wikipedia ne fait rien si l'animal
        n'a pas d'article Wikipedia."""
        # todo
        pass
