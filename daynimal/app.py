"""
Daynimal Flet App - Desktop/Mobile Application

A cross-platform application built with Flet (Flutter for Python) that displays
daily animal discoveries with enriched information.
"""

import flet as ft

from daynimal.db.first_launch import resolve_database
from daynimal.repository import AnimalRepository
from daynimal.ui.app_controller import AppController

# Try to import debugger (optional)
try:
    import daynimal.debug  # noqa: F401

    DEBUG_AVAILABLE = True
except ImportError:
    DEBUG_AVAILABLE = False


class DaynimalApp:
    """Main application class for Daynimal Flet app."""

    def __init__(self, page: ft.Page):
        self.page = page
        self.page.title = "Daynimal"
        self.page.padding = 0
        self.page.scroll = ft.ScrollMode.AUTO

        # Get debugger from page data if available
        self.debugger = None
        if hasattr(page, "data") and isinstance(page.data, dict):
            self.debugger = page.data.get("debugger")

        # Log app initialization
        if self.debugger:
            self.debugger.logger.info("DaynimalApp initialized")

        # Register cleanup handlers
        self.page.on_disconnect = self.on_disconnect
        if hasattr(self.page, "on_close"):
            self.page.on_close = self.on_close

        # Build UI
        self.build()

    def build(self):
        """Build the user interface."""
        # Load and apply theme from settings
        self._load_theme()

        # Check if database exists
        db_path = resolve_database()
        if db_path is None:
            # Show first-launch setup screen
            from daynimal.ui.state import AppState
            from daynimal.ui.views.setup_view import SetupView

            self.setup_view = SetupView(
                page=self.page,
                app_state=AppState(),
                on_setup_complete=self._on_setup_complete,
                debugger=self.debugger,
            )
            self.page.add(self.setup_view.build())
        else:
            self._build_main_app()

        self.page.update()

    def _build_main_app(self):
        """Build the main application UI (after DB is available)."""
        self.page.controls.clear()
        self.app_controller = AppController(page=self.page, debugger=self.debugger)
        self.page.add(self.app_controller.build())

    def _on_setup_complete(self):
        """Called when first-launch setup finishes successfully."""
        resolve_database()  # Update settings with new DB path
        self._build_main_app()
        self.page.update()

    def _load_theme(self):
        """Load theme setting from database and apply to page."""
        try:
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
        if self.debugger:
            self.debugger.logger.info("Cleaning up application resources...")

        # Cleanup app controller
        if hasattr(self, "app_controller"):
            try:
                self.app_controller.cleanup()
                if self.debugger:
                    self.debugger.logger.info("AppController cleaned up successfully")
            except Exception as e:
                if self.debugger:
                    self.debugger.logger.error(f"Error cleaning up AppController: {e}")

        if self.debugger:
            self.debugger.logger.info("Cleanup completed")

    def on_disconnect(self, e):
        """Handle page disconnect event (when user closes the window)."""
        if self.debugger:
            self.debugger.logger.info("Page disconnected, cleaning up...")
        try:
            self.cleanup()
        except Exception as error:
            if self.debugger:
                self.debugger.logger.error(f"Error during disconnect cleanup: {error}")

    def on_close(self, e):
        """Handle page close event."""
        if self.debugger:
            self.debugger.logger.info("Page closed, cleaning up...")
        try:
            self.cleanup()
        except Exception as error:
            if self.debugger:
                self.debugger.logger.error(f"Error during close cleanup: {error}")


def main():
    """Main entry point for the Flet app."""

    def app_main(page: ft.Page):
        DaynimalApp(page)

    # Run as desktop app
    ft.app(target=app_main)


if __name__ == "__main__":
    main()
