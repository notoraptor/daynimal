"""Favorites view for displaying favorite animals."""

import asyncio
import logging
import traceback
from typing import Callable

import flet as ft

from daynimal.ui.components.animal_card import create_favorite_card_with_delete
from daynimal.ui.components.pagination import PaginationBar
from daynimal.ui.components.widgets import view_header
from daynimal.ui.state import AppState
from daynimal.ui.views.base import BaseView

logger = logging.getLogger("daynimal")

PER_PAGE = 20
_MAX_NAME_LEN = 30


def _truncate_name(name: str) -> str:
    """Truncate a display name for SnackBar messages."""
    if len(name) > _MAX_NAME_LEN:
        return name[:_MAX_NAME_LEN] + "..."
    return name


class FavoritesView(BaseView):
    """View for displaying and managing favorite animals."""

    def __init__(
        self,
        page: ft.Page,
        app_state: AppState | None = None,
        on_animal_click: Callable[[int], None] | None = None,
    ):
        """
        Initialize FavoritesView.

        Args:
            page: Flet page instance
            app_state: Shared application state
            on_animal_click: Callback when an animal is clicked (receives taxon_id)
        """
        super().__init__(page, app_state)
        self.on_animal_click = on_animal_click
        self.current_page = 1
        self.total_count = 0
        self.favorites_list = ft.Column(controls=[], spacing=10)
        self.pagination_container = ft.Container()

    def build(self) -> ft.Control:
        """Build the favorites view UI."""
        # Header
        header = view_header("⭐ Favoris")

        # Content container
        content = ft.Column(
            controls=[
                header,
                ft.Divider(),
                ft.Container(content=self.favorites_list, padding=20, expand=True),
                self.pagination_container,
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
                return self.app_state.repository.get_favorites(
                    page=self.current_page, per_page=PER_PAGE
                )

            favorites_items, total = await asyncio.to_thread(fetch_favorites)
            self.total_count = total

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
                        alignment=ft.Alignment.CENTER,
                        expand=True,
                    )
                ]
            else:
                # Display favorites items
                controls = [
                    ft.Text(f"{total} favori(s)", size=16, color=ft.Colors.GREY_500)
                ]

                for item in favorites_items:
                    card = create_favorite_card_with_delete(
                        item, self._on_item_click, self._on_delete_favorite
                    )
                    controls.append(card)

                self.favorites_list.controls = controls

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
            logger.error(f"Error in load_favorites: {error}")
            traceback.print_exc()

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

    def _on_page_change(self, new_page: int):
        """Handle page change from pagination bar."""
        self.current_page = new_page
        asyncio.create_task(self.load_favorites())

    def _on_item_click(self, taxon_id: int):
        """Handle click on a favorite item."""
        try:
            logger.info(f"Favorite item clicked: taxon_id={taxon_id}")
            if self.on_animal_click:
                self.on_animal_click(taxon_id)
        except Exception as error:
            logger.error(f"Error in on_favorite_item_click: {error}")
            traceback.print_exc()

    def _on_delete_favorite(self, taxon_id: int, display_name: str):
        """Handle delete button click on a favorite item."""
        asyncio.create_task(self._delete_favorite_async(taxon_id, display_name))

    async def _delete_favorite_async(self, taxon_id: int, display_name: str):
        """Remove a favorite and refresh the list."""
        try:
            removed = await asyncio.to_thread(
                self.app_state.repository.remove_favorite, taxon_id
            )
            if removed:
                await self.load_favorites()
                label = _truncate_name(display_name)
                self.page.show_dialog(
                    ft.SnackBar(
                        ft.Text(f"Retiré des favoris : {label}"), show_close_icon=True
                    )
                )
            else:
                self.page.show_dialog(
                    ft.SnackBar(ft.Text("Favori introuvable"), show_close_icon=True)
                )
        except Exception as error:
            logger.error(f"Error removing favorite {taxon_id}: {error}")
            self.page.show_dialog(
                ft.SnackBar(
                    ft.Text("Erreur lors de la suppression"),
                    bgcolor=ft.Colors.ERROR,
                    show_close_icon=True,
                )
            )
