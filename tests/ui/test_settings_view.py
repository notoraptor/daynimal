"""Tests pour daynimal/ui/views/settings_view.py -- Vue Parametres.

Couvre: SettingsView (build, _load_settings, _on_theme_toggle,
_on_offline_toggle, _on_notifications_toggle, _on_notification_time_change,
_on_clear_cache).

Strategie: on mock AppState (repository + image_cache), NotificationService
et ft.Page. On simule les evenements des controles (Switch.on_change,
Dropdown.on_change, Button.on_click) et on verifie les appels au repository
et les changements d'UI.
"""

import asyncio
from unittest.mock import MagicMock, patch, AsyncMock, PropertyMock

import flet as ft
import pytest


# =============================================================================
# Helpers
# =============================================================================


def _make_view(mock_page, mock_app_state, mock_debugger):
    """Create a SettingsView instance with mocked dependencies."""
    from daynimal.ui.views.settings_view import SettingsView

    # Patch asyncio.create_task to avoid actually running async tasks in build()
    with patch("daynimal.ui.views.settings_view.asyncio.create_task"):
        view = SettingsView(mock_page, mock_app_state, mock_debugger)
    return view


def _find_controls_of_type(control, control_type, results=None):
    """Recursively find all controls of a given type in the control tree."""
    if results is None:
        results = []

    if isinstance(control, control_type):
        results.append(control)

    # Check .controls (Column, Row, etc.)
    if hasattr(control, "controls") and control.controls:
        for child in control.controls:
            _find_controls_of_type(child, control_type, results)

    # Check .content (Container)
    if hasattr(control, "content") and control.content is not None:
        _find_controls_of_type(control.content, control_type, results)

    return results


def _find_text_values(control):
    """Recursively find all ft.Text values in the control tree."""
    texts = _find_controls_of_type(control, ft.Text)
    return [t.value for t in texts if hasattr(t, "value") and t.value]


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def mock_page():
    """Mock de ft.Page avec theme_mode."""
    page = MagicMock(spec=ft.Page)
    page.theme_mode = ft.ThemeMode.LIGHT
    page.update = MagicMock()
    page.run_task = MagicMock()
    page.width = 400
    page.height = 800
    return page


@pytest.fixture
def mock_app_state():
    """Mock d'AppState avec repository (get_setting, set_setting, get_stats,
    connectivity) et image_cache (get_cache_size, clear)."""
    state = MagicMock()

    # Repository mock
    repo = MagicMock()

    def get_setting_side_effect(key, default=None):
        settings_map = {
            "theme_mode": "light",
            "force_offline": "false",
            "notifications_enabled": "false",
            "notification_time": "08:00",
        }
        return settings_map.get(key, default)

    repo.get_setting = MagicMock(side_effect=get_setting_side_effect)
    repo.set_setting = MagicMock()
    repo.get_stats = MagicMock(
        return_value={
            "species_count": 1500000,
            "vernacular_names": 3200000,
            "enriched_count": 500,
        }
    )
    repo.connectivity = MagicMock()
    repo.connectivity.force_offline = False

    type(state).repository = PropertyMock(return_value=repo)

    # Image cache mock
    image_cache = MagicMock()
    image_cache.get_cache_size = MagicMock(return_value=5242880)  # 5 Mo
    image_cache.clear = MagicMock(return_value=10)
    type(state).image_cache = PropertyMock(return_value=image_cache)

    return state


@pytest.fixture
def mock_debugger():
    """Mock de FletDebugger."""
    debugger = MagicMock()
    debugger.logger = MagicMock()
    debugger.logger.info = MagicMock()
    debugger.logger.error = MagicMock()
    debugger.log_error = MagicMock()
    return debugger


# =============================================================================
# SECTION 1 : SettingsView.build / _load_settings
# =============================================================================


class TestSettingsViewBuild:
    """Tests pour build() et _load_settings()."""

    @patch("daynimal.ui.views.settings_view.asyncio.create_task")
    def test_build_triggers_load_settings(
        self, mock_create_task, mock_page, mock_app_state, mock_debugger
    ):
        """Verifie que build() retourne settings_container et lance
        _load_settings() en tache async."""
        from daynimal.ui.views.settings_view import SettingsView

        view = SettingsView(mock_page, mock_app_state, mock_debugger)
        result = view.build()

        # build() should return the settings_container
        assert result is view.settings_container
        # asyncio.create_task should have been called to launch _load_settings
        assert mock_create_task.called

    @pytest.mark.asyncio
    async def test_load_settings_creates_theme_toggle(
        self, mock_page, mock_app_state, mock_debugger
    ):
        """Verifie que _load_settings cree un ft.Switch pour le theme
        sombre. La valeur initiale depend de get_setting('theme_mode'):
        'dark' -> value=True, sinon False."""
        view = _make_view(mock_page, mock_app_state, mock_debugger)

        await view._load_settings()

        switches = _find_controls_of_type(view.settings_container, ft.Switch)
        theme_switches = [
            s for s in switches if s.label and "sombre" in s.label.lower()
        ]
        assert len(theme_switches) == 1
        # Default theme_mode is "light", so the switch should be False
        assert theme_switches[0].value is False

    @pytest.mark.asyncio
    async def test_load_settings_creates_theme_toggle_dark(
        self, mock_page, mock_app_state, mock_debugger
    ):
        """Verifie que quand theme_mode='dark', le Switch theme est True."""
        repo = mock_app_state.repository

        def get_setting_dark(key, default=None):
            if key == "theme_mode":
                return "dark"
            settings_map = {
                "force_offline": "false",
                "notifications_enabled": "false",
                "notification_time": "08:00",
            }
            return settings_map.get(key, default)

        repo.get_setting = MagicMock(side_effect=get_setting_dark)

        view = _make_view(mock_page, mock_app_state, mock_debugger)
        await view._load_settings()

        switches = _find_controls_of_type(view.settings_container, ft.Switch)
        theme_switches = [
            s for s in switches if s.label and "sombre" in s.label.lower()
        ]
        assert len(theme_switches) == 1
        assert theme_switches[0].value is True

    @pytest.mark.asyncio
    async def test_load_settings_creates_offline_toggle(
        self, mock_page, mock_app_state, mock_debugger
    ):
        """Verifie que _load_settings cree un ft.Switch pour le mode
        hors ligne force. La valeur depend de get_setting('force_offline')."""
        view = _make_view(mock_page, mock_app_state, mock_debugger)

        await view._load_settings()

        switches = _find_controls_of_type(view.settings_container, ft.Switch)
        offline_switches = [
            s for s in switches if s.label and "hors ligne" in s.label.lower()
        ]
        assert len(offline_switches) == 1
        # Default force_offline is "false" -> value should be False
        assert offline_switches[0].value is False

    @pytest.mark.asyncio
    async def test_load_settings_creates_notification_controls(
        self, mock_page, mock_app_state, mock_debugger
    ):
        """Verifie que _load_settings cree un Switch pour les notifications
        et un Dropdown pour l'heure de notification (options de 00:00 a 23:00)."""
        view = _make_view(mock_page, mock_app_state, mock_debugger)

        await view._load_settings()

        switches = _find_controls_of_type(view.settings_container, ft.Switch)
        notif_switches = [
            s for s in switches if s.label and "notification" in s.label.lower()
        ]
        assert len(notif_switches) == 1
        assert notif_switches[0].value is False  # default "false"

        dropdowns = _find_controls_of_type(view.settings_container, ft.Dropdown)
        assert len(dropdowns) >= 1
        # The dropdown should have 24 options (00:00 to 23:00)
        dropdown = dropdowns[0]
        assert len(dropdown.options) == 24
        # Check some known values
        option_texts = [opt.key for opt in dropdown.options]
        assert "06:00" in option_texts
        assert "08:00" in option_texts
        assert "22:00" in option_texts
        # Default notification time
        assert dropdown.value == "08:00"

    @pytest.mark.asyncio
    async def test_load_settings_shows_cache_size(
        self, mock_page, mock_app_state, mock_debugger
    ):
        """Verifie que _load_settings affiche la taille du cache d'images.
        Mock: image_cache.get_cache_size retourne 5242880 (5 Mo).
        Le texte doit afficher '5.0 Mo'."""
        view = _make_view(mock_page, mock_app_state, mock_debugger)

        await view._load_settings()

        text_values = _find_text_values(view.settings_container)
        cache_texts = [t for t in text_values if "5.0 Mo" in t]
        assert len(cache_texts) >= 1

    @pytest.mark.asyncio
    async def test_load_settings_shows_db_stats(
        self, mock_page, mock_app_state, mock_debugger
    ):
        """Verifie que _load_settings affiche les statistiques de la DB
        (nombre d'especes, etc.) depuis repository.get_stats()."""
        view = _make_view(mock_page, mock_app_state, mock_debugger)

        await view._load_settings()

        text_values = _find_text_values(view.settings_container)
        all_text = " ".join(text_values)
        # Check for species count (1 500 000 with spaces as separator)
        assert "1 500 000" in all_text
        # Check for vernacular names
        assert "3 200 000" in all_text
        # Check for enriched count
        assert "500" in all_text

    @pytest.mark.asyncio
    async def test_load_settings_error_shows_error(
        self, mock_page, mock_app_state, mock_debugger
    ):
        """Verifie que si une exception est levee pendant le chargement,
        un container d'erreur est affiche."""
        # Make get_setting raise an exception
        mock_app_state.repository.get_setting = MagicMock(
            side_effect=RuntimeError("DB connection failed")
        )

        view = _make_view(mock_page, mock_app_state, mock_debugger)

        await view._load_settings()

        # Should contain error icon and error text
        text_values = _find_text_values(view.settings_container)
        error_texts = [
            t for t in text_values if "Erreur" in t or "DB connection failed" in t
        ]
        assert len(error_texts) >= 1

        # The debugger should have been notified
        mock_debugger.log_error.assert_called()


# =============================================================================
# SECTION 2 : Theme toggle
# =============================================================================


class TestThemeToggle:
    """Tests pour _on_theme_toggle."""

    def test_toggle_to_dark(self, mock_page, mock_app_state, mock_debugger):
        """Verifie que _on_theme_toggle avec e.control.value=True
        appelle repo.set_setting('theme_mode', 'dark') et definit
        page.theme_mode = ft.ThemeMode.DARK."""
        view = _make_view(mock_page, mock_app_state, mock_debugger)

        event = MagicMock()
        event.control.value = True

        view._on_theme_toggle(event)

        mock_app_state.repository.set_setting.assert_called_with("theme_mode", "dark")
        assert mock_page.theme_mode == ft.ThemeMode.DARK

    def test_toggle_to_light(self, mock_page, mock_app_state, mock_debugger):
        """Verifie que _on_theme_toggle avec e.control.value=False
        appelle repo.set_setting('theme_mode', 'light') et definit
        page.theme_mode = ft.ThemeMode.LIGHT."""
        view = _make_view(mock_page, mock_app_state, mock_debugger)

        event = MagicMock()
        event.control.value = False

        view._on_theme_toggle(event)

        mock_app_state.repository.set_setting.assert_called_with("theme_mode", "light")
        assert mock_page.theme_mode == ft.ThemeMode.LIGHT

    def test_calls_page_update(self, mock_page, mock_app_state, mock_debugger):
        """Verifie que page.update() est appele apres le changement de theme."""
        view = _make_view(mock_page, mock_app_state, mock_debugger)

        event = MagicMock()
        event.control.value = True

        view._on_theme_toggle(event)

        mock_page.update.assert_called()

    def test_error_handled(self, mock_page, mock_app_state, mock_debugger):
        """Verifie que si set_setting leve une exception, elle est attrapee
        et loguee sans propager."""
        view = _make_view(mock_page, mock_app_state, mock_debugger)

        mock_app_state.repository.set_setting = MagicMock(
            side_effect=RuntimeError("DB write error")
        )

        event = MagicMock()
        event.control.value = True

        # Should NOT raise
        view._on_theme_toggle(event)

        # The error should be logged
        mock_debugger.log_error.assert_called_once()
        args = mock_debugger.log_error.call_args
        assert args[0][0] == "on_theme_toggle"
        assert isinstance(args[0][1], RuntimeError)


# =============================================================================
# SECTION 3 : Offline toggle
# =============================================================================


class TestOfflineToggle:
    """Tests pour _on_offline_toggle."""

    def test_enable_offline(self, mock_page, mock_app_state, mock_debugger):
        """Verifie que _on_offline_toggle avec value=True appelle
        repo.set_setting('force_offline', 'true') et definit
        repo.connectivity.force_offline = True."""
        view = _make_view(mock_page, mock_app_state, mock_debugger)

        event = MagicMock()
        event.control.value = True

        view._on_offline_toggle(event)

        mock_app_state.repository.set_setting.assert_called_with(
            "force_offline", "true"
        )
        assert mock_app_state.repository.connectivity.force_offline is True

    def test_disable_offline(self, mock_page, mock_app_state, mock_debugger):
        """Verifie que value=False -> set_setting('force_offline', 'false')
        et connectivity.force_offline = False."""
        view = _make_view(mock_page, mock_app_state, mock_debugger)

        event = MagicMock()
        event.control.value = False

        view._on_offline_toggle(event)

        mock_app_state.repository.set_setting.assert_called_with(
            "force_offline", "false"
        )
        assert mock_app_state.repository.connectivity.force_offline is False


# =============================================================================
# SECTION 4 : Notifications
# =============================================================================


class TestNotificationsSettings:
    """Tests pour _on_notifications_toggle et _on_notification_time_change."""

    def test_enable_notifications(self, mock_page, mock_app_state, mock_debugger):
        """Verifie que _on_notifications_toggle avec value=True appelle
        repo.set_setting('notifications_enabled', 'true') et demarre
        le NotificationService."""
        view = _make_view(mock_page, mock_app_state, mock_debugger)

        # Add a notification_service to app_state
        notif_service = MagicMock()
        mock_app_state.notification_service = notif_service

        event = MagicMock()
        event.control.value = True

        view._on_notifications_toggle(event)

        mock_app_state.repository.set_setting.assert_called_with(
            "notifications_enabled", "true"
        )
        notif_service.start.assert_called_once()

    def test_disable_notifications(self, mock_page, mock_app_state, mock_debugger):
        """Verifie que value=False -> set_setting('notifications_enabled', 'false')
        et arrete le NotificationService."""
        view = _make_view(mock_page, mock_app_state, mock_debugger)

        notif_service = MagicMock()
        mock_app_state.notification_service = notif_service

        event = MagicMock()
        event.control.value = False

        view._on_notifications_toggle(event)

        mock_app_state.repository.set_setting.assert_called_with(
            "notifications_enabled", "false"
        )
        notif_service.stop.assert_called_once()

    def test_change_notification_time(self, mock_page, mock_app_state, mock_debugger):
        """Verifie que _on_notification_time_change avec e.control.value='09:00'
        appelle repo.set_setting('notification_time', '09:00')."""
        view = _make_view(mock_page, mock_app_state, mock_debugger)

        event = MagicMock()
        event.control.value = "09:00"

        view._on_notification_time_change(event)

        mock_app_state.repository.set_setting.assert_called_with(
            "notification_time", "09:00"
        )


# =============================================================================
# SECTION 5 : Cache management
# =============================================================================


class TestCacheManagement:
    """Tests pour _on_clear_cache."""

    @patch("daynimal.ui.views.settings_view.asyncio.create_task")
    def test_clear_cache(
        self, mock_create_task, mock_page, mock_app_state, mock_debugger
    ):
        """Verifie que _on_clear_cache appelle image_cache.clear()
        puis recharge les settings (appelle _load_settings) pour
        mettre a jour l'affichage de la taille du cache."""
        view = _make_view(mock_page, mock_app_state, mock_debugger)

        event = MagicMock()
        view._on_clear_cache(event)

        # image_cache.clear() should have been called
        mock_app_state.image_cache.clear.assert_called_once()
        # _load_settings should have been re-triggered via asyncio.create_task
        mock_create_task.assert_called_once()

    @pytest.mark.asyncio
    async def test_cache_size_format_kb(self, mock_page, mock_app_state, mock_debugger):
        """Verifie que quand get_cache_size retourne 512000 (500 Ko),
        le texte affiche '500.0 Ko'."""
        mock_app_state.image_cache.get_cache_size = MagicMock(return_value=512000)

        view = _make_view(mock_page, mock_app_state, mock_debugger)
        await view._load_settings()

        text_values = _find_text_values(view.settings_container)
        cache_texts = [t for t in text_values if "500.0 Ko" in t]
        assert len(cache_texts) >= 1

    @pytest.mark.asyncio
    async def test_cache_size_format_mb(self, mock_page, mock_app_state, mock_debugger):
        """Verifie que quand get_cache_size retourne 10485760 (10 Mo),
        le texte affiche '10.0 Mo'."""
        mock_app_state.image_cache.get_cache_size = MagicMock(return_value=10485760)

        view = _make_view(mock_page, mock_app_state, mock_debugger)
        await view._load_settings()

        text_values = _find_text_values(view.settings_container)
        cache_texts = [t for t in text_values if "10.0 Mo" in t]
        assert len(cache_texts) >= 1

    @pytest.mark.asyncio
    async def test_cache_size_zero(self, mock_page, mock_app_state, mock_debugger):
        """Verifie que quand get_cache_size retourne 0,
        le texte affiche '0.0 Ko' ou equivalent."""
        mock_app_state.image_cache.get_cache_size = MagicMock(return_value=0)

        view = _make_view(mock_page, mock_app_state, mock_debugger)
        await view._load_settings()

        text_values = _find_text_values(view.settings_container)
        cache_texts = [t for t in text_values if "0.0 Ko" in t]
        assert len(cache_texts) >= 1
