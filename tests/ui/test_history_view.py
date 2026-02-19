"""Tests pour daynimal/ui/views/history_view.py --- Vue Historique.

Couvre: HistoryView (build, load_history, _on_page_change, _on_item_click).

Strategie: on mock AppState.repository.get_history et ft.Page.
On verifie que load_history cree les bons AnimalCards avec les timestamps
formates, que la pagination fonctionne, et que les clics deleguent au callback.
"""

from datetime import datetime
from unittest.mock import MagicMock, patch, AsyncMock

import flet as ft
import pytest

from daynimal.schemas import AnimalInfo, Taxon, TaxonomicRank


def _make_animal(
    taxon_id: int, name: str, viewed_at: datetime | None = None
) -> AnimalInfo:
    """Helper to create a minimal AnimalInfo for testing."""
    return AnimalInfo(
        taxon=Taxon(
            taxon_id=taxon_id,
            scientific_name=name,
            canonical_name=name,
            rank=TaxonomicRank.SPECIES,
        ),
        viewed_at=viewed_at,
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
    """Mock d'AppState avec repository.get_history."""
    state = MagicMock()
    state.repository = MagicMock()
    state.repository.get_history = MagicMock(return_value=([], 0))
    return state


# =============================================================================
# SECTION 1 : HistoryView.build
# =============================================================================


class TestHistoryViewBuild:
    """Tests pour HistoryView.build()."""

    @patch("daynimal.ui.views.history_view.asyncio.create_task")
    def test_returns_column_with_header(
        self, _mock_create_task, mock_page, mock_app_state
    ):
        """Verifie que build() retourne un ft.Column contenant un header
        'Historique' (via view_header) suivi du container de liste et
        du container de pagination."""
        from daynimal.ui.views.history_view import HistoryView

        view = HistoryView(page=mock_page, app_state=mock_app_state)
        result = view.build()

        # build() returns a ft.Column
        assert isinstance(result, ft.Column)

        # The column has controls: header, divider, content container, pagination container
        assert len(result.controls) == 4

        # First control is the header (a Container from view_header)
        header = result.controls[0]
        assert isinstance(header, ft.Container)
        # The header contains a Row with a Text saying "Historique"
        header_row = header.content
        assert isinstance(header_row, ft.Row)
        header_text = header_row.controls[0]
        assert isinstance(header_text, ft.Text)
        assert "Historique" in header_text.value

        # Second control is a Divider
        assert isinstance(result.controls[1], ft.Divider)

        # Third control is a Container wrapping the history_list Column
        assert isinstance(result.controls[2], ft.Container)

        # Fourth control is the pagination container
        assert result.controls[3] is view.pagination_container

    @patch("daynimal.ui.views.history_view.asyncio.create_task")
    def test_triggers_load_history(self, mock_create_task, mock_page, mock_app_state):
        """Verifie que build() lance un asyncio.create_task pour
        load_history() afin de charger les donnees de maniere asynchrone."""
        from daynimal.ui.views.history_view import HistoryView

        view = HistoryView(page=mock_page, app_state=mock_app_state)
        view.build()

        # asyncio.create_task was called once with the coroutine from load_history()
        mock_create_task.assert_called_once()


# =============================================================================
# SECTION 2 : load_history
# =============================================================================


class TestHistoryViewLoadHistory:
    """Tests pour HistoryView.load_history()."""

    @pytest.mark.asyncio
    @patch("daynimal.ui.views.history_view.asyncio.to_thread", new_callable=AsyncMock)
    async def test_empty_history_shows_empty_state(
        self, mock_to_thread, mock_page, mock_app_state
    ):
        """Verifie que quand repository.get_history retourne ([], 0),
        l'UI affiche un etat vide avec l'icone HISTORY et le message
        'Aucun historique' et 'Consultez un animal pour le voir ici'."""
        from daynimal.ui.views.history_view import HistoryView

        mock_app_state.repository.get_history.return_value = ([], 0)
        mock_to_thread.return_value = ([], 0)

        view = HistoryView(page=mock_page, app_state=mock_app_state)

        await view.load_history()

        # The history_list should contain one container with the empty state
        assert len(view.history_list.controls) == 1
        container = view.history_list.controls[0]
        assert isinstance(container, ft.Container)

        # Inside the container, there's a Column with icon, title text, and description text
        column = container.content
        assert isinstance(column, ft.Column)

        # Find the icon
        icon_ctrl = column.controls[0]
        assert isinstance(icon_ctrl, ft.Icon)
        assert icon_ctrl.icon == ft.Icons.HISTORY

        # Find the title text "Aucun historique"
        title_text = column.controls[1]
        assert isinstance(title_text, ft.Text)
        assert "Aucun historique" in title_text.value

        # Find the description text
        desc_text = column.controls[2]
        assert isinstance(desc_text, ft.Text)
        assert "Consultez" in desc_text.value

    @pytest.mark.asyncio
    @patch("daynimal.ui.views.history_view.create_history_card")
    @patch("daynimal.ui.views.history_view.asyncio.to_thread", new_callable=AsyncMock)
    async def test_with_items_creates_cards(
        self, mock_to_thread, mock_create_card, mock_page, mock_app_state
    ):
        """Verifie que quand get_history retourne des animaux, un
        create_history_card est cree pour chacun. On verifie que
        history_list.controls contient le bon nombre de cards."""
        from daynimal.ui.views.history_view import HistoryView

        animals = [
            _make_animal(1, "Canis lupus", datetime(2026, 2, 10, 14, 30)),
            _make_animal(2, "Felis catus", datetime(2026, 2, 11, 9, 15)),
            _make_animal(3, "Panthera leo", datetime(2026, 2, 12, 18, 0)),
        ]

        mock_to_thread.return_value = (animals, 3)
        mock_create_card.side_effect = lambda animal, on_click, viewed_at: MagicMock(
            spec=ft.Card
        )

        view = HistoryView(page=mock_page, app_state=mock_app_state)

        await view.load_history()

        # The first control is the count text, then one card per animal
        # controls = [count_text, card1, card2, card3]
        assert len(view.history_list.controls) == 4  # 1 count text + 3 cards
        mock_create_card.assert_called()
        assert mock_create_card.call_count == 3

    @pytest.mark.asyncio
    @patch("daynimal.ui.views.history_view.create_history_card")
    @patch("daynimal.ui.views.history_view.asyncio.to_thread", new_callable=AsyncMock)
    async def test_formats_timestamp(
        self, mock_to_thread, mock_create_card, mock_page, mock_app_state
    ):
        """Verifie que le timestamp viewed_at est formate en 'DD/MM/YYYY HH:MM'
        pour chaque carte d'historique."""
        from daynimal.ui.views.history_view import HistoryView

        dt = datetime(2026, 2, 10, 14, 30)
        animals = [_make_animal(1, "Canis lupus", dt)]

        mock_to_thread.return_value = (animals, 1)
        mock_create_card.return_value = MagicMock(spec=ft.Card)

        view = HistoryView(page=mock_page, app_state=mock_app_state)

        await view.load_history()

        # Verify that create_history_card was called with the formatted timestamp
        mock_create_card.assert_called_once()
        call_args = mock_create_card.call_args
        viewed_at_str = call_args[0][2]  # Third positional arg is viewed_at_str
        assert viewed_at_str == "10/02/2026 14:30"

    @pytest.mark.asyncio
    @patch("daynimal.ui.views.history_view.create_history_card")
    @patch("daynimal.ui.views.history_view.asyncio.to_thread", new_callable=AsyncMock)
    async def test_shows_count_text(
        self, mock_to_thread, mock_create_card, mock_page, mock_app_state
    ):
        """Verifie qu'un texte '{total} animal(aux) consulte(s)' est affiche
        au-dessus de la liste."""
        from daynimal.ui.views.history_view import HistoryView

        animals = [
            _make_animal(1, "Canis lupus", datetime(2026, 2, 10, 14, 30)),
            _make_animal(2, "Felis catus", datetime(2026, 2, 11, 9, 15)),
        ]

        mock_to_thread.return_value = (animals, 2)
        mock_create_card.return_value = MagicMock(spec=ft.Card)

        view = HistoryView(page=mock_page, app_state=mock_app_state)

        await view.load_history()

        # First control should be the count text
        count_text = view.history_list.controls[0]
        assert isinstance(count_text, ft.Text)
        assert "2" in count_text.value
        assert "animal(aux)" in count_text.value

    @pytest.mark.asyncio
    @patch("daynimal.ui.views.history_view.asyncio.to_thread", new_callable=AsyncMock)
    async def test_error_shows_error_ui(
        self, mock_to_thread, mock_page, mock_app_state
    ):
        """Verifie que si get_history leve une exception, un container d'erreur
        est affiche avec l'icone ERROR et le message d'erreur."""
        from daynimal.ui.views.history_view import HistoryView

        view = HistoryView(page=mock_page, app_state=mock_app_state)

        error_msg = "Database connection failed"
        mock_to_thread.side_effect = Exception(error_msg)

        await view.load_history()

        # The history_list should contain one container with the error
        assert len(view.history_list.controls) == 1
        container = view.history_list.controls[0]
        assert isinstance(container, ft.Container)

        column = container.content
        assert isinstance(column, ft.Column)

        # Error icon
        icon_ctrl = column.controls[0]
        assert isinstance(icon_ctrl, ft.Icon)
        assert icon_ctrl.icon == ft.Icons.ERROR

        # Error title
        title_text = column.controls[1]
        assert isinstance(title_text, ft.Text)
        assert "Erreur" in title_text.value

        # Error details
        detail_text = column.controls[2]
        assert isinstance(detail_text, ft.Text)
        assert error_msg in detail_text.value

    @pytest.mark.asyncio
    @patch("daynimal.ui.views.history_view.PaginationBar")
    @patch("daynimal.ui.views.history_view.create_history_card")
    @patch("daynimal.ui.views.history_view.asyncio.to_thread", new_callable=AsyncMock)
    async def test_creates_pagination_bar(
        self,
        mock_to_thread,
        mock_create_card,
        mock_pagination,
        mock_page,
        mock_app_state,
    ):
        """Verifie que quand le total depasse per_page (20), un PaginationBar
        est cree dans pagination_container avec les bons parametres
        (page, total, per_page, on_page_change)."""
        from daynimal.ui.views.history_view import HistoryView, PER_PAGE

        # Create 5 items but report total of 25 (more than PER_PAGE=20)
        animals = [
            _make_animal(i, f"Animal {i}", datetime(2026, 2, i + 1, 10, 0))
            for i in range(1, 6)
        ]

        mock_to_thread.return_value = (animals, 25)
        mock_create_card.return_value = MagicMock(spec=ft.Card)

        mock_bar_instance = MagicMock()
        mock_bar_build = MagicMock()
        mock_bar_build.content = MagicMock()
        mock_bar_instance.build.return_value = mock_bar_build
        mock_pagination.return_value = mock_bar_instance

        view = HistoryView(page=mock_page, app_state=mock_app_state)

        await view.load_history()

        # PaginationBar was created with the correct arguments
        mock_pagination.assert_called_once_with(
            page=1, total=25, per_page=PER_PAGE, on_page_change=view._on_page_change
        )
        # Its build() was called and its content was assigned
        mock_bar_instance.build.assert_called_once()
        assert view.pagination_container.content is mock_bar_build.content


# =============================================================================
# SECTION 3 : Pagination et interaction
# =============================================================================


class TestHistoryViewInteraction:
    """Tests pour _on_page_change et _on_item_click."""

    @patch("daynimal.ui.views.history_view.asyncio.create_task")
    def test_on_page_change_updates_and_reloads(
        self, mock_create_task, mock_page, mock_app_state
    ):
        """Verifie que _on_page_change(2) met a jour self.current_page=2
        et relance load_history() via asyncio.create_task."""
        from daynimal.ui.views.history_view import HistoryView

        view = HistoryView(page=mock_page, app_state=mock_app_state)

        view._on_page_change(2)

        assert view.current_page == 2
        mock_create_task.assert_called_once()

    def test_on_item_click_calls_callback(self, mock_page, mock_app_state):
        """Verifie que _on_item_click(42) appelle on_animal_click(42)
        (le callback fourni par AppController)."""
        from daynimal.ui.views.history_view import HistoryView

        on_click = MagicMock()
        view = HistoryView(
            page=mock_page, app_state=mock_app_state, on_animal_click=on_click
        )

        view._on_item_click(42)

        on_click.assert_called_once_with(42)

    @patch("daynimal.ui.views.history_view.logger")
    def test_on_item_click_logs_info(self, mock_logger, mock_page, mock_app_state):
        """Verifie que _on_item_click log un message d'info via
        logger.info contenant le taxon_id."""
        from daynimal.ui.views.history_view import HistoryView

        on_click = MagicMock()
        view = HistoryView(
            page=mock_page, app_state=mock_app_state, on_animal_click=on_click
        )

        view._on_item_click(99)

        # Check that logger.info was called with a message containing the taxon_id
        mock_logger.info.assert_called_once()
        log_message = mock_logger.info.call_args[0][0]
        assert "99" in log_message

    @patch("daynimal.ui.views.history_view.logger")
    def test_on_item_click_error_handled(self, mock_logger, mock_page, mock_app_state):
        """Verifie que si on_animal_click leve une exception,
        _on_item_click l'attrape et la log via logger.error
        sans la propager."""
        from daynimal.ui.views.history_view import HistoryView

        on_click = MagicMock(side_effect=RuntimeError("Navigation failed"))
        view = HistoryView(
            page=mock_page, app_state=mock_app_state, on_animal_click=on_click
        )

        # Should NOT raise
        view._on_item_click(42)

        # Error was logged
        mock_logger.error.assert_called_once()
