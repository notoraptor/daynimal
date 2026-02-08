"""Search view for Daynimal app.

This module provides the search interface with debounced search functionality.
"""

import asyncio
from typing import Callable

import flet as ft

from daynimal.ui.components.animal_card import create_search_card
from daynimal.ui.state import AppState
from daynimal.ui.utils.debounce import Debouncer
from daynimal.ui.views.base import BaseView


class SearchView(BaseView):
    """Search view with debounced search field and results list.

    Features:
    - Debounced search (300ms delay)
    - Empty state when no query
    - Loading indicator during search
    - Results as clickable cards
    - No results state
    """

    def __init__(
        self,
        page: ft.Page,
        app_state: AppState,
        on_result_click: Callable[[int], None],
        debugger=None,
    ):
        """Initialize search view.

        Args:
            page: Flet page instance.
            app_state: Shared application state.
            on_result_click: Callback when search result is clicked. Receives taxon_id.
            debugger: Optional debugger instance for logging.
        """
        super().__init__(page, app_state, debugger)
        self.on_result_click = on_result_click
        self.debouncer = Debouncer(delay=0.3)  # 300ms debounce

        # Create UI components
        self.search_field = ft.TextField(
            label="Rechercher un animal",
            hint_text="Nom scientifique ou vernaculaire",
            prefix_icon=ft.Icons.SEARCH,
            on_change=self.on_search_change,
            autofocus=True,
        )

        self.results_container = ft.Column(
            controls=[],
            spacing=10,
        )

    def build(self) -> ft.Control:
        """Build the search view UI.

        Returns:
            ft.Control: The root control for search view.
        """
        # Header
        header = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.SEARCH, size=32),
                    ft.Text(
                        "Recherche",
                        size=24,
                        weight=ft.FontWeight.BOLD,
                    ),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            padding=20,
        )

        # Initial empty state
        self.show_empty_search_state()

        # Assemble view
        self.container.controls = [
            header,
            ft.Divider(),
            ft.Container(
                content=self.search_field,
                padding=ft.Padding(left=20, right=20, top=10, bottom=0),
            ),
            ft.Container(content=self.results_container, padding=20, expand=True),
        ]

        return self.container

    async def refresh(self):
        """Refresh search view (no-op for search view).

        Search view doesn't need refresh on navigation - it maintains its state.
        """
        pass

    def on_search_change(self, e):
        """Handle search field changes (with debouncing).

        Args:
            e: Change event from TextField.
        """
        query = e.control.value.strip()

        if not query:
            # Reset to empty state
            self.show_empty_search_state()
            self.page.update()
            return

        # Trigger debounced search
        asyncio.create_task(self.debouncer.debounce(self.perform_search, query))

    def show_empty_search_state(self):
        """Show empty state (before any search)."""
        self.results_container.controls = [
            ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Icon(ft.Icons.SEARCH, size=80, color=ft.Colors.GREY_500),
                        ft.Text(
                            "Recherchez un animal",
                            size=20,
                            weight=ft.FontWeight.BOLD,
                        ),
                        ft.Text(
                            "Entrez un nom scientifique ou vernaculaire",
                            size=14,
                            color=ft.Colors.GREY_500,
                            text_align=ft.TextAlign.CENTER,
                        ),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=10,
                ),
                padding=40,
                expand=True,
            )
        ]

    async def perform_search(self, query: str):
        """Perform search in repository.

        Args:
            query: Search query string.
        """
        self.log_info(f"Search started: '{query}'")

        # Show loading
        self.results_container.controls = [
            ft.Container(
                content=ft.Column(
                    controls=[
                        ft.ProgressRing(width=40, height=40),
                        ft.Text("Recherche en cours...", size=16),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=20,
                ),
                padding=40,
                expand=True,
            )
        ]
        self.page.update()
        await asyncio.sleep(0.1)  # Let UI update

        try:
            # Perform search (in background thread)
            results = await asyncio.to_thread(
                lambda: self.app_state.repository.search(query, limit=50)
            )

            self.log_info(f"Search completed: {len(results)} results for '{query}'")

            if not results:
                # No results
                self.results_container.controls = [
                    ft.Container(
                        content=ft.Column(
                            controls=[
                                ft.Icon(
                                    ft.Icons.SEARCH_OFF,
                                    size=80,
                                    color=ft.Colors.GREY_500,
                                ),
                                ft.Text(
                                    "Aucun résultat",
                                    size=20,
                                    weight=ft.FontWeight.BOLD,
                                ),
                                ft.Text(
                                    f"Aucun animal trouvé pour '{query}'",
                                    size=14,
                                    color=ft.Colors.GREY_500,
                                    text_align=ft.TextAlign.CENTER,
                                ),
                            ],
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            alignment=ft.MainAxisAlignment.CENTER,
                            spacing=10,
                        ),
                        padding=40,
                        expand=True,
                    )
                ]
            else:
                # Display results
                controls = [
                    ft.Text(
                        f"{len(results)} résultat(s)", size=16, color=ft.Colors.GREY_500
                    )
                ]

                for animal in results:
                    card = create_search_card(animal, self.on_result_click)
                    controls.append(card)

                self.results_container.controls = controls

        except Exception as error:
            self.log_error("perform_search", error)
            self.results_container.controls = [
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Icon(ft.Icons.ERROR, size=60, color=ft.Colors.ERROR),
                            ft.Text(
                                "Erreur lors de la recherche",
                                size=20,
                                color=ft.Colors.ERROR,
                                weight=ft.FontWeight.BOLD,
                            ),
                            ft.Text(str(error), size=14),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=10,
                    ),
                    padding=40,
                    expand=True,
                )
            ]

        finally:
            self.page.update()
