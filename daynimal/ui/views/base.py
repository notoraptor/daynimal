"""Base view class for Daynimal UI.

All views inherit from BaseView to ensure consistent interface and behavior.
"""

import logging
from abc import ABC, abstractmethod

import flet as ft

from daynimal.ui.state import AppState

logger = logging.getLogger("daynimal")


class BaseView(ABC):
    """Abstract base class for all views in the Daynimal app.

    Provides:
    - Common interface (build, refresh)
    - Helper methods for loading/error/empty states
    - Access to shared app state

    Subclasses must implement:
    - build(): Return the view's UI controls
    - refresh(): Reload/update view data
    """

    def __init__(self, page: ft.Page, app_state: AppState):
        """Initialize base view.

        Args:
            page: Flet page instance
            app_state: Shared application state
        """
        self.page = page
        self.app_state = app_state
        self.view_title: str = ""
        self.container = ft.Column(controls=[], spacing=10)

    @abstractmethod
    def build(self) -> ft.Control:
        """Build the view's UI.

        Returns:
            ft.Control: The root control for this view.
        """
        pass

    async def refresh(self):
        """Refresh view data.

        Called when the view becomes active (e.g., user navigates to it).
        Should reload data and update UI.
        Subclasses can override this to provide custom refresh behavior.
        """
        pass

    def show_loading(self, message: str = "Chargement..."):
        """Show loading indicator.

        Args:
            message: Loading message to display.
        """
        from daynimal.ui.components.widgets import LoadingWidget

        self.container.controls = [LoadingWidget(message)]
        try:
            self.page.update()
        except Exception:
            pass

    def show_error(self, title: str, details: str = ""):
        """Show error state.

        Args:
            title: Error title (short description).
            details: Optional error details (longer description or stack trace).
        """
        from daynimal.ui.components.widgets import ErrorWidget

        self.container.controls = [ErrorWidget(title, details)]
        try:
            self.page.update()
        except Exception:
            pass

    def show_empty_state(
        self,
        icon,
        title: str,
        description: str,
        icon_size: int = 80,
        icon_color: str = ft.Colors.GREY_500,
    ):
        """Show empty state.

        Args:
            icon: Flet icon to display.
            title: Title text.
            description: Description text.
            icon_size: Icon size in pixels.
            icon_color: Icon color.
        """
        from daynimal.ui.components.widgets import EmptyStateWidget

        self.container.controls = [
            EmptyStateWidget(icon, title, description, icon_size, icon_color)
        ]
        try:
            self.page.update()
        except Exception:
            pass

    def log_info(self, message: str):
        """Log info message.

        Args:
            message: Message to log.
        """
        logger.info(message)

    def log_error(self, context: str, error: Exception):
        """Log error message.

        Args:
            context: Context where error occurred.
            error: The exception that was raised.
        """
        logger.error(f"Error in {context}: {type(error).__name__}: {error}")
        logger.exception(error)
