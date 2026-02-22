"""Tests pour daynimal/ui/app_controller.py — Contrôleur principal de l'app.

Couvre: AppController (init, build, navigation, load_animal, favorite_toggle,
offline_banner, retry_connection, cleanup).

Stratégie: on mock ft.Page, AppState, NotificationService et les vues.
On vérifie que la navigation dispatch aux bonnes vues, que les actions
(favorite, load animal) appellent les bonnes méthodes du repository,
et que le lifecycle (cleanup) ferme proprement les ressources.

NOTE: On instancie le vrai AppController mais avec des dépendances mockées.
Les vues sont réelles (instanciées avec des mocks de page/state).
"""

from unittest.mock import MagicMock, patch, AsyncMock

import flet as ft
import pytest

from daynimal.schemas import AnimalInfo, Taxon, TaxonomicRank


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def mock_page():
    """Crée un mock de ft.Page avec les attributs nécessaires pour AppController."""
    page = MagicMock(spec=ft.Page)
    page.theme_mode = ft.ThemeMode.LIGHT
    page.update = MagicMock()
    page.show_dialog = MagicMock()
    page.pop_dialog = MagicMock()
    page.run_task = MagicMock()
    page.controls = []
    page.window = MagicMock()
    return page


@pytest.fixture
def mock_repository():
    """Crée un mock de AnimalRepository."""
    repo = MagicMock()
    repo.get_by_id = MagicMock(return_value=None)
    repo.add_to_history = MagicMock()
    repo.add_favorite = MagicMock(return_value=True)
    repo.remove_favorite = MagicMock(return_value=True)
    repo.is_favorite = MagicMock(return_value=False)
    repo.get_setting = MagicMock(return_value="false")
    repo.set_setting = MagicMock()
    repo.connectivity = MagicMock()
    repo.connectivity.is_online = True
    repo.connectivity.force_offline = False
    repo.image_cache = MagicMock()
    repo.image_cache.get_local_path = MagicMock(return_value=None)
    repo.close = MagicMock()
    return repo


@pytest.fixture
def sample_animal():
    """Crée un AnimalInfo minimal pour les tests."""
    taxon = Taxon(
        taxon_id=42,
        scientific_name="Canis lupus",
        canonical_name="Canis lupus",
        rank=TaxonomicRank.SPECIES,
        kingdom="Animalia",
        phylum="Chordata",
        class_="Mammalia",
        order="Carnivora",
        family="Canidae",
        genus="Canis",
        vernacular_names={"en": ["Wolf"], "fr": ["Loup"]},
    )
    return AnimalInfo(taxon=taxon)


def _create_controller(mock_page, mock_repository):
    """Helper: crée un AppController avec des dépendances mockées."""
    with (
        patch("daynimal.ui.app_controller.AppState") as MockAppState,
        patch("daynimal.ui.app_controller.NotificationService") as MockNotifService,
    ):
        mock_state = MagicMock()
        mock_state.repository = mock_repository
        mock_state.is_online = True
        mock_state.image_cache = mock_repository.image_cache
        mock_state.current_animal = None
        mock_state.current_image_index = 0
        mock_state.close_repository = MagicMock()
        MockAppState.return_value = mock_state

        mock_notif = MagicMock()
        mock_notif.start = MagicMock()
        mock_notif.stop = MagicMock()
        MockNotifService.return_value = mock_notif

        from daynimal.ui.app_controller import AppController

        controller = AppController(page=mock_page)

    return controller


@pytest.fixture
def controller(mock_page, mock_repository):
    """Crée un AppController avec toutes les dépendances mockées."""
    return _create_controller(mock_page, mock_repository)


# =============================================================================
# SECTION 1 : AppController.__init__
# =============================================================================


class TestAppControllerInit:
    """Tests pour AppController.__init__(page)."""

    def test_creates_all_six_views(self, mock_page, mock_repository):
        """Vérifie que __init__ crée les 6 vues: TodayView, HistoryView,
        FavoritesView, SearchView, StatsView, SettingsView.
        Chaque vue doit être stockée dans l'attribut correspondant."""
        controller = _create_controller(mock_page, mock_repository)

        from daynimal.ui.views.today_view import TodayView
        from daynimal.ui.views.history_view import HistoryView
        from daynimal.ui.views.favorites_view import FavoritesView
        from daynimal.ui.views.search_view import SearchView
        from daynimal.ui.views.stats_view import StatsView
        from daynimal.ui.views.settings_view import SettingsView

        assert isinstance(controller.discovery_view, TodayView)
        assert isinstance(controller.history_view, HistoryView)
        assert isinstance(controller.favorites_view, FavoritesView)
        assert isinstance(controller.search_view, SearchView)
        assert isinstance(controller.stats_view, StatsView)
        assert isinstance(controller.settings_view, SettingsView)

    def test_creates_navigation_bar(self, mock_page, mock_repository):
        """Vérifie que __init__ crée une NavigationBar avec 6 destinations
        (Aujourd'hui, Historique, Favoris, Recherche, Stats, Paramètres).
        La barre de navigation doit avoir on_change connecté à on_nav_change."""
        controller = _create_controller(mock_page, mock_repository)

        assert isinstance(controller.nav_bar, ft.NavigationBar)
        assert len(controller.nav_bar.destinations) == 6
        assert controller.nav_bar.on_change == controller.on_nav_change

        # Verify destination labels
        labels = [d.label for d in controller.nav_bar.destinations]
        assert "Découverte" in labels
        assert "Historique" in labels
        assert "Favoris" in labels
        assert "Recherche" in labels
        assert "Statistiques" in labels
        assert "Paramètres" in labels

    def test_creates_offline_banner(self, mock_page, mock_repository):
        """Vérifie que __init__ crée un bandeau offline (Container avec
        Row contenant un Icon WIFI_OFF et un texte 'Mode hors ligne').
        Le bandeau doit être initialement invisible (visible=False)."""
        controller = _create_controller(mock_page, mock_repository)

        banner = controller.offline_banner
        assert isinstance(banner, ft.Container)
        assert banner.visible is False

        # The banner content is a Row
        row = banner.content
        assert isinstance(row, ft.Row)

        # The row contains an Icon and a Text with "hors ligne"
        icons = [c for c in row.controls if isinstance(c, ft.Icon)]
        texts = [c for c in row.controls if isinstance(c, ft.Text)]
        assert len(icons) >= 1
        assert icons[0].icon == ft.Icons.WIFI_OFF
        assert any("hors ligne" in t.value.lower() for t in texts)

    def test_creates_app_state(self, mock_page, mock_repository):
        """Vérifie que __init__ crée un AppState stocké dans self.state."""
        controller = _create_controller(mock_page, mock_repository)
        assert controller.state is not None

    def test_creates_notification_service(self, mock_page, mock_repository):
        """Vérifie que __init__ crée un NotificationService avec on_clicked."""
        with (
            patch("daynimal.ui.app_controller.AppState") as MockAppState,
            patch("daynimal.ui.app_controller.NotificationService") as MockNotifService,
        ):
            mock_state = MagicMock()
            mock_state.repository = mock_repository
            mock_state.is_online = True
            mock_state.image_cache = mock_repository.image_cache
            mock_state.current_animal = None
            mock_state.current_image_index = 0
            mock_state.close_repository = MagicMock()
            MockAppState.return_value = mock_state

            mock_notif = MagicMock()
            MockNotifService.return_value = mock_notif

            from daynimal.ui.app_controller import AppController

            controller = AppController(page=mock_page)

            MockNotifService.assert_called_once_with(
                mock_state.repository, on_clicked=controller._on_notification_clicked
            )


# =============================================================================
# SECTION 2 : AppController.build
# =============================================================================


class TestAppControllerBuild:
    """Tests pour AppController.build()."""

    def test_returns_column_with_banner_content_nav(self, controller):
        """Vérifie que build() retourne un ft.Column contenant:
        1. Le bandeau offline
        2. Le content_container (avec expand=True)
        3. La barre de navigation."""
        layout = controller.build()

        assert isinstance(layout, ft.Column)
        assert layout.expand is True
        assert len(layout.controls) == 3
        assert layout.controls[0] is controller.offline_banner
        assert layout.controls[1] is controller.content_container
        assert layout.controls[2] is controller.nav_bar

    def test_starts_notification_service(self, controller):
        """Vérifie que build() appelle notification_service.start()."""
        controller.build()
        controller.notification_service.start.assert_called_once()

    def test_shows_discovery_view(self, controller):
        """Vérifie que build() appelle show_discovery_view() pour afficher
        la vue par défaut."""
        with patch.object(
            controller, "show_discovery_view", wraps=controller.show_discovery_view
        ) as mock_show:
            controller.build()
            mock_show.assert_called_once()

        assert controller.current_view_name == "discovery"

    def test_auto_load_enabled_by_default(self, controller, mock_page):
        """Vérifie que build() lance _load_random_animal quand
        auto_load_on_start est 'true' (défaut)."""
        controller.state.repository.get_setting = MagicMock(return_value="true")
        mock_page.run_task.reset_mock()

        controller.build()

        mock_page.run_task.assert_called_with(
            controller.discovery_view._load_random_animal, None
        )

    def test_auto_load_disabled(self, controller, mock_page):
        """Vérifie que build() ne lance PAS _load_random_animal quand
        auto_load_on_start est 'false'."""
        controller.state.repository.get_setting = MagicMock(return_value="false")
        mock_page.run_task.reset_mock()

        controller.build()

        # run_task should NOT have been called with _load_random_animal
        for call_args in mock_page.run_task.call_args_list:
            assert call_args[0][0] != controller.discovery_view._load_random_animal


# =============================================================================
# SECTION 3 : Navigation
# =============================================================================


def _make_nav_event(index):
    """Crée un event mock pour on_nav_change avec selected_index."""
    event = MagicMock()
    event.control = MagicMock()
    event.control.selected_index = index
    return event


class TestAppControllerNavigation:
    """Tests pour on_nav_change et les méthodes show_*_view."""

    def test_on_nav_change_index_0_shows_today(self, controller):
        """Vérifie que on_nav_change avec selected_index=0 appelle
        show_discovery_view(). On crée un event mock avec control.selected_index=0."""
        with patch.object(controller, "show_discovery_view") as mock_show:
            controller.on_nav_change(_make_nav_event(0))
            mock_show.assert_called_once()

    def test_on_nav_change_index_1_shows_history(self, controller):
        """Vérifie que index=1 appelle show_history_view()."""
        with patch.object(controller, "show_history_view") as mock_show:
            controller.on_nav_change(_make_nav_event(1))
            mock_show.assert_called_once()

    def test_on_nav_change_index_2_shows_favorites(self, controller):
        """Vérifie que index=2 appelle show_favorites_view()."""
        with patch.object(controller, "show_favorites_view") as mock_show:
            controller.on_nav_change(_make_nav_event(2))
            mock_show.assert_called_once()

    def test_on_nav_change_index_3_shows_search(self, controller):
        """Vérifie que index=3 appelle show_search_view()."""
        with patch.object(controller, "show_search_view") as mock_show:
            controller.on_nav_change(_make_nav_event(3))
            mock_show.assert_called_once()

    def test_on_nav_change_index_4_shows_stats(self, controller):
        """Vérifie que index=4 appelle show_stats_view()."""
        with patch.object(controller, "show_stats_view") as mock_show:
            controller.on_nav_change(_make_nav_event(4))
            mock_show.assert_called_once()

    def test_on_nav_change_index_5_shows_settings(self, controller):
        """Vérifie que index=5 appelle show_settings_view()."""
        with patch.object(controller, "show_settings_view") as mock_show:
            controller.on_nav_change(_make_nav_event(5))
            mock_show.assert_called_once()

    @patch("asyncio.create_task")
    @patch("daynimal.ui.app_controller.logger")
    def test_on_nav_change_logs_view_change(self, mock_logger, _mock_task, controller):
        """Vérifie que on_nav_change logue le changement de vue."""
        controller.on_nav_change(_make_nav_event(2))
        mock_logger.info.assert_called()
        log_msg = mock_logger.info.call_args[0][0]
        assert "Favorites" in log_msg

    def test_show_discovery_view_sets_content(self, controller, mock_page):
        """Vérifie que show_discovery_view() remplace le contenu du
        content_container par le résultat de today_view.build()
        et appelle page.update()."""
        mock_page.update.reset_mock()
        controller.show_discovery_view()

        assert len(controller.content_container.controls) == 1
        assert controller.current_view_name == "discovery"
        mock_page.update.assert_called()

    def test_show_history_view_calls_build(self, controller, mock_page):
        """Vérifie que show_history_view() appelle history_view.build()."""
        with patch.object(
            controller.history_view, "build", return_value=ft.Text("history")
        ) as mock_build:
            mock_page.update.reset_mock()
            controller.show_history_view()
            mock_build.assert_called_once()
            assert controller.current_view_name == "history"
            mock_page.update.assert_called()

    def test_show_favorites_view_calls_build(self, controller, mock_page):
        """Vérifie que show_favorites_view() appelle favorites_view.build()."""
        with patch.object(
            controller.favorites_view, "build", return_value=ft.Text("favs")
        ) as mock_build:
            mock_page.update.reset_mock()
            controller.show_favorites_view()
            mock_build.assert_called_once()
            assert controller.current_view_name == "favorites"
            mock_page.update.assert_called()

    def test_show_search_view_calls_build(self, controller, mock_page):
        """Vérifie que show_search_view() appelle search_view.build()."""
        with patch.object(
            controller.search_view, "build", return_value=ft.Text("search")
        ) as mock_build:
            mock_page.update.reset_mock()
            controller.show_search_view()
            mock_build.assert_called_once()
            assert controller.current_view_name == "search"
            mock_page.update.assert_called()

    def test_show_stats_view_calls_build(self, controller, mock_page):
        """Vérifie que show_stats_view() appelle stats_view.build()."""
        with patch.object(
            controller.stats_view, "build", return_value=ft.Text("stats")
        ) as mock_build:
            mock_page.update.reset_mock()
            controller.show_stats_view()
            mock_build.assert_called_once()
            assert controller.current_view_name == "stats"
            mock_page.update.assert_called()

    def test_show_settings_view_calls_build(self, controller, mock_page):
        """Vérifie que show_settings_view() appelle settings_view.build()."""
        with patch.object(
            controller.settings_view, "build", return_value=ft.Text("settings")
        ) as mock_build:
            mock_page.update.reset_mock()
            controller.show_settings_view()
            mock_build.assert_called_once()
            assert controller.current_view_name == "settings"
            mock_page.update.assert_called()


# =============================================================================
# SECTION 4 : Load animal from various sources
# =============================================================================


class TestLoadAnimalFromSource:
    """Tests pour load_animal_from_history/favorite/search."""

    @pytest.mark.asyncio
    async def test_load_animal_from_history(self, controller):
        """Vérifie que load_animal_from_history(taxon_id) appelle
        _load_and_display_animal avec enrich=True, add_to_history=False.
        L'animal chargé depuis l'historique est enrichi mais pas re-ajouté
        à l'historique."""
        with patch.object(
            controller, "_load_and_display_animal", new_callable=AsyncMock
        ) as mock_load:
            await controller.load_animal_from_history(42)
            mock_load.assert_awaited_once_with(
                taxon_id=42, source="history", enrich=True, add_to_history=False
            )

    @pytest.mark.asyncio
    async def test_load_animal_from_favorite(self, controller):
        """Vérifie que load_animal_from_favorite(taxon_id) appelle
        _load_and_display_animal avec enrich=True, add_to_history=False."""
        with patch.object(
            controller, "_load_and_display_animal", new_callable=AsyncMock
        ) as mock_load:
            await controller.load_animal_from_favorite(42)
            mock_load.assert_awaited_once_with(
                taxon_id=42, source="favorite", enrich=True, add_to_history=False
            )

    @pytest.mark.asyncio
    async def test_load_animal_from_search(self, controller):
        """Vérifie que load_animal_from_search(taxon_id) appelle
        _load_and_display_animal avec enrich=True, add_to_history=True.
        L'animal trouvé via recherche est ajouté à l'historique."""
        with patch.object(
            controller, "_load_and_display_animal", new_callable=AsyncMock
        ) as mock_load:
            await controller.load_animal_from_search(42)
            mock_load.assert_awaited_once_with(
                taxon_id=42, source="search", enrich=True, add_to_history=True
            )


# =============================================================================
# SECTION 5 : _load_and_display_animal
# =============================================================================


class TestLoadAndDisplayAnimal:
    """Tests pour _load_and_display_animal (méthode interne)."""

    @pytest.mark.asyncio
    async def test_success_displays_animal(self, controller, mock_page, sample_animal):
        """Vérifie que _load_and_display_animal: 1) switche la nav à index 0,
        2) affiche un LoadingWidget, 3) appelle repo.get_by_id en thread,
        4) appelle today_view._display_animal avec l'animal retourné,
        5) appelle page.update().
        Mock: repo.get_by_id retourne un AnimalInfo valide."""
        controller.state.repository.get_by_id = MagicMock(return_value=sample_animal)

        with (
            patch.object(controller.discovery_view, "_display_animal") as mock_display,
            patch("daynimal.ui.app_controller.asyncio.sleep", new_callable=AsyncMock),
            patch(
                "daynimal.ui.app_controller.asyncio.to_thread",
                new_callable=AsyncMock,
                return_value=sample_animal,
            ),
        ):
            await controller._load_and_display_animal(
                taxon_id=42, source="history", enrich=True, add_to_history=False
            )

            # Nav bar should switch to today (index 0)
            assert controller.nav_bar.selected_index == 0
            # _display_animal should be called with the animal
            mock_display.assert_called_once_with(sample_animal)
            # page.update should have been called
            mock_page.update.assert_called()

    @pytest.mark.asyncio
    async def test_not_found_shows_error(self, controller, mock_page):
        """Vérifie que si repo.get_by_id retourne None,
        un ErrorWidget est affiché dans le content_container."""
        from daynimal.ui.components.widgets import ErrorWidget

        with (
            patch("daynimal.ui.app_controller.asyncio.sleep", new_callable=AsyncMock),
            patch(
                "daynimal.ui.app_controller.asyncio.to_thread",
                new_callable=AsyncMock,
                return_value=None,
            ),
        ):
            await controller._load_and_display_animal(
                taxon_id=999, source="history", enrich=True, add_to_history=False
            )

            # today_animal_container should contain an ErrorWidget
            controls = controller.discovery_view.today_animal_container.controls
            assert len(controls) == 1
            assert isinstance(controls[0], ErrorWidget)

    @pytest.mark.asyncio
    async def test_exception_shows_error(self, controller, mock_page):
        """Vérifie que si repo.get_by_id lève une exception,
        un ErrorWidget est affiché avec le message d'erreur."""
        from daynimal.ui.components.widgets import ErrorWidget

        with (
            patch("daynimal.ui.app_controller.asyncio.sleep", new_callable=AsyncMock),
            patch(
                "daynimal.ui.app_controller.asyncio.to_thread",
                new_callable=AsyncMock,
                side_effect=Exception("DB error"),
            ),
        ):
            await controller._load_and_display_animal(
                taxon_id=42, source="search", enrich=True, add_to_history=True
            )

            controls = controller.discovery_view.today_animal_container.controls
            assert len(controls) == 1
            assert isinstance(controls[0], ErrorWidget)

    @pytest.mark.asyncio
    async def test_adds_to_history_when_requested(self, controller, sample_animal):
        """Vérifie que quand add_to_history=True, repo.add_to_history()
        est appelé avec le bon taxon_id et source."""
        controller.state.repository.get_by_id = MagicMock(return_value=sample_animal)
        controller.state.repository.add_to_history = MagicMock()

        with (
            patch.object(controller.discovery_view, "_display_animal"),
            patch("daynimal.ui.app_controller.asyncio.sleep", new_callable=AsyncMock),
            patch(
                "daynimal.ui.app_controller.asyncio.to_thread",
                new_callable=AsyncMock,
                return_value=sample_animal,
            ),
        ):
            await controller._load_and_display_animal(
                taxon_id=42, source="search", enrich=True, add_to_history=True
            )

            controller.state.repository.add_to_history.assert_called_once_with(
                42, command="search"
            )

    @pytest.mark.asyncio
    async def test_no_history_when_not_requested(self, controller, sample_animal):
        """Vérifie que quand add_to_history=False, repo.add_to_history()
        n'est PAS appelé."""
        controller.state.repository.get_by_id = MagicMock(return_value=sample_animal)
        controller.state.repository.add_to_history = MagicMock()

        with (
            patch.object(controller.discovery_view, "_display_animal"),
            patch("daynimal.ui.app_controller.asyncio.sleep", new_callable=AsyncMock),
            patch(
                "daynimal.ui.app_controller.asyncio.to_thread",
                new_callable=AsyncMock,
                return_value=sample_animal,
            ),
        ):
            await controller._load_and_display_animal(
                taxon_id=42, source="history", enrich=True, add_to_history=False
            )

            controller.state.repository.add_to_history.assert_not_called()

    @pytest.mark.asyncio
    async def test_updates_offline_banner(self, controller, sample_animal):
        """Vérifie que _load_and_display_animal appelle _update_offline_banner()
        après le chargement."""
        with (
            patch.object(controller.discovery_view, "_display_animal"),
            patch.object(controller, "_update_offline_banner") as mock_banner,
            patch("daynimal.ui.app_controller.asyncio.sleep", new_callable=AsyncMock),
            patch(
                "daynimal.ui.app_controller.asyncio.to_thread",
                new_callable=AsyncMock,
                return_value=sample_animal,
            ),
        ):
            await controller._load_and_display_animal(
                taxon_id=42, source="history", enrich=True, add_to_history=False
            )

            mock_banner.assert_called_once()


# =============================================================================
# SECTION 6 : Favorite toggle
# =============================================================================


class TestOnFavoriteToggle:
    """Tests pour on_favorite_toggle(taxon_id, is_favorite)."""

    def test_add_favorite(self, controller, mock_page):
        """Vérifie que on_favorite_toggle(42, False) appelle
        repo.add_favorite(42) et affiche un SnackBar 'Ajouté aux favoris'.
        is_favorite=False signifie que l'animal n'est PAS encore favori,
        donc on l'ajoute."""
        controller.state.repository.add_favorite = MagicMock(return_value=True)

        controller.on_favorite_toggle(42, False)

        controller.state.repository.add_favorite.assert_called_once_with(42)
        mock_page.show_dialog.assert_called_once()

        # Inspect the SnackBar argument
        snackbar = mock_page.show_dialog.call_args[0][0]
        assert isinstance(snackbar, ft.SnackBar)
        assert "Ajouté aux favoris" in snackbar.content.value

    def test_remove_favorite(self, controller, mock_page):
        """Vérifie que on_favorite_toggle(42, True) appelle
        repo.remove_favorite(42) et affiche un SnackBar 'Retiré des favoris'.
        is_favorite=True signifie que l'animal EST favori, donc on le retire."""
        controller.state.repository.remove_favorite = MagicMock(return_value=True)

        controller.on_favorite_toggle(42, True)

        controller.state.repository.remove_favorite.assert_called_once_with(42)
        mock_page.show_dialog.assert_called_once()

        snackbar = mock_page.show_dialog.call_args[0][0]
        assert isinstance(snackbar, ft.SnackBar)
        assert "Retiré des favoris" in snackbar.content.value

    def test_error_shows_error_snackbar(self, controller, mock_page):
        """Vérifie que si repo.add_favorite lève une exception,
        un SnackBar d'erreur est affiché via page.show_dialog."""
        controller.state.repository.add_favorite = MagicMock(
            side_effect=Exception("DB write error")
        )

        controller.on_favorite_toggle(42, False)

        # show_dialog should have been called with an error SnackBar
        mock_page.show_dialog.assert_called_once()
        snackbar = mock_page.show_dialog.call_args[0][0]
        assert isinstance(snackbar, ft.SnackBar)
        assert (
            "Erreur" in snackbar.content.value
            or "DB write error" in snackbar.content.value
        )


# =============================================================================
# SECTION 7 : Offline banner
# =============================================================================


class TestOfflineBanner:
    """Tests pour _update_offline_banner et _retry_connection."""

    def test_update_offline_banner_online(self, controller, mock_page):
        """Vérifie que quand on est en ligne (pas force_offline, is_online=True),
        le bandeau offline est masqué (visible=False)."""
        connectivity = controller.state.repository.connectivity
        connectivity.force_offline = False
        connectivity.is_online = True
        mock_page.update.reset_mock()

        controller._update_offline_banner()

        assert controller.offline_banner.visible is False
        mock_page.update.assert_called()

    def test_update_offline_banner_offline(self, controller, mock_page):
        """Vérifie que quand is_online=False (perte de connexion),
        le bandeau est visible avec le bouton Réessayer."""
        connectivity = controller.state.repository.connectivity
        connectivity.force_offline = False
        connectivity.is_online = False
        mock_page.update.reset_mock()

        controller._update_offline_banner()

        assert controller.offline_banner.visible is True
        # Le bandeau doit contenir un bouton "Réessayer"
        banner_row = controller.offline_banner.content
        has_retry = any(isinstance(c, ft.Button) for c in banner_row.controls)
        assert has_retry
        mock_page.update.assert_called()

    def test_update_offline_banner_force_offline(self, controller, mock_page):
        """Vérifie que quand force_offline=True, le bandeau s'affiche
        sans bouton Réessayer."""
        connectivity = controller.state.repository.connectivity
        connectivity.force_offline = True
        connectivity.is_online = False
        mock_page.update.reset_mock()

        controller._update_offline_banner()

        assert controller.offline_banner.visible is True
        # Le bandeau ne doit PAS contenir de bouton "Réessayer"
        banner_row = controller.offline_banner.content
        has_retry = any(isinstance(c, ft.Button) for c in banner_row.controls)
        assert not has_retry
        mock_page.update.assert_called()

    @pytest.mark.asyncio
    async def test_retry_connection_success(self, controller, mock_page, sample_animal):
        """Vérifie que _retry_connection appelle connectivity.check() en thread,
        met à jour le bandeau, et recharge l'animal si la connexion est rétablie."""
        connectivity = controller.state.repository.connectivity
        # Start offline
        connectivity.is_online = False

        # Set current animal on today_view
        controller.discovery_view.current_animal = sample_animal

        async def mock_to_thread(fn, *args, **kwargs):
            # Simulate connectivity.check() bringing us back online
            connectivity.is_online = True
            fn(*args, **kwargs)

        with (
            patch(
                "daynimal.ui.app_controller.asyncio.to_thread",
                side_effect=mock_to_thread,
            ),
            patch.object(
                controller, "_load_and_display_animal", new_callable=AsyncMock
            ) as mock_load,
            patch.object(controller, "_update_offline_banner"),
        ):
            await controller._retry_connection()

            # connectivity.check was called (via to_thread)
            connectivity.check.assert_called_once()
            # Should attempt to reload current animal since we were offline and came online
            mock_load.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_retry_connection_still_offline(
        self, controller, mock_page, sample_animal
    ):
        """Vérifie que _retry_connection n'essaie pas de recharger l'animal
        si la connexion n'est pas rétablie."""
        connectivity = controller.state.repository.connectivity
        # Start offline, stay offline
        connectivity.is_online = False

        controller.discovery_view.current_animal = sample_animal

        async def mock_to_thread(fn, *args, **kwargs):
            # check() called but stays offline
            fn(*args, **kwargs)

        with (
            patch(
                "daynimal.ui.app_controller.asyncio.to_thread",
                side_effect=mock_to_thread,
            ),
            patch.object(
                controller, "_load_and_display_animal", new_callable=AsyncMock
            ) as mock_load,
            patch.object(controller, "_update_offline_banner"),
        ):
            await controller._retry_connection()

            # Should NOT attempt to reload because still offline
            mock_load.assert_not_awaited()


# =============================================================================
# SECTION 8 : Notification click callback
# =============================================================================


class TestOnNotificationClicked:
    """Tests pour _on_notification_clicked(animal)."""

    def test_on_notification_clicked_displays_animal(
        self, controller, mock_page, sample_animal
    ):
        """Vérifie que _on_notification_clicked met nav_bar à index 0,
        affecte l'animal à today_view, appelle show_discovery_view,
        ajoute l'animal à l'historique, et amène la fenêtre au premier plan."""
        controller.nav_bar.selected_index = 3
        mock_page.update.reset_mock()

        with patch.object(
            controller, "show_discovery_view", wraps=controller.show_discovery_view
        ) as mock_show:
            controller._on_notification_clicked(sample_animal)

            assert controller.nav_bar.selected_index == 0
            assert controller.discovery_view.current_animal is sample_animal
            mock_show.assert_called_once()
            mock_page.run_task.assert_called_once_with(mock_page.window.to_front)

    def test_on_notification_clicked_adds_to_history(self, controller, sample_animal):
        """Vérifie que l'animal notifié est ajouté à l'historique
        avec command='notification'."""
        controller._on_notification_clicked(sample_animal)

        controller.state.repository.add_to_history.assert_called_once_with(
            sample_animal.taxon.taxon_id, command="notification"
        )


# =============================================================================
# SECTION 9 : Cleanup
# =============================================================================


class TestAppControllerCleanup:
    """Tests pour AppController.cleanup()."""

    def test_stops_notification_service(self, controller):
        """Vérifie que cleanup() appelle notification_service.stop()."""
        controller.cleanup()
        controller.notification_service.stop.assert_called_once()

    def test_closes_repository(self, controller):
        """Vérifie que cleanup() appelle state.close_repository()."""
        controller.cleanup()
        controller.state.close_repository.assert_called_once()
