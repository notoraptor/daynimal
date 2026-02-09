"""Statistics view for displaying database statistics."""

import asyncio
import traceback

import flet as ft

from daynimal.ui.state import AppState
from daynimal.ui.views.base import BaseView


class StatsView(BaseView):
    """View for displaying database statistics with responsive cards."""

    def __init__(self, page: ft.Page, app_state: AppState | None = None, debugger=None):
        """
        Initialize StatsView.

        Args:
            page: Flet page instance
            app_state: Shared application state
            debugger: Optional debugger instance for logging
        """
        super().__init__(page, app_state, debugger)
        self.stats_container = ft.Row(
            controls=[],
            spacing=15,
            wrap=True,
            run_spacing=15,
            alignment=ft.MainAxisAlignment.CENTER,
            vertical_alignment=ft.CrossAxisAlignment.START,  # Align cards to top
        )
        self.cached_stats: dict | None = None

    def build(self) -> ft.Control:
        """Build the statistics view UI."""
        # Header
        header = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Text(
                        "📊 Statistiques",
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
                ft.Container(content=self.stats_container, padding=20, expand=True),
            ],
            expand=True,
        )

        # If stats already cached, display them immediately
        if self.cached_stats is not None:
            self._display_stats(self.cached_stats)
            self.page.update()

        # Load/refresh stats asynchronously (will update if DB changed)
        asyncio.create_task(self.load_stats())

        return content

    def _display_stats(self, stats: dict):
        """Display statistics cards."""
        controls = []

        # Uniform card height for consistent layout
        card_min_height = 220

        # Total taxa
        controls.append(
            ft.Card(
                content=ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Icon(ft.Icons.PETS, size=50, color=ft.Colors.PRIMARY),
                            ft.Text(
                                f"{stats['total_taxa']:,}",
                                size=32,
                                weight=ft.FontWeight.BOLD,
                                color=ft.Colors.PRIMARY,
                                no_wrap=True,
                            ),
                            ft.Text("Taxa totaux", size=16, color=ft.Colors.GREY_500),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=5,
                        tight=True,
                    ),
                    padding=30,
                    height=card_min_height,
                )
            )
        )

        # Species count
        controls.append(
            ft.Card(
                content=ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Icon(ft.Icons.FAVORITE, size=50, color=ft.Colors.BLUE),
                            ft.Text(
                                f"{stats['species_count']:,}",
                                size=32,
                                weight=ft.FontWeight.BOLD,
                                color=ft.Colors.BLUE,
                                no_wrap=True,
                            ),
                            ft.Text("Espèces", size=16, color=ft.Colors.GREY_500),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=5,
                        tight=True,
                    ),
                    padding=30,
                    height=card_min_height,
                )
            )
        )

        # Enriched count
        controls.append(
            ft.Card(
                content=ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Icon(ft.Icons.INFO, size=50, color=ft.Colors.GREEN_500),
                            ft.Text(
                                f"{stats['enriched_count']:,}",
                                size=32,
                                weight=ft.FontWeight.BOLD,
                                color=ft.Colors.GREEN_500,
                                no_wrap=True,
                            ),
                            ft.Text(
                                "Animaux enrichis", size=16, color=ft.Colors.GREY_500
                            ),
                            ft.Text(
                                stats["enrichment_progress"],
                                size=14,
                                color=ft.Colors.GREY_500,
                            ),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=5,
                        tight=True,
                    ),
                    padding=30,
                    height=card_min_height,
                )
            )
        )

        # Vernacular names
        controls.append(
            ft.Card(
                content=ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Icon(
                                ft.Icons.TRANSLATE, size=50, color=ft.Colors.AMBER_500
                            ),
                            ft.Text(
                                f"{stats['vernacular_names']:,}",
                                size=32,
                                weight=ft.FontWeight.BOLD,
                                color=ft.Colors.AMBER_500,
                                no_wrap=True,
                            ),
                            ft.Text(
                                "Noms vernaculaires", size=16, color=ft.Colors.GREY_500
                            ),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=5,
                        tight=True,
                    ),
                    padding=30,
                    height=card_min_height,
                )
            )
        )

        self.stats_container.controls = controls

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
            # Log error with full traceback
            error_msg = f"Error loading stats: {error}"
            error_traceback = traceback.format_exc()

            if self.debugger:
                self.debugger.log_error("load_stats", error)
                self.debugger.logger.error(f"Full traceback:\n{error_traceback}")
            else:
                # Fallback: print to console if no debugger
                print(f"ERROR: {error_msg}")
                print(f"Traceback:\n{error_traceback}")

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
