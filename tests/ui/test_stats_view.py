"""Tests pour daynimal/ui/views/stats_view.py — Vue Statistiques.

Couvre: StatsView (build, _stat_card, _display_stats, load_stats).

Stratégie: on mock AppState.repository.get_stats et ft.Page.
On vérifie que les stat cards sont créées avec les bonnes valeurs
et que le caching fonctionne (deuxième build utilise les stats cachées).
"""

import asyncio
from unittest.mock import MagicMock, patch, AsyncMock

import flet as ft
import pytest


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
    """Mock d'AppState avec repository.get_stats."""
    # todo
    pass


@pytest.fixture
def mock_debugger():
    """Mock de FletDebugger."""
    # todo
    pass


@pytest.fixture
def sample_stats():
    """Statistiques simulées retournées par get_stats()."""
    return {
        "total_taxa": 163000,
        "species_count": 160000,
        "enriched_count": 500,
        "vernacular_names": 1100000,
    }


# =============================================================================
# SECTION 1 : StatsView.build
# =============================================================================


class TestStatsViewBuild:
    """Tests pour StatsView.build()."""

    def test_returns_column_with_header(self, mock_page, mock_app_state, mock_debugger):
        """Vérifie que build() retourne un ft.Column contenant un header
        'Statistiques' et le stats_container."""
        # todo
        pass

    def test_triggers_load_stats(self, mock_page, mock_app_state, mock_debugger):
        """Vérifie que build() lance load_stats() en tâche async."""
        # todo
        pass

    def test_uses_cached_stats(self, mock_page, mock_app_state, mock_debugger, sample_stats):
        """Vérifie que quand cached_stats est défini, build() appelle
        _display_stats immédiatement sans passer par le loading.
        Au deuxième appel de build, les stats sont déjà en cache."""
        # todo
        pass


# =============================================================================
# SECTION 2 : load_stats
# =============================================================================


class TestStatsViewLoadStats:
    """Tests pour load_stats()."""

    @pytest.mark.asyncio
    async def test_shows_loading_when_no_cache(self, mock_page, mock_app_state, mock_debugger):
        """Vérifie que quand cached_stats est None, load_stats() affiche
        d'abord un ProgressRing pendant le chargement."""
        # todo
        pass

    @pytest.mark.asyncio
    async def test_creates_four_stat_cards(self, mock_page, mock_app_state, mock_debugger, sample_stats):
        """Vérifie que load_stats() crée exactement 4 stat cards dans
        stats_container: total_taxa, species_count, enriched_count,
        vernacular_names."""
        # todo
        pass

    @pytest.mark.asyncio
    async def test_error_shows_error(self, mock_page, mock_app_state, mock_debugger):
        """Vérifie que si get_stats() lève une exception, un container
        d'erreur est affiché."""
        # todo
        pass

    @pytest.mark.asyncio
    async def test_sets_cached_stats(self, mock_page, mock_app_state, mock_debugger, sample_stats):
        """Vérifie que après un chargement réussi, self.cached_stats
        est mis à jour avec le dict retourné par get_stats()."""
        # todo
        pass


# =============================================================================
# SECTION 3 : _stat_card
# =============================================================================


class TestStatCard:
    """Tests pour _stat_card(icon, color, value, label, subtitle)."""

    def test_returns_ft_card(self, mock_page, mock_app_state, mock_debugger):
        """Vérifie que _stat_card retourne un ft.Card contenant un Row
        avec un cercle coloré (Container avec border_radius) contenant
        l'icône, et une Column avec la valeur et le label."""
        # todo
        pass

    def test_card_has_correct_value(self, mock_page, mock_app_state, mock_debugger):
        """Vérifie que la valeur affichée dans le card correspond au
        paramètre 'value' (ex: '163 000' pour 163000)."""
        # todo
        pass

    def test_card_with_subtitle(self, mock_page, mock_app_state, mock_debugger):
        """Vérifie que quand subtitle est fourni, il est affiché
        sous le label principal."""
        # todo
        pass

    def test_card_without_subtitle(self, mock_page, mock_app_state, mock_debugger):
        """Vérifie que quand subtitle est None, seuls la valeur et le label
        sont affichés (pas de texte supplémentaire)."""
        # todo
        pass


# =============================================================================
# SECTION 4 : _display_stats
# =============================================================================


class TestDisplayStats:
    """Tests pour _display_stats(stats)."""

    def test_displays_total_taxa(self, mock_page, mock_app_state, mock_debugger, sample_stats):
        """Vérifie que le premier card affiche le nombre total de taxa
        avec l'icône PETS et la couleur bleue."""
        # todo
        pass

    def test_displays_species_count(self, mock_page, mock_app_state, mock_debugger, sample_stats):
        """Vérifie que le deuxième card affiche le nombre d'espèces."""
        # todo
        pass

    def test_displays_enriched_with_progress(self, mock_page, mock_app_state, mock_debugger, sample_stats):
        """Vérifie que le card 'enriched' affiche le nombre d'animaux enrichis
        avec un sous-titre montrant le pourcentage (ex: '0.3% des espèces')."""
        # todo
        pass

    def test_displays_vernacular_names(self, mock_page, mock_app_state, mock_debugger, sample_stats):
        """Vérifie que le dernier card affiche le nombre de noms vernaculaires."""
        # todo
        pass
