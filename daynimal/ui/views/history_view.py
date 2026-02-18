"""History view for displaying animal viewing history."""

import asyncio
import traceback
from typing import Callable

import flet as ft

from daynimal.ui.components.animal_card import create_history_card
from daynimal.ui.components.pagination import PaginationBar
from daynimal.ui.components.widgets import view_header
from daynimal.ui.state import AppState
from daynimal.ui.views.base import BaseView

PER_PAGE = 20


class HistoryView(BaseView):
    """View for displaying and managing animal viewing history."""

    def __init__(
        self,
        page: ft.Page,
        app_state: AppState | None = None,
        on_animal_click: Callable[[int], None] | None = None,
        debugger=None,
    ):
        """
        Initialize HistoryView.

        Args:
            page: Flet page instance
            app_state: Shared application state
            on_animal_click: Callback when an animal is clicked (receives taxon_id)
            debugger: Optional debugger instance for logging
        """
        super().__init__(page, app_state, debugger)
        self.on_animal_click = on_animal_click
        self.current_page = 1
        self.total_count = 0
        self.history_list = ft.Column(controls=[], spacing=10)
        self.pagination_container = ft.Container()

    def build(self) -> ft.Control:
        """Build the history view UI."""
        # Header
        header = view_header("📚 Historique")

        # Content container
        content = ft.Column(
            controls=[
                header,
                ft.Divider(),
                ft.Container(content=self.history_list, padding=20),
                self.pagination_container,
            ]
        )

        # Load history asynchronously
        asyncio.create_task(self.load_history())

        return content

    async def load_history(self):
        """Load history from repository."""
        # Show loading
        self.history_list.controls = [
            ft.Container(
                content=ft.Column(
                    controls=[
                        ft.ProgressRing(width=60, height=60),
                        ft.Text("Chargement de l'historique...", size=18),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=20,
                ),
                padding=40,
            )
        ]
        self.page.update()
        await asyncio.sleep(0.1)

        try:
            # Fetch history
            def fetch_history():
                return self.app_state.repository.get_history(
                    page=self.current_page, per_page=PER_PAGE
                )

            history_items, total = await asyncio.to_thread(fetch_history)
            self.total_count = total

            if not history_items:
                # Empty history
                self.history_list.controls = [
                    ft.Container(
                        content=ft.Column(
                            controls=[
                                ft.Icon(
                                    ft.Icons.HISTORY, size=80, color=ft.Colors.GREY_500
                                ),
                                ft.Text(
                                    "Aucun historique",
                                    size=20,
                                    weight=ft.FontWeight.BOLD,
                                ),
                                ft.Text(
                                    "Consultez des animaux pour les voir apparaître ici",
                                    size=14,
                                    color=ft.Colors.GREY_500,
                                ),
                            ],
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            spacing=10,
                        ),
                        padding=40,
                    )
                ]
            else:
                # Display history items
                controls = [
                    ft.Text(
                        f"{total} animal(aux) consulté(s)",
                        size=16,
                        color=ft.Colors.GREY_500,
                    )
                ]

                for item in history_items:
                    viewed_at = item.viewed_at.strftime("%d/%m/%Y %H:%M")
                    card = create_history_card(item, self._on_item_click, viewed_at)
                    controls.append(card)

                self.history_list.controls = controls

                # Update pagination
                self.pagination_container.content = (
                    PaginationBar(
                        page=self.current_page,
                        total=total,
                        per_page=PER_PAGE,
                        on_page_change=self._on_page_change,
                    )
                    .build()
                    .content
                )

        except Exception as error:
            # Log error with full traceback
            error_msg = f"Error in load_history: {error}"
            error_traceback = traceback.format_exc()

            if self.debugger:
                self.debugger.log_error("load_history", error)
                self.debugger.logger.error(f"Full traceback:\n{error_traceback}")
            else:
                # Fallback: print to console if no debugger
                print(f"ERROR: {error_msg}")
                print(f"Traceback:\n{error_traceback}")

            # Show error
            self.history_list.controls = [
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Icon(ft.Icons.ERROR, size=60, color=ft.Colors.ERROR),
                            ft.Text(
                                "Erreur lors du chargement",
                                size=20,
                                color=ft.Colors.ERROR,
                            ),
                            ft.Text(str(error), size=14),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=10,
                    ),
                    padding=40,
                )
            ]

        finally:
            self.page.update()

    def _on_page_change(self, new_page: int):
        """Handle page change from pagination bar."""
        self.current_page = new_page
        asyncio.create_task(self.load_history())

    def _on_item_click(self, taxon_id: int):
        """Handle click on a history item."""
        try:
            if self.debugger:
                self.debugger.logger.info(f"History item clicked: taxon_id={taxon_id}")
            if self.on_animal_click:
                self.on_animal_click(taxon_id)
        except Exception as error:
            error_traceback = traceback.format_exc()
            if self.debugger:
                self.debugger.log_error("on_history_item_click", error)
                self.debugger.logger.error(f"Full traceback:\n{error_traceback}")
            else:
                print(f"ERROR: Error clicking history item: {error}")
                print(f"Traceback:\n{error_traceback}")
