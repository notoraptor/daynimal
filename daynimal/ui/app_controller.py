"""App controller for managing views and navigation."""

import asyncio
import logging
import traceback

import flet as ft

from daynimal.notifications import NotificationService
from daynimal.ui.components.widgets import ErrorWidget, LoadingWidget
from daynimal.ui.state import AppState
from daynimal.ui.views.favorites_view import FavoritesView
from daynimal.ui.views.history_view import HistoryView
from daynimal.ui.views.search_view import SearchView
from daynimal.ui.views.settings_view import SettingsView
from daynimal.ui.views.stats_view import StatsView
from daynimal.ui.views.today_view import TodayView

logger = logging.getLogger("daynimal")


class AppController:
    """
    Main application controller.

    Manages navigation, views, and orchestrates interactions between components.
    """

    def __init__(self, page: ft.Page):
        """
        Initialize AppController.

        Args:
            page: Flet page instance
        """
        self.page = page

        # Shared state
        self.state = AppState()
        self.current_view_name = "discovery"

        # Notification service
        self.notification_service = NotificationService(
            self.state.repository, on_clicked=self._on_notification_clicked
        )
        self.state.notification_service = self.notification_service

        # Content container (scrollable so navbar stays fixed at bottom)
        self.content_container = ft.Column(
            controls=[], expand=True, spacing=0, scroll=ft.ScrollMode.AUTO
        )

        # Initialize views (repository shared via AppState)
        self.discovery_view = TodayView(
            page=page, app_state=self.state, on_favorite_toggle=self.on_favorite_toggle
        )
        self.discovery_view.on_load_complete = self._update_offline_banner

        self.history_view = HistoryView(
            page=page,
            app_state=self.state,
            on_animal_click=lambda taxon_id: asyncio.create_task(
                self.load_animal_from_history(taxon_id)
            ),
        )

        self.favorites_view = FavoritesView(
            page=page,
            app_state=self.state,
            on_animal_click=lambda taxon_id: asyncio.create_task(
                self.load_animal_from_favorite(taxon_id)
            ),
        )

        self.search_view = SearchView(
            page=page,
            app_state=self.state,
            on_result_click=lambda taxon_id: asyncio.create_task(
                self.load_animal_from_search(taxon_id)
            ),
        )

        self.stats_view = StatsView(page=page, app_state=self.state)

        self.settings_view = SettingsView(
            page=page,
            app_state=self.state,
            on_offline_change=self._update_offline_banner,
        )

        # Offline banner
        self.offline_banner = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.WIFI_OFF, color=ft.Colors.WHITE, size=18),
                    ft.Text(
                        "Mode hors ligne — données en cache uniquement",
                        color=ft.Colors.WHITE,
                        size=13,
                    ),
                    ft.Button(
                        "Réessayer",
                        on_click=self._retry_connection,
                        style=ft.ButtonStyle(color=ft.Colors.WHITE),
                    ),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=10,
            ),
            bgcolor=ft.Colors.GREY_700,
            padding=ft.Padding(left=10, right=10, top=8, bottom=8),
            visible=False,
        )

        # Navigation bar
        self.nav_bar = ft.NavigationBar(
            destinations=[
                ft.NavigationBarDestination(icon=ft.Icons.PETS, label="Découverte"),
                ft.NavigationBarDestination(icon=ft.Icons.HISTORY, label="Historique"),
                ft.NavigationBarDestination(icon=ft.Icons.FAVORITE, label="Favoris"),
                ft.NavigationBarDestination(icon=ft.Icons.SEARCH, label="Recherche"),
                ft.NavigationBarDestination(
                    icon=ft.Icons.BAR_CHART, label="Statistiques"
                ),
                ft.NavigationBarDestination(icon=ft.Icons.SETTINGS, label="Paramètres"),
            ],
            label_behavior=ft.NavigationBarLabelBehavior.ALWAYS_HIDE,
            selected_index=0,
            on_change=self.on_nav_change,
        )

    def build(self) -> ft.Control:
        """Build the app UI."""
        # Main layout
        layout = ft.Column(
            controls=[self.offline_banner, self.content_container, self.nav_bar],
            expand=True,
            spacing=0,
        )

        # Show initial view
        self.show_discovery_view()

        # Start notification service
        self.notification_service.start()

        # Auto-load a random animal on start if setting enabled
        auto_load = (
            self.state.repository.get_setting("auto_load_on_start", "true") == "true"
        )
        if auto_load:
            self.page.run_task(self.discovery_view._load_random_animal, None)

        return layout

    def on_nav_change(self, e):
        """Handle navigation bar changes."""
        selected_index = e.control.selected_index

        view_names = [
            "Discovery",
            "History",
            "Favorites",
            "Search",
            "Stats",
            "Settings",
        ]
        if selected_index < len(view_names):
            logger.info(f"View changed to: {view_names[selected_index]}")

        # Update current view
        if selected_index == 0:
            self.show_discovery_view()
        elif selected_index == 1:
            self.show_history_view()
        elif selected_index == 2:
            self.show_favorites_view()
        elif selected_index == 3:
            self.show_search_view()
        elif selected_index == 4:
            self.show_stats_view()
        elif selected_index == 5:
            self.show_settings_view()

    def show_discovery_view(self):
        """Show the Discovery view."""
        self.current_view_name = "discovery"
        self.content_container.controls = [self.discovery_view.build()]
        self.page.update()

    def show_history_view(self):
        """Show the History view."""
        self.current_view_name = "history"
        self.content_container.controls = [self.history_view.build()]
        self.page.update()

    def show_favorites_view(self):
        """Show the Favorites view."""
        self.current_view_name = "favorites"
        self.content_container.controls = [self.favorites_view.build()]
        self.page.update()

    def show_search_view(self):
        """Show the Search view."""
        self.current_view_name = "search"
        self.content_container.controls = [self.search_view.build()]
        self.page.update()

    def show_stats_view(self):
        """Show the Stats view."""
        self.current_view_name = "stats"
        self.content_container.controls = [self.stats_view.build()]
        self.page.update()

    def show_settings_view(self):
        """Show the Settings view."""
        self.current_view_name = "settings"
        self.content_container.controls = [self.settings_view.build()]
        self.page.update()

    async def load_animal_from_history(self, taxon_id: int):
        """Load an animal from history and display in Today view."""
        await self._load_and_display_animal(
            taxon_id=taxon_id, source="history", enrich=True, add_to_history=False
        )

    async def load_animal_from_favorite(self, taxon_id: int):
        """Load an animal from favorites and display in Today view."""
        await self._load_and_display_animal(
            taxon_id=taxon_id, source="favorite", enrich=True, add_to_history=False
        )

    async def load_animal_from_search(self, taxon_id: int):
        """Load an animal from search and display in Today view."""
        await self._load_and_display_animal(
            taxon_id=taxon_id, source="search", enrich=True, add_to_history=True
        )

    async def _load_and_display_animal(
        self,
        taxon_id: int,
        source: str,
        enrich: bool = True,
        add_to_history: bool = False,
    ):
        """
        Unified method to load and display an animal in Today view.

        Args:
            taxon_id: The ID of the taxon to load
            source: Source of the request ("history", "favorite", "search") for logging
            enrich: Whether to enrich the animal with external API data
            add_to_history: Whether to add the animal to history after loading
        """
        # Switch to Today view
        self.nav_bar.selected_index = 0
        self.show_discovery_view()

        # Show loading in today view
        self.discovery_view.today_animal_container.controls = [
            LoadingWidget(subtitle="Chargement de l'animal...")
        ]
        self.page.update()
        await asyncio.sleep(0.1)

        try:
            # Fetch animal
            def fetch_animal():
                repo = self.state.repository
                return repo.get_by_id(taxon_id, enrich=enrich)

            animal = await asyncio.to_thread(fetch_animal)

            # Update offline banner after load
            self._update_offline_banner()

            if animal:
                self.discovery_view.current_animal = animal
                self.discovery_view.current_image_index = 0  # Reset carousel

                logger.info(f"Loading animal ({source}): {animal.display_name}")

                # Display animal in Today view
                self.discovery_view._display_animal(animal)

                # Add to history if requested
                if add_to_history:
                    repo = self.state.repository
                    repo.add_to_history(taxon_id, command=source)
            else:
                # Animal not found
                self.discovery_view.today_animal_container.controls = [
                    ErrorWidget(title="Animal introuvable")
                ]
                self.page.update()

        except Exception as error:
            logger.error(f"Error loading animal from {source} (ID {taxon_id}): {error}")
            traceback.print_exc()

            # Show error in UI
            self.discovery_view.today_animal_container.controls = [
                ErrorWidget(title="Erreur lors du chargement", details=str(error))
            ]
            self.page.update()

    def on_favorite_toggle(self, taxon_id: int, is_favorite: bool):
        """Handle favorite toggle from any view."""
        try:
            repo = self.state.repository

            if is_favorite:
                # Remove from favorites
                success = repo.remove_favorite(taxon_id)
                if success:
                    self.page.show_dialog(
                        ft.SnackBar(ft.Text("Retiré des favoris"), show_close_icon=True)
                    )
            else:
                # Add to favorites
                success = repo.add_favorite(taxon_id)
                if success:
                    self.page.show_dialog(
                        ft.SnackBar(ft.Text("Ajouté aux favoris"), show_close_icon=True)
                    )

        except Exception as error:
            logger.error(f"Error in on_favorite_toggle: {error}")
            traceback.print_exc()

            # Show error snackbar
            self.page.show_dialog(
                ft.SnackBar(
                    ft.Text(f"Erreur: {str(error)}"),
                    bgcolor=ft.Colors.ERROR,
                    show_close_icon=True,
                )
            )

    def _update_offline_banner(self):
        """Update offline banner visibility and content based on connectivity state."""
        connectivity = self.state.repository.connectivity
        force_offline = connectivity.force_offline
        is_online = connectivity.is_online

        if force_offline:
            # Voluntary offline mode — no retry button
            banner_row = self.offline_banner.content
            banner_row.controls = [
                ft.Icon(ft.Icons.WIFI_OFF, color=ft.Colors.WHITE, size=18),
                ft.Text("Mode hors ligne activé", color=ft.Colors.WHITE, size=13),
            ]
            self.offline_banner.visible = True
        elif not is_online:
            # Connection lost — show retry button
            banner_row = self.offline_banner.content
            banner_row.controls = [
                ft.Icon(ft.Icons.WIFI_OFF, color=ft.Colors.WHITE, size=18),
                ft.Text(
                    "Mode hors ligne — données en cache uniquement",
                    color=ft.Colors.WHITE,
                    size=13,
                ),
                ft.Button(
                    "Réessayer",
                    on_click=self._retry_connection,
                    style=ft.ButtonStyle(color=ft.Colors.WHITE),
                ),
            ]
            self.offline_banner.visible = True
        else:
            # Online — hide banner
            self.offline_banner.visible = False

        self.page.update()

    async def _retry_connection(self, e=None):
        """Retry network connection and reload current animal if back online."""
        connectivity = self.state.repository.connectivity
        was_offline = not connectivity.is_online
        await asyncio.to_thread(connectivity.check)
        self._update_offline_banner()

        if (
            was_offline
            and connectivity.is_online
            and self.discovery_view.current_animal
        ):
            # Reload current animal with enrichment
            taxon_id = self.discovery_view.current_animal.taxon.taxon_id
            await self._load_and_display_animal(
                taxon_id=taxon_id, source="retry", enrich=True, add_to_history=False
            )

    def _on_notification_clicked(self, animal):
        """Handle notification click: bring window to front and show the notified animal."""
        self.nav_bar.selected_index = 0
        self.discovery_view.current_animal = animal
        self.show_discovery_view()
        self.state.repository.add_to_history(
            animal.taxon.taxon_id, command="notification"
        )
        self.page.run_task(self.page.window.to_front)

    def cleanup(self):
        """Clean up resources."""
        self.notification_service.stop()
        self.state.close_repository()
