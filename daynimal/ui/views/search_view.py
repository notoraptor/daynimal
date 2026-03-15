"""Search view for Daynimal app.

This module provides the search interface with a classic search field
(submit on Enter or button click).
"""

import asyncio
from typing import Callable

import flet as ft

from daynimal.ui.components.animal_card import create_search_card
from daynimal.ui.components.pagination import PaginationBar
from daynimal.ui.state import AppState
from daynimal.ui.views.base import BaseView

PER_PAGE = 20
MAX_RESULTS = 50


class SearchView(BaseView):
    """Search view with search field and results list.

    Features:
    - Search triggered by Enter key or search button
    - Empty state when no query
    - Loading indicator during search
    - Results as clickable cards with pagination
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
        self.view_title = "🔍 Recherche"
        self.on_result_click = on_result_click
        self.all_results = []
        self.current_page = 1
        self.total_count = 0

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
            icon=ft.Icons.ARROW_FORWARD,
            on_click=self._on_search_click,
            tooltip="Rechercher",
        )

        # Info container (result count) — fixed at top with search bar
        self.info_container = ft.Column(
            controls=[], spacing=0, horizontal_alignment=ft.CrossAxisAlignment.CENTER
        )
        self.view_subheader = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[self.search_field, self.search_button],
                        spacing=5,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    self.info_container,
                ],
                spacing=5,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=ft.Padding(left=20, right=20, top=10, bottom=5),
        )

        # Pagination — fixed at bottom
        self.pagination_container = ft.Column(
            controls=[], spacing=0, horizontal_alignment=ft.CrossAxisAlignment.CENTER
        )
        self.view_footer = ft.Container(content=self.pagination_container)

        self.results_container = ft.Column(controls=[], spacing=10)

    def build(self) -> ft.Control:
        """Build the search view UI.

        Returns:
            ft.Control: The root control for search view.
        """
        # Initial empty state
        self.show_empty_search_state()

        return ft.Container(content=self.results_container, padding=20)

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
        self.info_container.controls = []
        self.pagination_container.controls = []
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
        self.current_page = 1

        # Show loading
        self.info_container.controls = []
        self.pagination_container.controls = []
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
                lambda: self.app_state.repository.search(query, limit=MAX_RESULTS)
            )

            self.log_info(f"Search completed: {len(results)} results for '{query}'")
            self.all_results = results
            self.total_count = len(results)

            if not results:
                # No results
                self.info_container.controls = []
                self.pagination_container.controls = []
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
                self._display_page()

        except Exception as error:
            self.log_error("perform_search", error)
            self.info_container.controls = []
            self.pagination_container.controls = []
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

    def _display_page(self):
        """Display the current page of results."""
        start = (self.current_page - 1) * PER_PAGE
        end = start + PER_PAGE
        page_results = self.all_results[start:end]

        # Info (fixed at top)
        self.info_container.controls = [
            ft.Text(
                f"{self.total_count} {'résultat' if self.total_count == 1 else 'résultats'}",
                size=16,
                color=ft.Colors.GREY_500,
            )
        ]

        # Pagination (fixed at bottom)
        self.pagination_container.controls = [
            PaginationBar(
                page=self.current_page,
                total=self.total_count,
                per_page=PER_PAGE,
                on_page_change=self._on_page_change,
            ).build()
        ]

        # Result cards (scrollable)
        cards = []
        for animal in page_results:
            card = create_search_card(animal, self.on_result_click)
            cards.append(card)

        self.results_container.controls = cards

    def _on_page_change(self, new_page: int):
        """Handle page change from pagination bar."""
        self.current_page = new_page
        self._display_page()
        self.page.update()
