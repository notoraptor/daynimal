"""Search view for Daynimal app.

This module provides the search interface with a classic search field
(submit on Enter or button click).
"""

import asyncio
from typing import Callable

import flet as ft

from daynimal.ui.components.animal_card import create_search_card
from daynimal.ui.components.widgets import view_header
from daynimal.ui.state import AppState
from daynimal.ui.views.base import BaseView


class SearchView(BaseView):
    """Search view with search field and results list.

    Features:
    - Search triggered by Enter key or search button
    - Empty state when no query
    - Loading indicator during search
    - Results as clickable cards
    - No results state
    """

    def __init__(
        self, page: ft.Page, app_state: AppState, on_result_click: Callable[[int], None]
    ):
        """Initialize search view.

        Args:
            page: Flet page instance.
            app_state: Shared application state.
            on_result_click: Callback when search result is clicked. Receives taxon_id.
        """
        super().__init__(page, app_state)
        self.on_result_click = on_result_click

        # Create UI components
        self.search_field = ft.TextField(
            label="Rechercher un animal",
            hint_text="Nom scientifique ou vernaculaire",
            prefix_icon=ft.Icons.SEARCH,
            on_submit=self._on_submit,
            autofocus=True,
            expand=True,
        )

        self.search_button = ft.IconButton(
            icon=ft.Icons.SEARCH, on_click=self._on_search_click, tooltip="Rechercher"
        )

        self.results_container = ft.Column(controls=[], spacing=10)

    def build(self) -> ft.Control:
        """Build the search view UI.

        Returns:
            ft.Control: The root control for search view.
        """
        # Header
        header = view_header("🔍 Recherche")

        # Initial empty state
        self.show_empty_search_state()

        # Search bar: TextField + button
        search_bar = ft.Container(
            content=ft.Row(
                controls=[self.search_field, self.search_button],
                spacing=5,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=ft.Padding(left=20, right=20, top=10, bottom=0),
        )

        # Assemble view
        self.container.controls = [
            header,
            ft.Divider(),
            search_bar,
            ft.Container(content=self.results_container, padding=20),
        ]

        return self.container

    async def refresh(self):
        """Refresh search view (no-op for search view).

        Search view doesn't need refresh on navigation - it maintains its state.
        """
        pass

    def _on_submit(self, e):
        """Handle Enter key in search field."""
        query = self.search_field.value.strip()
        if query:
            asyncio.create_task(self.perform_search(query))

    def _on_search_click(self, e):
        """Handle search button click."""
        query = self.search_field.value.strip()
        if query:
            asyncio.create_task(self.perform_search(query))

    def show_empty_search_state(self):
        """Show empty state (before any search)."""
        self.results_container.controls = [
            ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Icon(ft.Icons.SEARCH, size=80, color=ft.Colors.GREY_500),
                        ft.Text(
                            "Recherchez un animal", size=20, weight=ft.FontWeight.BOLD
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
                alignment=ft.Alignment(0, 0),
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
                alignment=ft.Alignment(0, 0),
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
                                    "Aucun résultat", size=20, weight=ft.FontWeight.BOLD
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
                        alignment=ft.Alignment(0, 0),
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
                    alignment=ft.Alignment(0, 0),
                )
            ]

        finally:
            self.page.update()
