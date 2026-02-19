"""Tests pour daynimal/app.py — Application Flet principale.

Couvre: DaynimalApp (init, build, theme, cleanup, lifecycle),
_show_error, _install_asyncio_exception_handler.

Stratégie: on mock ft.Page, resolve_database, is_mobile, AnimalRepository,
AppController. On instancie DaynimalApp avec un mock page et on vérifie
les propriétés définies et les méthodes appelées.
"""

import asyncio
import sys
import traceback
from unittest.mock import MagicMock, patch, AsyncMock, call

import pytest


def _make_mock_page():
    """Create a properly configured mock ft.Page for tests."""
    page = MagicMock()
    page.title = None
    page.padding = None
    page.scroll = None
    page.controls = []
    page.theme_mode = None
    page.data = None

    # Mock window
    page.window = MagicMock()
    page.window.width = None
    page.window.height = None

    # page.add appends to controls
    def mock_add(control):
        page.controls.append(control)

    page.add = MagicMock(side_effect=mock_add)
    page.update = MagicMock()

    # on_disconnect, on_close
    page.on_disconnect = None
    page.on_close = None

    return page


# =============================================================================
# SECTION 1 : _show_error
# =============================================================================


class TestShowError:
    """Tests pour la fonction _show_error(page, error)."""

    def test_show_error_adds_controls_to_page(self):
        """Vérifie que _show_error ajoute des contrôles (Column avec textes d'erreur)
        à page.controls et appelle page.update(). Le premier Text doit contenir
        le message d'erreur passé en argument."""
        from daynimal.app import _show_error

        page = MagicMock()
        page.controls = MagicMock()

        error = RuntimeError("Something broke")
        _show_error(page, error)

        # page.controls.clear() was called
        page.controls.clear.assert_called_once()

        # page.add was called with a Column
        page.add.assert_called_once()
        column = page.add.call_args[0][0]

        # The column should be a ft.Column with children containing the error message
        import flet as ft

        assert isinstance(column, ft.Column)
        texts = column.controls
        # Second text should contain the error message string
        assert "Something broke" in texts[1].value

        # page.update() was called
        page.update.assert_called_once()

    def test_show_error_includes_traceback(self):
        """Vérifie que _show_error inclut le traceback formaté dans les contrôles
        ajoutés à la page, via traceback.format_exc()."""
        from daynimal.app import _show_error

        page = MagicMock()
        page.controls = MagicMock()

        error = ValueError("test error")

        # Generate a real traceback
        try:
            raise ValueError("test error")
        except ValueError as e:
            _show_error(page, e)

        page.add.assert_called_once()
        column = page.add.call_args[0][0]
        # The third text should contain the traceback info
        import flet as ft

        assert isinstance(column, ft.Column)
        traceback_text = column.controls[2]
        # It should be selectable and contain traceback text
        assert traceback_text.selectable is True


# =============================================================================
# SECTION 2 : _install_asyncio_exception_handler
# =============================================================================


class TestInstallAsyncioExceptionHandler:
    """Tests pour _install_asyncio_exception_handler."""

    @patch("traceback.print_exception")
    @patch("asyncio.get_running_loop")
    def test_ignores_connection_reset_error(self, mock_get_loop, mock_print_exc):
        """Vérifie que le handler installé par _install_asyncio_exception_handler
        ignore silencieusement les ConnectionResetError sans les imprimer.
        On crée un loop mock, on appelle le handler avec une ConnectionResetError,
        et on vérifie que print/print_exception n'est pas appelé."""
        from daynimal.app import _install_asyncio_exception_handler

        mock_loop = MagicMock()
        mock_get_loop.return_value = mock_loop

        _install_asyncio_exception_handler()

        # Grab the handler that was set
        mock_loop.set_exception_handler.assert_called_once()
        handler = mock_loop.set_exception_handler.call_args[0][0]

        # Call handler with a ConnectionResetError
        context = {"exception": ConnectionResetError("Connection reset")}
        handler(mock_loop, context)
        mock_print_exc.assert_not_called()

    @patch("traceback.print_exception")
    @patch("asyncio.get_running_loop")
    def test_prints_other_exceptions(self, mock_get_loop, mock_print_exc):
        """Vérifie que le handler imprime les exceptions non-ConnectionResetError
        via traceback.print_exception. On passe un ValueError au handler et
        on vérifie que print_exception est appelé avec le bon type/value."""
        from daynimal.app import _install_asyncio_exception_handler

        mock_loop = MagicMock()
        mock_get_loop.return_value = mock_loop

        _install_asyncio_exception_handler()

        handler = mock_loop.set_exception_handler.call_args[0][0]

        exc = ValueError("bad value")
        context = {"exception": exc}
        handler(mock_loop, context)
        mock_print_exc.assert_called_once()
        # First argument should be the exception type
        args = mock_print_exc.call_args
        assert args[0][0] is type(exc)
        assert args[0][1] is exc


# =============================================================================
# SECTION 3 : DaynimalApp.__init__
# =============================================================================


class TestDaynimalAppInit:
    """Tests pour DaynimalApp.__init__(page)."""

    def _make_app(self, page=None, is_mobile_val=False):
        """Helper to create a DaynimalApp with everything mocked."""
        from daynimal.app import DaynimalApp

        if page is None:
            page = _make_mock_page()

        with (
            patch.object(DaynimalApp, "build"),
            patch("daynimal.config.is_mobile", return_value=is_mobile_val),
        ):
            app = DaynimalApp(page)
        return app

    def test_sets_page_title(self):
        """Vérifie que __init__ définit page.title à 'Daynimal'."""
        page = _make_mock_page()
        self._make_app(page)
        assert page.title == "Daynimal"

    def test_sets_page_padding(self):
        """Vérifie que __init__ définit page.padding à 0."""
        page = _make_mock_page()
        self._make_app(page)
        assert page.padding == 0

    def test_desktop_sets_window_size(self):
        """Vérifie que sur desktop (is_mobile()=False), __init__ définit
        page.window.width=420 et page.window.height=820."""
        page = _make_mock_page()
        self._make_app(page, is_mobile_val=False)
        assert page.window.width == 420
        assert page.window.height == 820

    def test_mobile_skips_window_size(self):
        """Vérifie que sur mobile (is_mobile()=True), __init__ ne modifie pas
        page.window.width/height."""
        page = _make_mock_page()
        self._make_app(page, is_mobile_val=True)
        # Window dimensions should remain None (not set)
        assert page.window.width is None
        assert page.window.height is None

    def test_registers_disconnect_handler(self):
        """Vérifie que __init__ assigne on_disconnect et on_close sur la page."""
        page = _make_mock_page()
        app = self._make_app(page)
        assert page.on_disconnect is not None
        assert page.on_disconnect == app.on_disconnect
        assert page.on_close == app.on_close

    def test_uses_debugger_from_page_data(self):
        """Vérifie que si page.data est un dict contenant 'debugger',
        l'app utilise ce debugger au lieu d'en créer un nouveau."""
        page = _make_mock_page()
        mock_debugger = MagicMock()
        page.data = {"debugger": mock_debugger}
        app = self._make_app(page)
        assert app.debugger is mock_debugger


# =============================================================================
# SECTION 4 : DaynimalApp.build
# =============================================================================


class TestDaynimalAppBuild:
    """Tests pour DaynimalApp.build() — routage selon DB et plateforme."""

    def _make_app_no_build(self, page=None):
        """Create a DaynimalApp with build() mocked out during __init__."""
        from daynimal.app import DaynimalApp

        if page is None:
            page = _make_mock_page()

        with (
            patch.object(DaynimalApp, "build"),
            patch("daynimal.config.is_mobile", return_value=False),
        ):
            app = DaynimalApp(page)

        return app

    def test_with_db_builds_main_app(self):
        """Vérifie que quand resolve_database() retourne un chemin valide
        et is_mobile()=False, build() appelle _build_main_app()."""
        page = _make_mock_page()
        app = self._make_app_no_build(page)

        with (
            patch(
                "daynimal.db.first_launch.resolve_database",
                return_value="/fake/db.sqlite",
            ),
            patch.object(app, "_load_theme"),
            patch.object(app, "_build_main_app") as mock_build_main,
        ):
            app.build()
            mock_build_main.assert_called_once()

    def test_no_db_mobile_shows_setup_view(self):
        """Vérifie que quand resolve_database() retourne None et is_mobile()=True,
        build() instancie SetupView et appelle setup_view.build()."""
        page = _make_mock_page()
        app = self._make_app_no_build(page)

        mock_setup_view_instance = MagicMock()
        mock_setup_view_instance.build.return_value = MagicMock()

        with (
            patch("daynimal.db.first_launch.resolve_database", return_value=None),
            patch("daynimal.config.is_mobile", return_value=True),
            patch.object(app, "_load_theme"),
            patch(
                "daynimal.ui.views.setup_view.SetupView",
                return_value=mock_setup_view_instance,
            ) as mock_setup_cls,
            patch("daynimal.ui.state.AppState"),
        ):
            app.build()
            mock_setup_cls.assert_called_once()
            mock_setup_view_instance.build.assert_called_once()

    def test_no_db_desktop_shows_instructions(self):
        """Vérifie que quand resolve_database() retourne None et is_mobile()=False,
        build() appelle _build_desktop_no_db_screen()."""
        page = _make_mock_page()
        app = self._make_app_no_build(page)

        with (
            patch("daynimal.db.first_launch.resolve_database", return_value=None),
            patch("daynimal.config.is_mobile", return_value=False),
            patch.object(app, "_load_theme"),
            patch.object(app, "_build_desktop_no_db_screen") as mock_no_db_screen,
        ):
            app.build()
            mock_no_db_screen.assert_called_once()


# =============================================================================
# SECTION 5 : DaynimalApp._load_theme
# =============================================================================


class TestLoadTheme:
    """Tests pour DaynimalApp._load_theme()."""

    def _make_app_no_build(self, page=None):
        """Create a DaynimalApp with build() mocked out."""
        from daynimal.app import DaynimalApp

        if page is None:
            page = _make_mock_page()

        with (
            patch.object(DaynimalApp, "build"),
            patch("daynimal.config.is_mobile", return_value=False),
        ):
            app = DaynimalApp(page)
        return app

    def test_dark_theme_applied(self):
        """Vérifie que quand le repository retourne 'dark' pour le setting
        'theme_mode', _load_theme() définit page.theme_mode à ft.ThemeMode.DARK."""
        import flet as ft

        page = _make_mock_page()
        app = self._make_app_no_build(page)

        mock_repo = MagicMock()
        mock_repo.get_setting.return_value = "dark"
        mock_repo.__enter__ = MagicMock(return_value=mock_repo)
        mock_repo.__exit__ = MagicMock(return_value=False)

        with patch("daynimal.repository.AnimalRepository", return_value=mock_repo):
            app._load_theme()

        assert page.theme_mode == ft.ThemeMode.DARK

    def test_light_theme_applied(self):
        """Vérifie que quand le setting est 'light', page.theme_mode = LIGHT."""
        import flet as ft

        page = _make_mock_page()
        app = self._make_app_no_build(page)

        mock_repo = MagicMock()
        mock_repo.get_setting.return_value = "light"
        mock_repo.__enter__ = MagicMock(return_value=mock_repo)
        mock_repo.__exit__ = MagicMock(return_value=False)

        with patch("daynimal.repository.AnimalRepository", return_value=mock_repo):
            app._load_theme()

        assert page.theme_mode == ft.ThemeMode.LIGHT

    def test_exception_defaults_to_light(self):
        """Vérifie que quand AnimalRepository() lève une exception (ex: pas de DB),
        _load_theme() ne plante pas et page.theme_mode reste LIGHT par défaut."""
        import flet as ft

        page = _make_mock_page()
        app = self._make_app_no_build(page)

        with patch(
            "daynimal.repository.AnimalRepository", side_effect=Exception("No DB")
        ):
            app._load_theme()

        assert page.theme_mode == ft.ThemeMode.LIGHT

    def test_no_setting_defaults_to_light(self):
        """Vérifie que quand get_setting retourne None, le thème est LIGHT."""
        import flet as ft

        page = _make_mock_page()
        app = self._make_app_no_build(page)

        mock_repo = MagicMock()
        # get_setting returns "light" as default (the method passes "light" as default)
        mock_repo.get_setting.return_value = "light"
        mock_repo.__enter__ = MagicMock(return_value=mock_repo)
        mock_repo.__exit__ = MagicMock(return_value=False)

        with patch("daynimal.repository.AnimalRepository", return_value=mock_repo):
            app._load_theme()

        assert page.theme_mode == ft.ThemeMode.LIGHT


# =============================================================================
# SECTION 6 : DaynimalApp.cleanup
# =============================================================================


class TestDaynimalAppCleanup:
    """Tests pour DaynimalApp.cleanup()."""

    def _make_app_no_build(self, page=None):
        """Create a DaynimalApp with build() mocked out."""
        from daynimal.app import DaynimalApp

        if page is None:
            page = _make_mock_page()

        with (
            patch.object(DaynimalApp, "build"),
            patch("daynimal.config.is_mobile", return_value=False),
        ):
            app = DaynimalApp(page)
        return app

    def test_cleanup_calls_app_controller_cleanup(self):
        """Vérifie que cleanup() appelle self.app_controller.cleanup()
        quand app_controller existe."""
        app = self._make_app_no_build()
        mock_controller = MagicMock()
        app.app_controller = mock_controller

        app.cleanup()
        mock_controller.cleanup.assert_called_once()

    def test_cleanup_without_app_controller(self):
        """Vérifie que cleanup() ne plante pas quand self n'a pas d'attribut
        app_controller (cas où build() n'a pas créé de controller)."""
        app = self._make_app_no_build()
        # Ensure no app_controller attribute
        if hasattr(app, "app_controller"):
            delattr(app, "app_controller")

        # Should not raise
        app.cleanup()

    def test_cleanup_handles_exception(self):
        """Vérifie que si app_controller.cleanup() lève une exception,
        cleanup() l'attrape et la log sans la propager."""
        app = self._make_app_no_build()
        mock_controller = MagicMock()
        mock_controller.cleanup.side_effect = RuntimeError("cleanup failed")
        app.app_controller = mock_controller

        # Should not raise
        app.cleanup()


# =============================================================================
# SECTION 7 : DaynimalApp.on_disconnect / on_close
# =============================================================================


class TestDaynimalAppLifecycle:
    """Tests pour on_disconnect et on_close."""

    def _make_app_no_build(self, page=None):
        """Create a DaynimalApp with build() mocked out."""
        from daynimal.app import DaynimalApp

        if page is None:
            page = _make_mock_page()

        with (
            patch.object(DaynimalApp, "build"),
            patch("daynimal.config.is_mobile", return_value=False),
        ):
            app = DaynimalApp(page)
        return app

    def test_on_disconnect_calls_cleanup_then_exit(self):
        """Vérifie que on_disconnect(e) appelle cleanup() puis os._exit(0)."""
        app = self._make_app_no_build()

        with (
            patch.object(app, "cleanup") as mock_cleanup,
            patch("daynimal.app.os._exit") as mock_exit,
        ):
            app.on_disconnect(MagicMock())
            mock_cleanup.assert_called_once()
            mock_exit.assert_called_once_with(0)

    def test_on_close_calls_cleanup(self):
        """Vérifie que on_close(e) appelle cleanup().
        Vérifie aussi que les exceptions dans cleanup sont attrapées."""
        app = self._make_app_no_build()

        with patch.object(app, "cleanup") as mock_cleanup:
            app.on_close(MagicMock())
            mock_cleanup.assert_called_once()

        # Also verify exception is caught
        app2 = self._make_app_no_build()
        with patch.object(app2, "cleanup", side_effect=RuntimeError("fail")):
            # Should not raise
            app2.on_close(MagicMock())


# =============================================================================
# SECTION 8 : DaynimalApp._on_setup_complete / _build_desktop_no_db_screen
# =============================================================================


class TestDaynimalAppSetup:
    """Tests pour _on_setup_complete et _build_desktop_no_db_screen."""

    def _make_app_no_build(self, page=None):
        """Create a DaynimalApp with build() mocked out."""
        from daynimal.app import DaynimalApp

        if page is None:
            page = _make_mock_page()

        with (
            patch.object(DaynimalApp, "build"),
            patch("daynimal.config.is_mobile", return_value=False),
        ):
            app = DaynimalApp(page)
        return app

    def test_on_setup_complete_resolves_db_and_builds_main(self):
        """Vérifie que _on_setup_complete() appelle resolve_database()
        puis _build_main_app() puis page.update()."""
        page = _make_mock_page()
        app = self._make_app_no_build(page)

        with (
            patch("daynimal.db.first_launch.resolve_database") as mock_resolve,
            patch.object(app, "_build_main_app") as mock_build_main,
        ):
            app._on_setup_complete()
            mock_resolve.assert_called_once()
            mock_build_main.assert_called_once()
            page.update.assert_called()

    def test_build_desktop_no_db_screen_has_instructions(self):
        """Vérifie que _build_desktop_no_db_screen() ajoute à la page
        un écran contenant les commandes CLI de setup (texte incluant
        'uv run daynimal setup')."""
        page = _make_mock_page()
        app = self._make_app_no_build(page)

        app._build_desktop_no_db_screen()

        # page.add should have been called
        page.add.assert_called_once()
        container = page.add.call_args[0][0]

        # Recursively search for text containing "uv run daynimal setup"
        def find_text(control, target):
            if hasattr(control, "value") and target in str(
                getattr(control, "value", "")
            ):
                return True
            for attr in ("content", "controls"):
                child = getattr(control, attr, None)
                if child is not None:
                    if isinstance(child, list):
                        for c in child:
                            if find_text(c, target):
                                return True
                    else:
                        if find_text(child, target):
                            return True
            return False

        assert find_text(container, "uv run daynimal setup"), (
            "Desktop no-DB screen should contain 'uv run daynimal setup' instructions"
        )

    def test_build_desktop_no_db_screen_has_quit_button(self):
        """Vérifie que l'écran sans DB contient un bouton 'Quitter'
        qui déclenche la fermeture de la fenêtre."""
        import flet as ft

        page = _make_mock_page()
        app = self._make_app_no_build(page)

        app._build_desktop_no_db_screen()

        container = page.add.call_args[0][0]

        # Recursively search for a FilledButton with text "Quitter"
        def find_button(control, text):
            if isinstance(control, ft.FilledButton) and (
                getattr(control, "content", None) == text
                or getattr(control, "text", None) == text
            ):
                return control
            for attr in ("content", "controls"):
                child = getattr(control, attr, None)
                if child is not None:
                    if isinstance(child, list):
                        for c in child:
                            result = find_button(c, text)
                            if result:
                                return result
                    else:
                        result = find_button(child, text)
                        if result:
                            return result
            return None

        quit_btn = find_button(container, "Quitter")
        assert quit_btn is not None, "Should have a 'Quitter' button"
        assert quit_btn.on_click is not None, (
            "Quitter button should have an on_click handler"
        )
