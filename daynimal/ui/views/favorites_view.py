"""Favorites view for displaying favorite animals."""

import asyncio
import traceback
from typing import Callable

import flet as ft

from daynimal.repository import AnimalRepository
from daynimal.ui.views.base import BaseView


class FavoritesView(BaseView):
    """View for displaying and managing favorite animals."""

    def __init__(
        self,
        page: ft.Page,
        repository: AnimalRepository | None = None,
        on_animal_click: Callable[[int], None] | None = None,
        debugger=None,
    ):
        """
        Initialize FavoritesView.

        Args:
            page: Flet page instance
            repository: Animal repository instance
            on_animal_click: Callback when an animal is clicked (receives taxon_id)
            debugger: Optional debugger instance for logging
        """
        super().__init__(page, repository, debugger)
        self.on_animal_click = on_animal_click
        self.favorites_list = ft.Column(controls=[], spacing=10)

    def build(self) -> ft.Control:
        """Build the favorites view UI."""
        # Header
        header = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Text(
                        "⭐ Favoris",
                        size=28,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.PRIMARY,
                    )
                ],
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            padding=20,
        )

        # Content container
        content = ft.Column(
            controls=[
                header,
                ft.Divider(),
                ft.Container(content=self.favorites_list, padding=20, expand=True),
            ],
            expand=True,
        )

        # Load favorites asynchronously
        asyncio.create_task(self.load_favorites())

        return content

    async def load_favorites(self):
        """Load favorites from repository."""
        # Show loading
        self.favorites_list.controls = [
            ft.Container(
                content=ft.Column(
                    controls=[
                        ft.ProgressRing(width=60, height=60),
                        ft.Text("Chargement des favoris...", size=18),
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
            # Fetch favorites
            def fetch_favorites():
                # Create repository if needed
                if self.repository is None:
                    self.repository = AnimalRepository()
                return self.repository.get_favorites(page=1, per_page=50)

            favorites_items, total = await asyncio.to_thread(fetch_favorites)

            if not favorites_items:
                # Empty favorites
                self.favorites_list.controls = [
                    ft.Container(
                        content=ft.Column(
                            controls=[
                                ft.Icon(
                                    ft.Icons.FAVORITE, size=80, color=ft.Colors.GREY_500
                                ),
                                ft.Text(
                                    "Aucun favori", size=20, weight=ft.FontWeight.BOLD
                                ),
                                ft.Text(
                                    "Ajoutez des animaux à vos favoris",
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
                # Display favorites items
                controls = [
                    ft.Text(f"{total} favori(s)", size=16, color=ft.Colors.GREY_500)
                ]

                for item in favorites_items:
                    card = ft.Card(
                        content=ft.Container(
                            content=ft.Column(
                                controls=[
                                    ft.Row(
                                        controls=[
                                            ft.Text(
                                                item.taxon.canonical_name
                                                or item.taxon.scientific_name,
                                                size=18,
                                                weight=ft.FontWeight.BOLD,
                                            )
                                        ]
                                    ),
                                    ft.Text(
                                        item.taxon.scientific_name,
                                        size=14,
                                        italic=True,
                                        color=ft.Colors.BLUE,
                                    ),
                                    ft.Row(
                                        controls=[
                                            ft.Icon(
                                                ft.Icons.FAVORITE,
                                                size=16,
                                                color=ft.Colors.RED,
                                            ),
                                            ft.Text(
                                                "Favori",
                                                size=12,
                                                color=ft.Colors.GREY_500,
                                            ),
                                            ft.Container(expand=True),  # Spacer
                                            ft.Icon(
                                                ft.Icons.ARROW_FORWARD,
                                                size=16,
                                                color=ft.Colors.GREY_400,
                                            ),
                                        ],
                                        spacing=5,
                                    ),
                                ],
                                spacing=5,
                            ),
                            padding=15,
                            data=item.taxon.taxon_id,  # Store taxon_id for click handler
                            on_click=self._on_favorite_item_click,
                            ink=True,  # Add ink ripple effect on click
                        ),
                    )
                    controls.append(card)

                self.favorites_list.controls = controls

        except Exception as error:
            # Log error with full traceback
            error_msg = f"Error in load_favorites: {error}"
            error_traceback = traceback.format_exc()

            if self.debugger:
                self.debugger.log_error("load_favorites", error)
                self.debugger.logger.error(f"Full traceback:\n{error_traceback}")
            else:
                # Fallback: print to console if no debugger
                print(f"ERROR: {error_msg}")
                print(f"Traceback:\n{error_traceback}")

            # Show error
            self.favorites_list.controls = [
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

    def _on_favorite_item_click(self, e):
        """Handle click on a favorite item."""
        try:
            taxon_id = e.control.data

            if self.debugger:
                self.debugger.logger.info(f"Favorite item clicked: taxon_id={taxon_id}")

            # Call parent callback to load animal
            if self.on_animal_click:
                self.on_animal_click(taxon_id)

        except Exception as error:
            error_msg = f"Error clicking favorite item: {error}"
            error_traceback = traceback.format_exc()

            if self.debugger:
                self.debugger.log_error("on_favorite_item_click", error)
                self.debugger.logger.error(f"Full traceback:\n{error_traceback}")
            else:
                print(f"ERROR: {error_msg}")
                print(f"Traceback:\n{error_traceback}")
