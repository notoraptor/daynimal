"""Tests pour daynimal/ui/views/history_view.py — Vue Historique.

Couvre: HistoryView (build, load_history, _on_page_change, _on_item_click).

Stratégie: on mock AppState.repository.get_history et ft.Page.
On vérifie que load_history crée les bons AnimalCards avec les timestamps
formatés, que la pagination fonctionne, et que les clics délèguent au callback.
"""

import asyncio
from unittest.mock import MagicMock, patch, AsyncMock

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
    """Mock d'AppState avec repository.get_history."""
    # todo
    pass


@pytest.fixture
def mock_debugger():
    """Mock de FletDebugger."""
    # todo
    pass


# =============================================================================
# SECTION 1 : HistoryView.build
# =============================================================================


class TestHistoryViewBuild:
    """Tests pour HistoryView.build()."""

    def test_returns_column_with_header(self, mock_page, mock_app_state, mock_debugger):
        """Vérifie que build() retourne un ft.Column contenant un header
        'Historique' (via view_header) suivi du container de liste et
        du container de pagination."""
        # todo
        pass

    def test_triggers_load_history(self, mock_page, mock_app_state, mock_debugger):
        """Vérifie que build() lance un asyncio.create_task pour
        load_history() afin de charger les données de manière asynchrone."""
        # todo
        pass


# =============================================================================
# SECTION 2 : load_history
# =============================================================================


class TestHistoryViewLoadHistory:
    """Tests pour HistoryView.load_history()."""

    @pytest.mark.asyncio
    async def test_empty_history_shows_empty_state(self, mock_page, mock_app_state, mock_debugger):
        """Vérifie que quand repository.get_history retourne ([], 0),
        l'UI affiche un état vide avec l'icône HISTORY et le message
        'Aucun historique' et 'Consultez un animal pour le voir ici'."""
        # todo
        pass

    @pytest.mark.asyncio
    async def test_with_items_creates_cards(self, mock_page, mock_app_state, mock_debugger):
        """Vérifie que quand get_history retourne des animaux, un
        create_history_card est créé pour chacun. On vérifie que
        history_list.controls contient le bon nombre de cards."""
        # todo
        pass

    @pytest.mark.asyncio
    async def test_formats_timestamp(self, mock_page, mock_app_state, mock_debugger):
        """Vérifie que le timestamp viewed_at est formaté en 'DD/MM/YYYY à HH:MM'
        pour chaque carte d'historique."""
        # todo
        pass

    @pytest.mark.asyncio
    async def test_shows_count_text(self, mock_page, mock_app_state, mock_debugger):
        """Vérifie qu'un texte '{total} animal(aux) consulté(s)' est affiché
        au-dessus de la liste."""
        # todo
        pass

    @pytest.mark.asyncio
    async def test_error_shows_error_ui(self, mock_page, mock_app_state, mock_debugger):
        """Vérifie que si get_history lève une exception, un container d'erreur
        est affiché avec l'icône ERROR et le message d'erreur."""
        # todo
        pass

    @pytest.mark.asyncio
    async def test_creates_pagination_bar(self, mock_page, mock_app_state, mock_debugger):
        """Vérifie que quand le total dépasse per_page (20), un PaginationBar
        est créé dans pagination_container avec les bons paramètres
        (page, total, per_page, on_page_change)."""
        # todo
        pass


# =============================================================================
# SECTION 3 : Pagination et interaction
# =============================================================================


class TestHistoryViewInteraction:
    """Tests pour _on_page_change et _on_item_click."""

    def test_on_page_change_updates_and_reloads(self, mock_page, mock_app_state, mock_debugger):
        """Vérifie que _on_page_change(2) met à jour self.current_page=2
        et relance load_history() via asyncio.create_task."""
        # todo
        pass

    def test_on_item_click_calls_callback(self, mock_page, mock_app_state, mock_debugger):
        """Vérifie que _on_item_click(42) appelle on_animal_click(42)
        (le callback fourni par AppController)."""
        # todo
        pass

    def test_on_item_click_logs_info(self, mock_page, mock_app_state, mock_debugger):
        """Vérifie que _on_item_click log un message d'info via
        debugger.logger.info contenant le taxon_id."""
        # todo
        pass

    def test_on_item_click_error_handled(self, mock_page, mock_app_state, mock_debugger):
        """Vérifie que si on_animal_click lève une exception,
        _on_item_click l'attrape et la log via debugger.log_error
        sans la propager."""
        # todo
        pass
