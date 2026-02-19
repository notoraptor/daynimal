"""Tests pour daynimal/ui/views/stats_view.py --- Vue Statistiques.

Couvre: StatsView (build, _stat_card, _display_stats, load_stats).

Strategie: on mock AppState.repository.get_stats et ft.Page.
On verifie que les stat cards sont creees avec les bonnes valeurs
et que le caching fonctionne (deuxieme build utilise les stats cachees).
"""

import asyncio
from unittest.mock import MagicMock, patch, AsyncMock

import flet as ft
import pytest

from daynimal.ui.views.stats_view import StatsView


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def mock_page():
    """Mock de ft.Page."""
    page = MagicMock(spec=ft.Page)
    page.update = MagicMock()
    page.run_task = MagicMock()
    page.width = 400
    page.height = 800
    return page


@pytest.fixture
def mock_app_state():
    """Mock d'AppState avec repository.get_stats."""
    state = MagicMock()
    state.repository = MagicMock()
    state.repository.get_stats = MagicMock(return_value={
        "total_taxa": 163000,
        "species_count": 160000,
        "enriched_count": 500,
        "vernacular_names": 1100000,
        "enrichment_progress": "500/160000 (0.3%)",
    })
    state.current_animal = None
    state.current_image_index = 0
    state.cached_stats = None
    return state


@pytest.fixture
def sample_stats():
    """Statistiques simulees retournees par get_stats()."""
    return {
        "total_taxa": 163000,
        "species_count": 160000,
        "enriched_count": 500,
        "vernacular_names": 1100000,
        "enrichment_progress": "500/160000 (0.3%)",
    }


def _make_view(mock_page, mock_app_state):
    """Helper to create a StatsView with mocked dependencies."""
    return StatsView(page=mock_page, app_state=mock_app_state)


# =============================================================================
# SECTION 1 : StatsView.build
# =============================================================================


class TestStatsViewBuild:
    """Tests pour StatsView.build()."""

    @patch("daynimal.ui.views.stats_view.asyncio.create_task")
    def test_returns_column_with_header(self, _mock_create_task, mock_page, mock_app_state):
        """Verifie que build() retourne un ft.Column contenant un header
        'Statistiques' et le stats_container."""
        view = _make_view(mock_page, mock_app_state)

        result = view.build()

        # build() returns a ft.Column
        assert isinstance(result, ft.Column)

        # The Column should have controls: header, divider, container wrapping stats_container
        assert len(result.controls) >= 3

        # First control is the header container (from view_header)
        header_container = result.controls[0]
        assert isinstance(header_container, ft.Container)

        # The header contains a Row with a Text that includes "Statistiques"
        header_row = header_container.content
        assert isinstance(header_row, ft.Row)
        header_text = header_row.controls[0]
        assert isinstance(header_text, ft.Text)
        assert "Statistiques" in header_text.value

        # Second control is a Divider
        assert isinstance(result.controls[1], ft.Divider)

        # Third control is a Container wrapping stats_container
        stats_wrapper = result.controls[2]
        assert isinstance(stats_wrapper, ft.Container)
        assert stats_wrapper.content is view.stats_container

    @patch("daynimal.ui.views.stats_view.asyncio.create_task")
    def test_triggers_load_stats(self, mock_create_task, mock_page, mock_app_state):
        """Verifie que build() lance load_stats() en tache async."""
        view = _make_view(mock_page, mock_app_state)

        view.build()

        # asyncio.create_task should have been called once
        mock_create_task.assert_called_once()

        # The argument to create_task should be a coroutine from load_stats()
        call_args = mock_create_task.call_args[0][0]
        assert asyncio.iscoroutine(call_args)
        # Clean up the coroutine to avoid RuntimeWarning
        call_args.close()

    @patch("daynimal.ui.views.stats_view.asyncio.create_task")
    def test_uses_cached_stats(self, _mock_create_task, mock_page, mock_app_state, sample_stats):
        """Verifie que quand cached_stats est defini, build() appelle
        _display_stats immediatement sans passer par le loading.
        Au deuxieme appel de build, les stats sont deja en cache."""
        view = _make_view(mock_page, mock_app_state)

        # Pre-set cached stats
        view.cached_stats = sample_stats

        # patch.object on local view must remain with-statement
        with patch.object(view, "_display_stats", wraps=view._display_stats) as mock_display:
            view.build()

        # _display_stats should have been called immediately with cached stats
        mock_display.assert_called_once_with(sample_stats)

        # page.update() should have been called because cached_stats is not None
        mock_page.update.assert_called()


# =============================================================================
# SECTION 2 : load_stats
# =============================================================================


class TestStatsViewLoadStats:
    """Tests pour load_stats()."""

    @pytest.mark.asyncio
    @patch("daynimal.ui.views.stats_view.asyncio.sleep", new_callable=AsyncMock)
    @patch("daynimal.ui.views.stats_view.asyncio.to_thread", new_callable=AsyncMock)
    async def test_shows_loading_when_no_cache(self, mock_to_thread, _mock_sleep, mock_page, mock_app_state):
        """Verifie que quand cached_stats est None, load_stats() affiche
        d'abord un ProgressRing pendant le chargement."""
        view = _make_view(mock_page, mock_app_state)
        view.cached_stats = None

        loading_controls_captured = []

        def capture_loading_state():
            # Capture the controls at the moment update is called
            if view.stats_container.controls:
                ctrl = view.stats_container.controls[0]
                if isinstance(ctrl, ft.Container) and isinstance(ctrl.content, ft.Column):
                    for child in ctrl.content.controls:
                        if isinstance(child, ft.ProgressRing):
                            loading_controls_captured.append(True)

        mock_page.update = MagicMock(side_effect=capture_loading_state)

        mock_to_thread.return_value = {
            "total_taxa": 100,
            "species_count": 80,
            "enriched_count": 10,
            "vernacular_names": 200,
            "enrichment_progress": "10/80 (12.5%)",
        }

        await view.load_stats()

        # The loading ProgressRing should have been shown
        assert len(loading_controls_captured) > 0, "ProgressRing should have been shown during loading"

    @pytest.mark.asyncio
    @patch("daynimal.ui.views.stats_view.asyncio.sleep", new_callable=AsyncMock)
    @patch("daynimal.ui.views.stats_view.asyncio.to_thread", new_callable=AsyncMock)
    async def test_creates_four_stat_cards(self, mock_to_thread, _mock_sleep, mock_page, mock_app_state, sample_stats):
        """Verifie que load_stats() cree exactement 4 stat cards dans
        stats_container: total_taxa, species_count, enriched_count,
        vernacular_names."""
        view = _make_view(mock_page, mock_app_state)

        mock_to_thread.return_value = sample_stats

        await view.load_stats()

        # stats_container should have exactly 4 cards
        assert len(view.stats_container.controls) == 4

        # All controls should be ft.Card instances
        for card in view.stats_container.controls:
            assert isinstance(card, ft.Card)

    @pytest.mark.asyncio
    @patch("daynimal.ui.views.stats_view.asyncio.sleep", new_callable=AsyncMock)
    @patch("daynimal.ui.views.stats_view.asyncio.to_thread", new_callable=AsyncMock)
    async def test_error_shows_error(self, mock_to_thread, _mock_sleep, mock_page, mock_app_state):
        """Verifie que si get_stats() leve une exception, un container
        d'erreur est affiche."""
        view = _make_view(mock_page, mock_app_state)

        mock_to_thread.side_effect = RuntimeError("DB connection failed")

        await view.load_stats()

        # stats_container should show an error container
        assert len(view.stats_container.controls) == 1
        error_container = view.stats_container.controls[0]
        assert isinstance(error_container, ft.Container)

        # The error container should have a Column with an error icon
        error_column = error_container.content
        assert isinstance(error_column, ft.Column)

        # Find the error Icon and error text
        has_error_icon = False
        has_error_text = False
        for ctrl in error_column.controls:
            if isinstance(ctrl, ft.Icon) and ctrl.icon == ft.Icons.ERROR:
                has_error_icon = True
            if isinstance(ctrl, ft.Text) and "Erreur" in str(ctrl.value):
                has_error_text = True

        assert has_error_icon, "Error icon should be displayed"
        assert has_error_text, "Error text should be displayed"

    @pytest.mark.asyncio
    @patch("daynimal.ui.views.stats_view.asyncio.sleep", new_callable=AsyncMock)
    @patch("daynimal.ui.views.stats_view.asyncio.to_thread", new_callable=AsyncMock)
    async def test_sets_cached_stats(self, mock_to_thread, _mock_sleep, mock_page, mock_app_state, sample_stats):
        """Verifie que apres un chargement reussi, self.cached_stats
        est mis a jour avec le dict retourne par get_stats()."""
        view = _make_view(mock_page, mock_app_state)

        # Initially no cache
        assert view.cached_stats is None

        mock_to_thread.return_value = sample_stats

        await view.load_stats()

        # After loading, cached_stats should be set
        assert view.cached_stats == sample_stats
        assert view.cached_stats["total_taxa"] == 163000
        assert view.cached_stats["species_count"] == 160000
        assert view.cached_stats["enriched_count"] == 500
        assert view.cached_stats["vernacular_names"] == 1100000


# =============================================================================
# SECTION 3 : _stat_card
# =============================================================================


class TestStatCard:
    """Tests pour _stat_card(icon, color, value, label, subtitle)."""

    def test_returns_ft_card(self, mock_page, mock_app_state):
        """Verifie que _stat_card retourne un ft.Card contenant un Row
        avec un cercle colore (Container avec border_radius) contenant
        l'icone, et une Column avec la valeur et le label."""
        view = _make_view(mock_page, mock_app_state)

        card = view._stat_card(ft.Icons.PETS, ft.Colors.BLUE, "1,000", "Taxa")

        # Returns a Card
        assert isinstance(card, ft.Card)

        # Card has a Container as content
        card_container = card.content
        assert isinstance(card_container, ft.Container)

        # Container has a Row
        row = card_container.content
        assert isinstance(row, ft.Row)

        # Row has 2 controls: icon circle and text column
        assert len(row.controls) == 2

        # First control is the icon circle (Container with border_radius)
        icon_circle = row.controls[0]
        assert isinstance(icon_circle, ft.Container)
        assert icon_circle.border_radius == 22
        assert icon_circle.bgcolor == ft.Colors.BLUE

        # Icon circle contains an Icon
        assert isinstance(icon_circle.content, ft.Icon)

        # Second control is a Column with texts
        text_column = row.controls[1]
        assert isinstance(text_column, ft.Column)

    def test_card_has_correct_value(self, mock_page, mock_app_state):
        """Verifie que la valeur affichee dans le card correspond au
        parametre 'value' (ex: '163,000' pour 163000)."""
        view = _make_view(mock_page, mock_app_state)

        card = view._stat_card(ft.Icons.PETS, ft.Colors.BLUE, "163,000", "Taxa totaux")

        # Navigate to the text column
        row = card.content.content
        text_column = row.controls[1]

        # First text in column is the value
        value_text = text_column.controls[0]
        assert isinstance(value_text, ft.Text)
        assert value_text.value == "163,000"
        assert value_text.weight == ft.FontWeight.BOLD

    def test_card_with_subtitle(self, mock_page, mock_app_state):
        """Verifie que quand subtitle est fourni, il est affiche
        sous le label principal."""
        view = _make_view(mock_page, mock_app_state)

        card = view._stat_card(
            ft.Icons.INFO, ft.Colors.GREEN_500, "500", "Enrichis",
            subtitle="0.3% des especes"
        )

        row = card.content.content
        text_column = row.controls[1]

        # Should have 3 texts: value, label, subtitle
        assert len(text_column.controls) == 3

        value_text = text_column.controls[0]
        label_text = text_column.controls[1]
        subtitle_text = text_column.controls[2]

        assert value_text.value == "500"
        assert label_text.value == "Enrichis"
        assert subtitle_text.value == "0.3% des especes"
        assert subtitle_text.size == 12

    def test_card_without_subtitle(self, mock_page, mock_app_state):
        """Verifie que quand subtitle est None, seuls la valeur et le label
        sont affiches (pas de texte supplementaire)."""
        view = _make_view(mock_page, mock_app_state)

        card = view._stat_card(ft.Icons.PETS, ft.Colors.BLUE, "1,000", "Taxa")

        row = card.content.content
        text_column = row.controls[1]

        # Should have only 2 texts: value and label (no subtitle)
        assert len(text_column.controls) == 2

        value_text = text_column.controls[0]
        label_text = text_column.controls[1]
        assert value_text.value == "1,000"
        assert label_text.value == "Taxa"


# =============================================================================
# SECTION 4 : _display_stats
# =============================================================================


class TestDisplayStats:
    """Tests pour _display_stats(stats)."""

    def test_displays_total_taxa(self, mock_page, mock_app_state, sample_stats):
        """Verifie que le premier card affiche le nombre total de taxa
        avec l'icone PETS et la couleur bleue."""
        view = _make_view(mock_page, mock_app_state)

        view._display_stats(sample_stats)

        # First card is total_taxa
        assert len(view.stats_container.controls) == 4
        first_card = view.stats_container.controls[0]
        assert isinstance(first_card, ft.Card)

        # Navigate to the icon circle and check icon
        row = first_card.content.content
        icon_circle = row.controls[0]
        icon = icon_circle.content
        assert isinstance(icon, ft.Icon)
        assert icon.icon == ft.Icons.PETS

        # Check the value text contains the formatted number
        text_column = row.controls[1]
        value_text = text_column.controls[0]
        assert "163" in value_text.value

        # Check label
        label_text = text_column.controls[1]
        assert label_text.value == "Taxa totaux"

    def test_displays_species_count(self, mock_page, mock_app_state, sample_stats):
        """Verifie que le deuxieme card affiche le nombre d'especes."""
        view = _make_view(mock_page, mock_app_state)

        view._display_stats(sample_stats)

        second_card = view.stats_container.controls[1]
        assert isinstance(second_card, ft.Card)

        row = second_card.content.content
        text_column = row.controls[1]

        value_text = text_column.controls[0]
        # 160000 formatted: "160,000"
        assert "160" in value_text.value

        label_text = text_column.controls[1]
        assert "Esp" in label_text.value

        # Check icon is FAVORITE
        icon_circle = row.controls[0]
        icon = icon_circle.content
        assert icon.icon == ft.Icons.FAVORITE

    def test_displays_enriched_with_progress(self, mock_page, mock_app_state, sample_stats):
        """Verifie que le card 'enriched' affiche le nombre d'animaux enrichis
        avec un sous-titre montrant le pourcentage (ex: '0.3% des especes')."""
        view = _make_view(mock_page, mock_app_state)

        view._display_stats(sample_stats)

        third_card = view.stats_container.controls[2]
        assert isinstance(third_card, ft.Card)

        row = third_card.content.content
        text_column = row.controls[1]

        # Value: 500
        value_text = text_column.controls[0]
        assert "500" in value_text.value

        # Label: Animaux enrichis
        label_text = text_column.controls[1]
        assert label_text.value == "Animaux enrichis"

        # Subtitle: enrichment_progress (e.g. "500/160000 (0.3%)")
        assert len(text_column.controls) == 3
        subtitle_text = text_column.controls[2]
        assert "0.3%" in subtitle_text.value

        # Check icon is INFO with GREEN color
        icon_circle = row.controls[0]
        assert icon_circle.bgcolor == ft.Colors.GREEN_500
        icon = icon_circle.content
        assert icon.icon == ft.Icons.INFO

    def test_displays_vernacular_names(self, mock_page, mock_app_state, sample_stats):
        """Verifie que le dernier card affiche le nombre de noms vernaculaires."""
        view = _make_view(mock_page, mock_app_state)

        view._display_stats(sample_stats)

        fourth_card = view.stats_container.controls[3]
        assert isinstance(fourth_card, ft.Card)

        row = fourth_card.content.content
        text_column = row.controls[1]

        value_text = text_column.controls[0]
        # 1100000 formatted: "1,100,000"
        assert "1" in value_text.value
        assert "100" in value_text.value

        label_text = text_column.controls[1]
        assert label_text.value == "Noms vernaculaires"

        # Check icon is TRANSLATE with AMBER color
        icon_circle = row.controls[0]
        assert icon_circle.bgcolor == ft.Colors.AMBER_500
        icon = icon_circle.content
        assert icon.icon == ft.Icons.TRANSLATE

        # No subtitle for vernacular names
        assert len(text_column.controls) == 2
