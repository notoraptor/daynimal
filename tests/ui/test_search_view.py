"""Tests for SearchView."""

from unittest.mock import MagicMock, patch

import flet as ft
import pytest

from daynimal.schemas import AnimalInfo, Taxon
from daynimal.ui.state import AppState
from daynimal.ui.views.search_view import SearchView


def _make_animal(
    taxon_id: int, name: str, vernacular: dict | None = None
) -> AnimalInfo:
    """Create a minimal AnimalInfo for testing."""
    return AnimalInfo(
        taxon=Taxon(
            taxon_id=taxon_id,
            scientific_name=name,
            canonical_name=name.split()[0],
            rank="species",
            kingdom="Animalia",
            phylum="Chordata",
            class_="Mammalia",
            order="Carnivora",
            family="Felidae",
            genus=name.split()[0],
            parent_id=None,
            vernacular_names=vernacular or {},
        )
    )


def _make_search_view():
    """Create a SearchView with mocked page and app_state."""
    page = MagicMock(spec=ft.Page)
    page.update = MagicMock()
    app_state = MagicMock(spec=AppState)
    on_click = MagicMock()
    view = SearchView(page=page, app_state=app_state, on_result_click=on_click)
    return view, page, app_state, on_click


def test_search_view_build_returns_control():
    """Test build() returns a ft.Control with search field and button."""
    view, _, _, _ = _make_search_view()
    result = view.build()

    assert isinstance(result, ft.Column)
    # Should have: header, divider, search_bar, results_container
    assert len(result.controls) == 4


def test_search_view_has_search_field_and_button():
    """Test SearchView has a search field and a search button."""
    view, _, _, _ = _make_search_view()
    view.build()

    assert isinstance(view.search_field, ft.TextField)
    assert isinstance(view.search_button, ft.IconButton)
    assert view.search_field.on_submit is not None
    assert view.search_button.on_click is not None


def test_search_view_initial_empty_state():
    """Test SearchView shows empty state initially after build."""
    view, _, _, _ = _make_search_view()
    view.build()

    # results_container should have the empty state
    assert len(view.results_container.controls) == 1
    container = view.results_container.controls[0]
    assert isinstance(container, ft.Container)
    # The inner Column should contain the "Recherchez un animal" text
    inner_col = container.content
    assert isinstance(inner_col, ft.Column)
    texts = [c for c in inner_col.controls if isinstance(c, ft.Text)]
    assert any("Recherchez un animal" in t.value for t in texts)


@pytest.mark.asyncio
async def test_perform_search_with_results():
    """Test perform_search displays result cards when results are found."""
    view, page, app_state, on_click = _make_search_view()
    view.build()

    animals = [_make_animal(1, "Panthera leo"), _make_animal(2, "Panthera tigris")]
    app_state.repository.search.return_value = animals

    await view.perform_search("Panthera")

    # Should show count text + 2 cards
    assert len(view.results_container.controls) == 3
    count_text = view.results_container.controls[0]
    assert isinstance(count_text, ft.Text)
    assert "2" in count_text.value


@pytest.mark.asyncio
async def test_perform_search_no_results():
    """Test perform_search shows 'no results' when search returns empty."""
    view, page, app_state, _ = _make_search_view()
    view.build()

    app_state.repository.search.return_value = []

    await view.perform_search("xxxxxx")

    # Should show no-results state
    assert len(view.results_container.controls) == 1
    container = view.results_container.controls[0]
    inner_col = container.content
    texts = [c for c in inner_col.controls if isinstance(c, ft.Text)]
    assert any("Aucun résultat" in t.value for t in texts)


@pytest.mark.asyncio
async def test_perform_search_with_error():
    """Test perform_search shows error state on exception."""
    view, page, app_state, _ = _make_search_view()
    view.build()

    app_state.repository.search.side_effect = RuntimeError("DB error")

    await view.perform_search("test")

    # Should show error state
    assert len(view.results_container.controls) == 1
    container = view.results_container.controls[0]
    inner_col = container.content
    texts = [c for c in inner_col.controls if isinstance(c, ft.Text)]
    assert any("Erreur" in t.value for t in texts)
    assert any("DB error" in t.value for t in texts)


def test_on_submit_triggers_search():
    """Test _on_submit creates a task for perform_search."""
    view, _, app_state, _ = _make_search_view()
    view.build()
    view.search_field.value = "lion"

    with patch("daynimal.ui.views.search_view.asyncio.create_task") as mock_task:
        view._on_submit(MagicMock())
        mock_task.assert_called_once()


def test_on_submit_ignores_empty_query():
    """Test _on_submit does nothing when query is empty."""
    view, _, _, _ = _make_search_view()
    view.build()
    view.search_field.value = "   "

    with patch("daynimal.ui.views.search_view.asyncio.create_task") as mock_task:
        view._on_submit(MagicMock())
        mock_task.assert_not_called()


def test_on_search_click_triggers_search():
    """Test _on_search_click creates a task for perform_search."""
    view, _, app_state, _ = _make_search_view()
    view.build()
    view.search_field.value = "tiger"

    with patch("daynimal.ui.views.search_view.asyncio.create_task") as mock_task:
        view._on_search_click(MagicMock())
        mock_task.assert_called_once()


def test_on_search_click_ignores_empty_query():
    """Test _on_search_click does nothing when query is empty."""
    view, _, _, _ = _make_search_view()
    view.build()
    view.search_field.value = ""

    with patch("daynimal.ui.views.search_view.asyncio.create_task") as mock_task:
        view._on_search_click(MagicMock())
        mock_task.assert_not_called()
