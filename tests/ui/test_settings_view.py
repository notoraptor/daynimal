"""Tests pour daynimal/ui/views/settings_view.py -- Vue Parametres.

Couvre: SettingsView (build, _load_settings, _on_theme_toggle,
_on_offline_toggle, _open_notification_dialog, _on_notif_dialog_save,
_on_notif_dialog_cancel, _on_clear_cache).

Strategie: on mock AppState (repository + image_cache), NotificationService
et ft.Page. On simule les evenements des controles (Switch.on_change,
Button.on_click) et on verifie les appels au repository
et les changements d'UI.
"""

from unittest.mock import MagicMock, call, patch, PropertyMock

import flet as ft
import pytest

from daynimal.ui.views.settings_view import _format_notification_summary


# =============================================================================
# Helpers
# =============================================================================


def _make_view(mock_page, mock_app_state):
    """Create a SettingsView instance with mocked dependencies."""
    from daynimal.ui.views.settings_view import SettingsView

    # Patch asyncio.create_task to avoid actually running async tasks in build()
    with patch("daynimal.ui.views.settings_view.asyncio.create_task"):
        view = SettingsView(mock_page, mock_app_state)
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

    # Check .actions (AlertDialog)
    if hasattr(control, "actions") and control.actions:
        for child in control.actions:
            _find_controls_of_type(child, control_type, results)

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
    page.show_dialog = MagicMock()
    page.pop_dialog = MagicMock()
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
            "auto_load_on_start": "true",
            "notifications_enabled": "false",
            "notification_start": "2026-02-21T08:00",
            "notification_period": "24:00",
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


# =============================================================================
# SECTION 1 : SettingsView.build / _load_settings
# =============================================================================


class TestSettingsViewBuild:
    """Tests pour build() et _load_settings()."""

    @patch("daynimal.ui.views.settings_view.asyncio.create_task")
    def test_build_triggers_load_settings(
        self, mock_create_task, mock_page, mock_app_state
    ):
        """Verifie que build() retourne settings_container et lance
        _load_settings() en tache async."""
        from daynimal.ui.views.settings_view import SettingsView

        view = SettingsView(mock_page, mock_app_state)
        result = view.build()

        # build() should return the settings_container
        assert result is view.settings_container
        # asyncio.create_task should have been called to launch _load_settings
        assert mock_create_task.called

    @pytest.mark.asyncio
    async def test_load_settings_creates_theme_toggle(self, mock_page, mock_app_state):
        """Verifie que _load_settings cree un ft.Switch pour le theme sombre."""
        view = _make_view(mock_page, mock_app_state)

        await view._load_settings()

        switches = _find_controls_of_type(view.settings_container, ft.Switch)
        theme_switches = [
            s for s in switches if s.label and "sombre" in s.label.lower()
        ]
        assert len(theme_switches) == 1
        assert theme_switches[0].value is False

    @pytest.mark.asyncio
    async def test_load_settings_creates_theme_toggle_dark(
        self, mock_page, mock_app_state
    ):
        """Verifie que quand theme_mode='dark', le Switch theme est True."""
        repo = mock_app_state.repository

        def get_setting_dark(key, default=None):
            if key == "theme_mode":
                return "dark"
            settings_map = {
                "force_offline": "false",
                "notifications_enabled": "false",
                "notification_start": "2026-02-21T08:00",
                "notification_period": "24:00",
            }
            return settings_map.get(key, default)

        repo.get_setting = MagicMock(side_effect=get_setting_dark)

        view = _make_view(mock_page, mock_app_state)
        await view._load_settings()

        switches = _find_controls_of_type(view.settings_container, ft.Switch)
        theme_switches = [
            s for s in switches if s.label and "sombre" in s.label.lower()
        ]
        assert len(theme_switches) == 1
        assert theme_switches[0].value is True

    @pytest.mark.asyncio
    async def test_load_settings_creates_offline_toggle(
        self, mock_page, mock_app_state
    ):
        """Verifie que _load_settings cree un ft.Switch pour le mode hors ligne."""
        view = _make_view(mock_page, mock_app_state)

        await view._load_settings()

        switches = _find_controls_of_type(view.settings_container, ft.Switch)
        offline_switches = [
            s for s in switches if s.label and "hors ligne" in s.label.lower()
        ]
        assert len(offline_switches) == 1
        assert offline_switches[0].value is False

    @pytest.mark.asyncio
    async def test_load_settings_creates_notification_controls(
        self, mock_page, mock_app_state
    ):
        """Verifie que _load_settings cree: ft.Text resume 'Desactivees'
        + ft.Button 'Modifier'."""
        view = _make_view(mock_page, mock_app_state)

        await view._load_settings()

        # Summary text should say "Désactivées" (notifications disabled by default)
        text_values = _find_text_values(view.settings_container)
        assert any("Désactivées" in t for t in text_values)

        # "Modifier" button should exist
        buttons = _find_controls_of_type(view.settings_container, ft.Button)
        modifier_buttons = [
            b
            for b in buttons
            if hasattr(b, "content")
            and isinstance(b.content, str)
            and "Modifier" in b.content
        ]
        assert len(modifier_buttons) == 1

    @pytest.mark.asyncio
    async def test_notification_summary_enabled(self, mock_page, mock_app_state):
        """Verifie que le resume affiche les details quand notifications activees."""
        repo = mock_app_state.repository

        def get_setting_notif_on(key, default=None):
            settings_map = {
                "theme_mode": "light",
                "force_offline": "false",
                "notifications_enabled": "true",
                "notification_start": "2026-02-21T08:00",
                "notification_period": "24:00",
            }
            return settings_map.get(key, default)

        repo.get_setting = MagicMock(side_effect=get_setting_notif_on)

        view = _make_view(mock_page, mock_app_state)
        await view._load_settings()

        text_values = _find_text_values(view.settings_container)
        summary_texts = [t for t in text_values if "Activées" in t]
        assert len(summary_texts) == 1
        assert "24h" in summary_texts[0]
        assert "21/02/2026" in summary_texts[0]
        assert "08:00" in summary_texts[0]

    @pytest.mark.asyncio
    async def test_load_settings_shows_cache_size(self, mock_page, mock_app_state):
        """Verifie que _load_settings affiche la taille du cache d'images."""
        view = _make_view(mock_page, mock_app_state)

        await view._load_settings()

        text_values = _find_text_values(view.settings_container)
        cache_texts = [t for t in text_values if "5.0 Mo" in t]
        assert len(cache_texts) >= 1

    @pytest.mark.asyncio
    async def test_load_settings_shows_db_stats(self, mock_page, mock_app_state):
        """Verifie que _load_settings affiche les statistiques de la DB."""
        view = _make_view(mock_page, mock_app_state)

        await view._load_settings()

        text_values = _find_text_values(view.settings_container)
        all_text = " ".join(text_values)
        assert "1 500 000" in all_text
        assert "3 200 000" in all_text
        assert "500" in all_text

    @pytest.mark.asyncio
    async def test_load_settings_error_shows_error(self, mock_page, mock_app_state):
        """Verifie qu'une exception affiche un container d'erreur."""
        mock_app_state.repository.get_setting = MagicMock(
            side_effect=RuntimeError("DB connection failed")
        )

        view = _make_view(mock_page, mock_app_state)

        await view._load_settings()

        text_values = _find_text_values(view.settings_container)
        error_texts = [
            t for t in text_values if "Erreur" in t or "DB connection failed" in t
        ]
        assert len(error_texts) >= 1


# =============================================================================
# SECTION 2 : Theme toggle
# =============================================================================


class TestThemeToggle:
    """Tests pour _on_theme_toggle."""

    def test_toggle_to_dark(self, mock_page, mock_app_state):
        view = _make_view(mock_page, mock_app_state)
        event = MagicMock()
        event.control.value = True
        view._on_theme_toggle(event)
        mock_app_state.repository.set_setting.assert_called_with("theme_mode", "dark")
        assert mock_page.theme_mode == ft.ThemeMode.DARK

    def test_toggle_to_light(self, mock_page, mock_app_state):
        view = _make_view(mock_page, mock_app_state)
        event = MagicMock()
        event.control.value = False
        view._on_theme_toggle(event)
        mock_app_state.repository.set_setting.assert_called_with("theme_mode", "light")
        assert mock_page.theme_mode == ft.ThemeMode.LIGHT

    def test_calls_page_update(self, mock_page, mock_app_state):
        view = _make_view(mock_page, mock_app_state)
        event = MagicMock()
        event.control.value = True
        view._on_theme_toggle(event)
        mock_page.update.assert_called()

    def test_error_handled(self, mock_page, mock_app_state):
        view = _make_view(mock_page, mock_app_state)
        mock_app_state.repository.set_setting = MagicMock(
            side_effect=RuntimeError("DB write error")
        )
        event = MagicMock()
        event.control.value = True
        view._on_theme_toggle(event)  # Should NOT raise


# =============================================================================
# SECTION 3 : Offline toggle
# =============================================================================


class TestOfflineToggle:
    """Tests pour _on_offline_toggle."""

    def test_enable_offline(self, mock_page, mock_app_state):
        view = _make_view(mock_page, mock_app_state)
        event = MagicMock()
        event.control.value = True
        view._on_offline_toggle(event)
        mock_app_state.repository.set_setting.assert_called_with(
            "force_offline", "true"
        )
        assert mock_app_state.repository.connectivity.force_offline is True

    def test_disable_offline(self, mock_page, mock_app_state):
        view = _make_view(mock_page, mock_app_state)
        event = MagicMock()
        event.control.value = False
        view._on_offline_toggle(event)
        mock_app_state.repository.set_setting.assert_called_with(
            "force_offline", "false"
        )
        assert mock_app_state.repository.connectivity.force_offline is False


# =============================================================================
# SECTION 4 : Notifications dialog
# =============================================================================


class TestNotificationsDialog:
    """Tests pour _open_notification_dialog, _on_notif_dialog_save,
    _on_notif_dialog_cancel."""

    def test_open_notification_dialog(self, mock_page, mock_app_state):
        """Verifie que _open_notification_dialog ouvre un AlertDialog
        via page.show_dialog."""
        view = _make_view(mock_page, mock_app_state)

        event = MagicMock()
        view._open_notification_dialog(event)

        mock_page.show_dialog.assert_called_once()
        dialog_arg = mock_page.show_dialog.call_args[0][0]
        assert isinstance(dialog_arg, ft.AlertDialog)

        # Dialog should contain a Switch, dropdowns, and text fields
        switches = _find_controls_of_type(dialog_arg, ft.Switch)
        assert len(switches) == 1

        dropdowns = _find_controls_of_type(dialog_arg, ft.Dropdown)
        assert len(dropdowns) == 2

        text_fields = _find_controls_of_type(dialog_arg, ft.TextField)
        assert len(text_fields) == 2

        # Actions: Annuler + Sauvegarder
        assert len(dialog_arg.actions) == 2

    @patch("daynimal.ui.views.settings_view.asyncio.create_task")
    def test_notification_dialog_save(
        self, mock_create_task, mock_page, mock_app_state
    ):
        """Verifie que sauvegarder ecrit les 3 settings + start + pop_dialog."""
        view = _make_view(mock_page, mock_app_state)

        # Set up notification service mock
        notif_service = MagicMock()
        mock_app_state.notification_service = notif_service

        # Open dialog first to create _dlg_* controls
        event = MagicMock()
        view._open_notification_dialog(event)

        # Modify dialog values
        view._dlg_enabled_switch.value = True
        view._dlg_hour_dropdown.value = "09"
        view._dlg_minute_dropdown.value = "30"
        view._dlg_period_hours_field.value = "1"
        view._dlg_period_minutes_field.value = "30"

        # Save
        mock_app_state.repository.set_setting.reset_mock()
        view._on_notif_dialog_save(event)

        # Verify all 3 settings were saved
        set_calls = mock_app_state.repository.set_setting.call_args_list
        assert call("notifications_enabled", "true") in set_calls
        assert call("notification_start", "2026-02-21T09:30") in set_calls
        assert call("notification_period", "1:30") in set_calls

        # Verify service was started (since enabled=True)
        notif_service.start.assert_called_once()

        # Verify dialog was closed
        mock_page.pop_dialog.assert_called_once()

        # Verify _load_settings was triggered
        mock_create_task.assert_called_once()

    def test_notification_dialog_cancel(self, mock_page, mock_app_state):
        """Verifie que annuler ferme le dialog sans sauvegarder."""
        view = _make_view(mock_page, mock_app_state)

        # Reset set_setting mock to track calls
        mock_app_state.repository.set_setting.reset_mock()

        event = MagicMock()
        view._on_notif_dialog_cancel(event)

        # No settings should be saved
        mock_app_state.repository.set_setting.assert_not_called()

        # Dialog should be closed
        mock_page.pop_dialog.assert_called_once()

    @patch("daynimal.ui.views.settings_view.asyncio.create_task")
    def test_notification_dialog_save_disabled(
        self, mock_create_task, mock_page, mock_app_state
    ):
        """Verifie que sauvegarder avec notifications desactivees appelle stop."""
        view = _make_view(mock_page, mock_app_state)

        notif_service = MagicMock()
        mock_app_state.notification_service = notif_service

        event = MagicMock()
        view._open_notification_dialog(event)

        # Keep notifications disabled (default)
        view._dlg_enabled_switch.value = False

        mock_app_state.repository.set_setting.reset_mock()
        view._on_notif_dialog_save(event)

        notif_service.stop.assert_called_once()
        notif_service.start.assert_not_called()


# =============================================================================
# SECTION 5 : _format_notification_summary
# =============================================================================


class TestFormatNotificationSummary:
    """Tests pour _format_notification_summary."""

    def test_disabled(self):
        from datetime import datetime

        start = datetime(2026, 2, 21, 8, 0)
        assert _format_notification_summary(False, start, 24, 0) == "Désactivées"

    def test_24h_period(self):
        from datetime import datetime

        start = datetime(2026, 2, 21, 8, 0)
        result = _format_notification_summary(True, start, 24, 0)
        assert result == "Activées — toutes les 24h depuis le 21/02/2026 à 08:00"

    def test_minutes_only(self):
        from datetime import datetime

        start = datetime(2026, 2, 21, 17, 50)
        result = _format_notification_summary(True, start, 0, 5)
        assert result == "Activées — toutes les 5min depuis le 21/02/2026 à 17:50"

    def test_hours_and_minutes(self):
        from datetime import datetime

        start = datetime(2026, 2, 21, 8, 0)
        result = _format_notification_summary(True, start, 1, 30)
        assert result == "Activées — toutes les 1h 30min depuis le 21/02/2026 à 08:00"


# =============================================================================
# SECTION 6 : Cache management
# =============================================================================


class TestCacheManagement:
    """Tests pour _on_clear_cache."""

    @patch("daynimal.ui.views.settings_view.asyncio.create_task")
    def test_clear_cache(self, mock_create_task, mock_page, mock_app_state):
        view = _make_view(mock_page, mock_app_state)
        event = MagicMock()
        view._on_clear_cache(event)
        mock_app_state.image_cache.clear.assert_called_once()
        mock_create_task.assert_called_once()

    @pytest.mark.asyncio
    async def test_cache_size_format_kb(self, mock_page, mock_app_state):
        mock_app_state.image_cache.get_cache_size = MagicMock(return_value=512000)
        view = _make_view(mock_page, mock_app_state)
        await view._load_settings()
        text_values = _find_text_values(view.settings_container)
        cache_texts = [t for t in text_values if "500.0 Ko" in t]
        assert len(cache_texts) >= 1

    @pytest.mark.asyncio
    async def test_cache_size_format_mb(self, mock_page, mock_app_state):
        mock_app_state.image_cache.get_cache_size = MagicMock(return_value=10485760)
        view = _make_view(mock_page, mock_app_state)
        await view._load_settings()
        text_values = _find_text_values(view.settings_container)
        cache_texts = [t for t in text_values if "10.0 Mo" in t]
        assert len(cache_texts) >= 1

    @pytest.mark.asyncio
    async def test_cache_size_zero(self, mock_page, mock_app_state):
        mock_app_state.image_cache.get_cache_size = MagicMock(return_value=0)
        view = _make_view(mock_page, mock_app_state)
        await view._load_settings()
        text_values = _find_text_values(view.settings_container)
        cache_texts = [t for t in text_values if "0.0 Ko" in t]
        assert len(cache_texts) >= 1


# =============================================================================
# SECTION 7 : Auto-load toggle
# =============================================================================


class TestAutoLoadToggle:
    """Tests pour _on_auto_load_toggle."""

    def test_enable_auto_load(self, mock_page, mock_app_state):
        view = _make_view(mock_page, mock_app_state)
        event = MagicMock()
        event.control.value = True
        view._on_auto_load_toggle(event)
        mock_app_state.repository.set_setting.assert_called_with(
            "auto_load_on_start", "true"
        )

    def test_disable_auto_load(self, mock_page, mock_app_state):
        view = _make_view(mock_page, mock_app_state)
        event = MagicMock()
        event.control.value = False
        view._on_auto_load_toggle(event)
        mock_app_state.repository.set_setting.assert_called_with(
            "auto_load_on_start", "false"
        )

    @pytest.mark.asyncio
    async def test_auto_load_switch_in_settings(self, mock_page, mock_app_state):
        """Vérifie que _load_settings crée un ft.Switch pour le chargement auto."""
        view = _make_view(mock_page, mock_app_state)
        await view._load_settings()

        switches = _find_controls_of_type(view.settings_container, ft.Switch)
        auto_switches = [
            s for s in switches if s.label and "démarrage" in s.label.lower()
        ]
        assert len(auto_switches) == 1
        # Default is true (auto_load_on_start not in settings_map → default "true")
        assert auto_switches[0].value is True
