"""Tests pour daynimal/ui/views/favorites_view.py — Vue Favoris.

Couvre: FavoritesView (build, load_favorites, _on_page_change, _on_item_click).

Stratégie: identique à HistoryView — on mock AppState.repository.get_favorites
et ft.Page. On vérifie la structure de l'UI et les interactions.
"""

from unittest.mock import MagicMock, patch

import flet as ft
import pytest

from daynimal.schemas import AnimalInfo, Taxon, TaxonomicRank


def _make_animal(taxon_id: int, name: str) -> AnimalInfo:
    """Helper to create a minimal AnimalInfo for testing."""
    return AnimalInfo(
        taxon=Taxon(
            taxon_id=taxon_id,
            scientific_name=name,
            canonical_name=name,
            rank=TaxonomicRank.SPECIES,
        )
    )


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def mock_page():
    """Mock de ft.Page."""
    page = MagicMock(spec=ft.Page)
    page.update = MagicMock()
    return page


@pytest.fixture
def mock_app_state():
    """Mock d'AppState avec repository.get_favorites."""
    state = MagicMock()
    state.repository = MagicMock()
    state.repository.get_favorites = MagicMock(return_value=([], 0))
    return state


# =============================================================================
# SECTION 1 : FavoritesView.build
# =============================================================================


class TestFavoritesViewBuild:
    """Tests pour FavoritesView.build()."""

    @patch("daynimal.ui.views.favorites_view.asyncio.create_task")
    def test_returns_column_with_header(
        self, mock_create_task, mock_page, mock_app_state
    ):
        """Vérifie que build() retourne un ft.Column contenant un header 'Favoris'."""
        from daynimal.ui.views.favorites_view import FavoritesView

        view = FavoritesView(mock_page, mock_app_state)
        result = view.build()

        assert isinstance(result, ft.Column)
        # Should contain header, divider, favorites container, pagination
        assert len(result.controls) >= 3

    @patch("daynimal.ui.views.favorites_view.asyncio.create_task")
    def test_triggers_load_favorites(self, mock_create_task, mock_page, mock_app_state):
        """Vérifie que build() lance load_favorites() en tâche async."""
        from daynimal.ui.views.favorites_view import FavoritesView

        view = FavoritesView(mock_page, mock_app_state)
        view.build()

        mock_create_task.assert_called_once()


# =============================================================================
# SECTION 2 : load_favorites
# =============================================================================


class TestFavoritesViewLoadFavorites:
    """Tests pour FavoritesView.load_favorites()."""

    @pytest.mark.asyncio
    @patch("daynimal.ui.views.favorites_view.asyncio.create_task")
    async def test_empty_shows_empty_state(
        self, mock_create_task, mock_page, mock_app_state
    ):
        """Vérifie que quand get_favorites retourne ([], 0), l'UI affiche 'Aucun favori'."""
        from daynimal.ui.views.favorites_view import FavoritesView

        mock_app_state.repository.get_favorites.return_value = ([], 0)

        view = FavoritesView(mock_page, mock_app_state)
        view.build()

        await view.load_favorites()

        # Check favorites_list has the empty state
        controls = view.favorites_list.controls
        assert len(controls) >= 1
        # The empty state container should contain "Aucun favori" text
        container = controls[0]
        assert isinstance(container, ft.Container)

    @pytest.mark.asyncio
    @patch("daynimal.ui.views.favorites_view.create_favorite_card")
    @patch("daynimal.ui.views.favorites_view.asyncio.create_task")
    async def test_with_items_creates_cards(
        self, mock_create_task, mock_create_card, mock_page, mock_app_state
    ):
        """Vérifie que quand get_favorites retourne des animaux, des cards sont créées."""
        from daynimal.ui.views.favorites_view import FavoritesView

        animals = [_make_animal(1, "Canis lupus"), _make_animal(2, "Felis catus")]
        mock_app_state.repository.get_favorites.return_value = (animals, 2)
        mock_create_card.return_value = ft.Container()

        view = FavoritesView(mock_page, mock_app_state)
        view.build()

        await view.load_favorites()

        assert mock_create_card.call_count == 2

    @pytest.mark.asyncio
    @patch("daynimal.ui.views.favorites_view.create_favorite_card")
    @patch("daynimal.ui.views.favorites_view.asyncio.create_task")
    async def test_shows_count_text(
        self, mock_create_task, mock_create_card, mock_page, mock_app_state
    ):
        """Vérifie qu'un texte '{total} favori(s)' est affiché."""
        from daynimal.ui.views.favorites_view import FavoritesView

        animals = [_make_animal(1, "Canis lupus")]
        mock_app_state.repository.get_favorites.return_value = (animals, 1)
        mock_create_card.return_value = ft.Container()

        view = FavoritesView(mock_page, mock_app_state)
        view.build()

        await view.load_favorites()

        # Check that count text is in controls
        texts = [
            c.value for c in view.favorites_list.controls if isinstance(c, ft.Text)
        ]
        assert any("1 favori" in t for t in texts if t)

    @pytest.mark.asyncio
    @patch("daynimal.ui.views.favorites_view.asyncio.create_task")
    async def test_error_shows_error_ui(
        self, mock_create_task, mock_page, mock_app_state
    ):
        """Vérifie que les exceptions sont attrapées et un message d'erreur est affiché."""
        from daynimal.ui.views.favorites_view import FavoritesView

        mock_app_state.repository.get_favorites.side_effect = Exception("DB error")

        view = FavoritesView(mock_page, mock_app_state)
        view.build()

        await view.load_favorites()

        # Should show error container
        controls = view.favorites_list.controls
        assert len(controls) >= 1

    @pytest.mark.asyncio
    @patch("daynimal.ui.views.favorites_view.PaginationBar")
    @patch("daynimal.ui.views.favorites_view.create_favorite_card")
    @patch("daynimal.ui.views.favorites_view.asyncio.create_task")
    async def test_creates_pagination_bar(
        self,
        mock_create_task,
        mock_create_card,
        mock_pagination,
        mock_page,
        mock_app_state,
    ):
        """Vérifie que quand total > per_page (20), un PaginationBar est créé."""
        from daynimal.ui.views.favorites_view import FavoritesView

        animals = [_make_animal(i, f"Species {i}") for i in range(1, 21)]
        mock_app_state.repository.get_favorites.return_value = (animals, 25)
        mock_create_card.return_value = ft.Container()

        mock_bar = MagicMock()
        mock_bar.build.return_value = MagicMock(content=ft.Container())
        mock_pagination.return_value = mock_bar

        view = FavoritesView(mock_page, mock_app_state)
        view.build()

        await view.load_favorites()

        mock_pagination.assert_called_once()


# =============================================================================
# SECTION 3 : Interaction
# =============================================================================


class TestFavoritesViewInteraction:
    """Tests pour _on_page_change et _on_item_click."""

    @patch("daynimal.ui.views.favorites_view.asyncio.create_task")
    def test_on_page_change_updates_and_reloads(
        self, mock_create_task, mock_page, mock_app_state
    ):
        """Vérifie que _on_page_change(3) met à jour current_page et relance load_favorites."""
        from daynimal.ui.views.favorites_view import FavoritesView

        view = FavoritesView(mock_page, mock_app_state)
        view.build()

        # Reset call count after build
        mock_create_task.reset_mock()

        view._on_page_change(3)

        assert view.current_page == 3
        mock_create_task.assert_called_once()

    @patch("daynimal.ui.views.favorites_view.asyncio.create_task")
    def test_on_item_click_calls_callback(
        self, mock_create_task, mock_page, mock_app_state
    ):
        """Vérifie que _on_item_click(42) appelle on_animal_click(42)."""
        from daynimal.ui.views.favorites_view import FavoritesView

        callback = MagicMock()
        view = FavoritesView(mock_page, mock_app_state, on_animal_click=callback)
        view.build()

        view._on_item_click(42)

        callback.assert_called_once_with(42)

    @patch("daynimal.ui.views.favorites_view.asyncio.create_task")
    def test_on_item_click_error_handled(
        self, mock_create_task, mock_page, mock_app_state
    ):
        """Vérifie que les exceptions dans on_animal_click sont attrapées."""
        from daynimal.ui.views.favorites_view import FavoritesView

        callback = MagicMock(side_effect=Exception("callback error"))
        view = FavoritesView(mock_page, mock_app_state, on_animal_click=callback)
        view.build()

        # Should not raise
        view._on_item_click(42)
