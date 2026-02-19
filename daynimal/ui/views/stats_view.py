"""Statistics view for displaying database statistics."""

import asyncio
import logging
import traceback

import flet as ft

from daynimal.ui.components.widgets import view_header
from daynimal.ui.state import AppState
from daynimal.ui.views.base import BaseView

logger = logging.getLogger("daynimal")


class StatsView(BaseView):
    """View for displaying database statistics with responsive cards."""

    def __init__(self, page: ft.Page, app_state: AppState | None = None):
        """
        Initialize StatsView.

        Args:
            page: Flet page instance
            app_state: Shared application state
        """
        super().__init__(page, app_state)
        self.stats_container = ft.Column(controls=[], spacing=10)
        self.cached_stats: dict | None = None

    def build(self) -> ft.Control:
        """Build the statistics view UI."""
        # Header
        header = view_header("📊 Statistiques")

        # Content container
        content = ft.Column(
            controls=[
                header,
                ft.Divider(),
                ft.Container(content=self.stats_container, padding=20),
            ]
        )

        # If stats already cached, display them immediately
        if self.cached_stats is not None:
            self._display_stats(self.cached_stats)
            self.page.update()

        # Load/refresh stats asynchronously (will update if DB changed)
        asyncio.create_task(self.load_stats())

        return content

    def _stat_card(self, icon, color, value: str, label: str, subtitle: str = ""):
        """Build a compact horizontal stat card."""
        texts = [
            ft.Text(
                value, size=22, weight=ft.FontWeight.BOLD, color=color, no_wrap=True
            ),
            ft.Text(label, size=14, color=ft.Colors.GREY_500),
        ]
        if subtitle:
            texts.append(ft.Text(subtitle, size=12, color=ft.Colors.GREY_500))

        icon_circle = ft.Container(
            content=ft.Icon(icon, size=24, color=ft.Colors.WHITE),
            width=44,
            height=44,
            border_radius=22,
            bgcolor=color,
            alignment=ft.Alignment(0, 0),
        )

        return ft.Card(
            content=ft.Container(
                content=ft.Row(
                    controls=[
                        icon_circle,
                        ft.Column(controls=texts, spacing=2, tight=True),
                    ],
                    spacing=15,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                padding=ft.Padding(left=20, right=20, top=14, bottom=14),
            )
        )

    def _display_stats(self, stats: dict):
        """Display statistics cards."""
        self.stats_container.controls = [
            self._stat_card(
                ft.Icons.PETS,
                ft.Colors.PRIMARY,
                f"{stats['total_taxa']:,}",
                "Taxa totaux",
            ),
            self._stat_card(
                ft.Icons.FAVORITE,
                ft.Colors.BLUE,
                f"{stats['species_count']:,}",
                "Espèces",
            ),
            self._stat_card(
                ft.Icons.INFO,
                ft.Colors.GREEN_500,
                f"{stats['enriched_count']:,}",
                "Animaux enrichis",
                subtitle=stats["enrichment_progress"],
            ),
            self._stat_card(
                ft.Icons.TRANSLATE,
                ft.Colors.AMBER_500,
                f"{stats['vernacular_names']:,}",
                "Noms vernaculaires",
            ),
        ]

    async def load_stats(self):
        """Load statistics from repository."""
        # Show loading only if no cached stats
        if self.cached_stats is None:
            self.stats_container.controls = [
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.ProgressRing(width=60, height=60),
                            ft.Text("Chargement des statistiques...", size=18),
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
            # Fetch stats
            def fetch_stats():
                return self.app_state.repository.get_stats()

            stats = await asyncio.to_thread(fetch_stats)

            # Update cache
            self.cached_stats = stats

            # Display stats
            self._display_stats(stats)
            self.page.update()

        except Exception as error:
            logger.error(f"Error loading stats: {error}")
            traceback.print_exc()

            # Show error
            self.stats_container.controls = [
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
