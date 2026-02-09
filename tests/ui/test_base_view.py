"""
Tests for BaseView abstract class.

Tests helper methods: show_loading, show_error, show_empty_state,
log_info, log_error, and default refresh behavior.
"""

import pytest
from unittest.mock import MagicMock

import flet as ft

from daynimal.ui.views.base import BaseView
from daynimal.ui.state import AppState


class ConcreteView(BaseView):
    """Concrete implementation of BaseView for testing."""

    def build(self) -> ft.Control:
        return self.container


class TestBaseViewInit:
    """Tests for BaseView initialization."""

    def test_stores_page_and_state(self):
        """Test that page and app_state are stored."""
        page = MagicMock(spec=ft.Page)
        state = MagicMock(spec=AppState)

        view = ConcreteView(page, state)

        assert view.page is page
        assert view.app_state is state
        assert view.debugger is None

    def test_init_with_debugger(self):
        """Test initialization with debugger."""
        page = MagicMock(spec=ft.Page)
        state = MagicMock(spec=AppState)
        debugger = MagicMock()

        view = ConcreteView(page, state, debugger=debugger)

        assert view.debugger is debugger

    def test_container_initialized(self):
        """Test that container is initialized as empty Column."""
        page = MagicMock(spec=ft.Page)
        state = MagicMock(spec=AppState)

        view = ConcreteView(page, state)

        assert isinstance(view.container, ft.Column)
        assert view.container.controls == []

    def test_build_returns_container(self):
        """Test that build() returns the container."""
        page = MagicMock(spec=ft.Page)
        state = MagicMock(spec=AppState)

        view = ConcreteView(page, state)
        result = view.build()

        assert result is view.container


class TestBaseViewRefresh:
    """Tests for BaseView.refresh() default implementation."""

    @pytest.mark.asyncio
    async def test_refresh_default_does_nothing(self):
        """Test that default refresh() does nothing."""
        page = MagicMock(spec=ft.Page)
        state = MagicMock(spec=AppState)

        view = ConcreteView(page, state)
        await view.refresh()  # Should not raise


class TestBaseViewShowLoading:
    """Tests for BaseView.show_loading()."""

    def test_updates_container(self):
        """Test that show_loading replaces container controls."""
        page = MagicMock(spec=ft.Page)
        state = MagicMock(spec=AppState)

        view = ConcreteView(page, state)
        view.show_loading("Loading data...")

        assert len(view.container.controls) == 1
        page.update.assert_called_once()

    def test_default_message(self):
        """Test show_loading with default message."""
        page = MagicMock(spec=ft.Page)
        state = MagicMock(spec=AppState)

        view = ConcreteView(page, state)
        view.show_loading()

        assert len(view.container.controls) == 1

    def test_handles_page_update_error(self):
        """Test that show_loading handles page.update() errors gracefully."""
        page = MagicMock(spec=ft.Page)
        page.update.side_effect = Exception("Page not connected")
        state = MagicMock(spec=AppState)

        view = ConcreteView(page, state)
        view.show_loading()  # Should not raise


class TestBaseViewShowError:
    """Tests for BaseView.show_error()."""

    def test_updates_container(self):
        """Test that show_error replaces container controls."""
        page = MagicMock(spec=ft.Page)
        state = MagicMock(spec=AppState)

        view = ConcreteView(page, state)
        view.show_error("Error occurred", "Details here")

        assert len(view.container.controls) == 1
        page.update.assert_called_once()

    def test_without_details(self):
        """Test show_error without details."""
        page = MagicMock(spec=ft.Page)
        state = MagicMock(spec=AppState)

        view = ConcreteView(page, state)
        view.show_error("Error occurred")

        assert len(view.container.controls) == 1

    def test_handles_page_update_error(self):
        """Test that show_error handles page.update() errors gracefully."""
        page = MagicMock(spec=ft.Page)
        page.update.side_effect = Exception("Page not connected")
        state = MagicMock(spec=AppState)

        view = ConcreteView(page, state)
        view.show_error("Error")  # Should not raise


class TestBaseViewShowEmptyState:
    """Tests for BaseView.show_empty_state()."""

    def test_updates_container(self):
        """Test that show_empty_state replaces container controls."""
        page = MagicMock(spec=ft.Page)
        state = MagicMock(spec=AppState)

        view = ConcreteView(page, state)
        view.show_empty_state(ft.Icons.SEARCH, "No results", "Try again")

        assert len(view.container.controls) == 1
        page.update.assert_called_once()

    def test_with_custom_icon_params(self):
        """Test show_empty_state with custom icon size and color."""
        page = MagicMock(spec=ft.Page)
        state = MagicMock(spec=AppState)

        view = ConcreteView(page, state)
        view.show_empty_state(
            ft.Icons.INFO, "Empty", "Nothing here", icon_size=40, icon_color=ft.Colors.BLUE
        )

        assert len(view.container.controls) == 1

    def test_handles_page_update_error(self):
        """Test that show_empty_state handles page.update() errors gracefully."""
        page = MagicMock(spec=ft.Page)
        page.update.side_effect = Exception("Page not connected")
        state = MagicMock(spec=AppState)

        view = ConcreteView(page, state)
        view.show_empty_state(ft.Icons.INFO, "Empty", "Nothing here")  # Should not raise


class TestBaseViewLogging:
    """Tests for BaseView logging methods."""

    def test_log_info_with_debugger(self):
        """Test log_info with debugger."""
        page = MagicMock(spec=ft.Page)
        state = MagicMock(spec=AppState)
        debugger = MagicMock()

        view = ConcreteView(page, state, debugger=debugger)
        view.log_info("Test message")

        debugger.logger.info.assert_called_once_with("Test message")

    def test_log_info_without_debugger(self, capsys):
        """Test log_info falls back to print."""
        page = MagicMock(spec=ft.Page)
        state = MagicMock(spec=AppState)

        view = ConcreteView(page, state)
        view.log_info("Test message")

        captured = capsys.readouterr()
        assert "[INFO] Test message" in captured.out

    def test_log_error_with_debugger(self):
        """Test log_error with debugger."""
        page = MagicMock(spec=ft.Page)
        state = MagicMock(spec=AppState)
        debugger = MagicMock()

        view = ConcreteView(page, state, debugger=debugger)
        error = ValueError("test error")
        view.log_error("context", error)

        debugger.log_error.assert_called_once_with("context", error)

    def test_log_error_without_debugger(self, capsys):
        """Test log_error falls back to print."""
        page = MagicMock(spec=ft.Page)
        state = MagicMock(spec=AppState)

        view = ConcreteView(page, state)
        error = ValueError("test error")
        view.log_error("context", error)

        captured = capsys.readouterr()
        assert "[ERROR] context: test error" in captured.out
