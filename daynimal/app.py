"""
Daynimal Flet App - Desktop/Mobile Application

A cross-platform application built with Flet (Flutter for Python) that displays
daily animal discoveries with enriched information.
"""

import os
import sys
import types

# On Android/mobile, Flet copies package contents to an "app" directory.
# Absolute imports like "from daynimal.xxx" fail because there's no "daynimal"
# package on sys.path. Fix: register current directory as the "daynimal" package.
if "daynimal" not in sys.modules:
    _app_dir = os.path.dirname(os.path.abspath(__file__))
    _pkg = types.ModuleType("daynimal")
    _pkg.__path__ = [_app_dir]
    _pkg.__package__ = "daynimal"
    _pkg.__file__ = os.path.join(_app_dir, "__init__.py")
    sys.modules["daynimal"] = _pkg

import asyncio
import logging
import traceback

import flet as ft

logger = logging.getLogger("daynimal")


class DaynimalApp:
    """Main application class for Daynimal Flet app."""

    def __init__(self, page: ft.Page):
        self.page = page
        self.page.title = "Daynimal"
        self.page.padding = 0
        self.page.scroll = None

        # Portrait window on desktop (simulates mobile aspect ratio)
        from daynimal.config import is_mobile

        if not is_mobile():
            self.page.window.width = 420
            self.page.window.height = 820

        logger.info("DaynimalApp initialized")

        # Register cleanup handlers
        self.page.on_disconnect = self.on_disconnect
        if hasattr(self.page, "on_close"):
            self.page.on_close = self.on_close

        # Build UI
        self.build()

    def build(self):
        """Build the user interface."""
        from daynimal.db.first_launch import resolve_database

        # Load and apply theme from settings
        self._load_theme()

        # Check if database exists
        db_path = resolve_database()
        if db_path is None:
            from daynimal.config import is_mobile

            if is_mobile():
                # Mobile: show first-launch setup screen
                from daynimal.ui.state import AppState
                from daynimal.ui.views.setup_view import SetupView

                self.setup_view = SetupView(
                    page=self.page,
                    app_state=AppState(),
                    on_setup_complete=self._on_setup_complete,
                )
                self.page.add(self.setup_view.build())
            else:
                # Desktop: show instructions to run CLI setup
                self._build_desktop_no_db_screen()
        else:
            self._build_main_app()

        self.page.update()

    def _build_desktop_no_db_screen(self):
        """Show an informational screen when DB is missing on desktop."""
        self.page.add(
            ft.Container(
                content=ft.Column(
                    [
                        ft.Icon(ft.Icons.INFO, size=64, color=ft.Colors.BLUE_400),
                        ft.Text(
                            "Base de données introuvable",
                            size=24,
                            weight=ft.FontWeight.BOLD,
                            text_align=ft.TextAlign.CENTER,
                        ),
                        ft.Text(
                            "L'application a besoin d'une base de données pour fonctionner.\n"
                            "Veuillez lancer le setup depuis le terminal :",
                            size=14,
                            text_align=ft.TextAlign.CENTER,
                            color=ft.Colors.GREY_500,
                        ),
                        ft.Container(
                            content=ft.Text(
                                "uv run daynimal setup",
                                size=16,
                                weight=ft.FontWeight.W_500,
                                font_family="Courier New",
                                text_align=ft.TextAlign.CENTER,
                            ),
                            bgcolor=ft.Colors.GREY_200,
                            border_radius=8,
                            padding=ft.Padding.symmetric(horizontal=20, vertical=12),
                            margin=ft.Margin.symmetric(vertical=10),
                        ),
                        ft.Text(
                            "Cette commande construit la base complète (~1 GB) depuis GBIF + TAXREF.\n"
                            "Pour une installation rapide (~117 MB) :",
                            size=12,
                            text_align=ft.TextAlign.CENTER,
                            color=ft.Colors.GREY_500,
                        ),
                        ft.Container(
                            content=ft.Text(
                                "uv run daynimal setup --mode minimal",
                                size=14,
                                font_family="Courier New",
                                text_align=ft.TextAlign.CENTER,
                            ),
                            bgcolor=ft.Colors.GREY_200,
                            border_radius=8,
                            padding=ft.Padding.symmetric(horizontal=16, vertical=8),
                        ),
                        ft.Container(height=20),
                        ft.FilledButton(
                            "Quitter", icon=ft.Icons.CLOSE, on_click=self._on_quit_click
                        ),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=10,
                ),
                expand=True,
                alignment=ft.Alignment.CENTER,
                padding=40,
            )
        )

    async def _on_quit_click(self, _):
        """Handle quit button click."""
        await self.page.window.close()

    def _build_main_app(self):
        """Build the main application UI (after DB is available)."""
        from daynimal.ui.app_controller import AppController

        self.page.controls.clear()
        self.app_controller = AppController(page=self.page)
        self.page.add(self.app_controller.build())

    def _on_setup_complete(self):
        """Called when first-launch setup finishes successfully."""
        from daynimal.db.first_launch import resolve_database

        resolve_database()  # Update settings with new DB path
        self._build_main_app()
        self.page.update()

    def _load_theme(self):
        """Load theme setting from database and apply to page."""
        try:
            from daynimal.repository import AnimalRepository

            with AnimalRepository() as repo:
                theme_mode = repo.get_setting("theme_mode", "light")
                self.page.theme_mode = (
                    ft.ThemeMode.DARK if theme_mode == "dark" else ft.ThemeMode.LIGHT
                )
        except Exception:
            # Default to light theme if error
            self.page.theme_mode = ft.ThemeMode.LIGHT

    def cleanup(self):
        """
        Clean up resources (close connections, database, etc.).

        This is called when the app is closing to properly release resources.
        """
        logger.info("Cleaning up application resources...")

        if hasattr(self, "app_controller"):
            try:
                self.app_controller.cleanup()
                logger.info("AppController cleaned up successfully")
            except Exception:
                logger.error("Error cleaning up AppController")
                traceback.print_exc()

        logger.info("Cleanup completed")

    def on_disconnect(self, e):
        """Handle page disconnect event (when user closes the window)."""
        logger.info("Page disconnected, cleaning up...")
        try:
            self.cleanup()
        except Exception:
            logger.error("Error during disconnect cleanup")
            traceback.print_exc()

        # Force exit: on Windows the asyncio proactor event loop hangs
        # after the Flutter client disconnects (ConnectionResetError).
        os._exit(0)

    def on_close(self, e):
        """Handle page close event."""
        logger.info("Page closed, cleaning up...")
        try:
            self.cleanup()
        except Exception:
            logger.error("Error during close cleanup")
            traceback.print_exc()


def main():
    """Main entry point for the Flet app."""

    def app_main(page: ft.Page):
        _install_asyncio_exception_handler()
        try:
            DaynimalApp(page)
        except Exception as e:
            _show_error(page, e)

    ft.run(main=app_main)


def _install_asyncio_exception_handler():
    """Print all unhandled async exceptions to the terminal.

    Flet catches exceptions from event handlers and shows them in the UI,
    but doesn't print them to the terminal. This installs a handler that
    also prints them to stderr so they can be read/copied from the CLI.
    """
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        return


    loop.set_exception_handler(_asyncio_exception_handler)


def _asyncio_exception_handler(loop, context):
    exc = context.get("exception")
    if exc:
        # ConnectionResetError is expected on Windows when the Flet
        # window closes (Flutter disconnects before Python finishes).
        if isinstance(exc, ConnectionResetError):
            return
        print("\n--- Unhandled Flet exception ---", file=sys.stderr, flush=True)
        traceback.print_exception(
            type(exc), exc, exc.__traceback__, file=sys.stderr
        )
        print("--------------------------------\n", file=sys.stderr, flush=True)


def _show_error(page: ft.Page, error: Exception):
    """Show error visually on the page (critical for mobile debugging)."""
    import traceback

    page.controls.clear()
    page.add(
        ft.Column(
            [
                ft.Text("Startup Error", size=24, color=ft.Colors.ERROR),
                ft.Text(str(error), size=14),
                ft.Text(traceback.format_exc(), size=10, selectable=True),
            ],
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )
    )
    page.update()


if __name__ == "__main__":
    main()
