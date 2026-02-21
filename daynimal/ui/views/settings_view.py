"""Settings view for app configuration and credits."""

import asyncio
import logging
import traceback

import flet as ft

from daynimal.ui.components.widgets import view_header
from daynimal.ui.state import AppState
from daynimal.ui.views.base import BaseView

logger = logging.getLogger("daynimal")


class SettingsView(BaseView):
    """View for app settings, preferences, and credits."""

    def __init__(
        self,
        page: ft.Page,
        app_state: AppState | None = None,
        on_offline_change: callable = None,
    ):
        """
        Initialize SettingsView.

        Args:
            page: Flet page instance
            app_state: Shared application state
            on_offline_change: Callback when offline mode is toggled
        """
        super().__init__(page, app_state)
        self.on_offline_change = on_offline_change
        self.settings_container = ft.Column(controls=[])

    def build(self) -> ft.Control:
        """Build the settings view UI."""
        # Load settings asynchronously
        asyncio.create_task(self._load_settings())

        return self.settings_container

    async def _load_settings(self):
        """Load settings and build the UI."""
        try:
            # Fetch theme setting and stats
            def fetch_data():
                repo = self.app_state.repository
                theme_mode = repo.get_setting("theme_mode", "light")
                force_offline = repo.get_setting("force_offline", "false") == "true"
                stats = repo.get_stats()
                return theme_mode, force_offline, stats

            theme_mode, force_offline, stats = await asyncio.to_thread(fetch_data)

            # Fetch notification settings
            def fetch_notification_settings():
                repo = self.app_state.repository
                notif_enabled = (
                    repo.get_setting("notifications_enabled", "false") == "true"
                )
                notif_time = repo.get_setting("notification_time", "08:00")
                return notif_enabled, notif_time

            notif_enabled, notif_time = await asyncio.to_thread(
                fetch_notification_settings
            )
            is_dark = theme_mode == "dark"

            # Header
            header = view_header("⚙️ Paramètres")

            # App info section
            app_info = ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Text(
                            "🦁 Daynimal",
                            size=24,
                            weight=ft.FontWeight.BOLD,
                            text_align=ft.TextAlign.CENTER,
                        ),
                        ft.Text(
                            "Découverte quotidienne d'animaux",
                            size=14,
                            color=ft.Colors.GREY_700,
                            text_align=ft.TextAlign.CENTER,
                        ),
                        ft.Text(
                            "Version 0.2.0 - Février 2026",
                            size=12,
                            color=ft.Colors.GREY_500,
                            text_align=ft.TextAlign.CENTER,
                        ),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=5,
                ),
                padding=20,
            )

            # Preferences section
            preferences = ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Text("Préférences", size=18, weight=ft.FontWeight.BOLD),
                        ft.Switch(
                            label="Thème sombre",
                            value=is_dark,
                            on_change=self._on_theme_toggle,
                        ),
                        ft.Switch(
                            label="Forcer le mode hors ligne",
                            value=force_offline,
                            on_change=self._on_offline_toggle,
                        ),
                    ],
                    spacing=10,
                ),
                padding=ft.Padding(left=20, right=20, top=10, bottom=10),
            )

            # Notifications section
            hour_options = [ft.dropdown.Option(f"{h:02d}:00") for h in range(24)]
            notifications_section = ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Text("Notifications", size=18, weight=ft.FontWeight.BOLD),
                        ft.Switch(
                            label="Notification quotidienne",
                            value=notif_enabled,
                            on_change=self._on_notifications_toggle,
                        ),
                        ft.Row(
                            controls=[
                                ft.Text("Heure de notification :", size=14),
                                ft.Dropdown(
                                    value=notif_time,
                                    options=hour_options,
                                    width=120,
                                    on_select=self._on_notification_time_change,
                                ),
                            ],
                            spacing=10,
                        ),
                    ],
                    spacing=10,
                ),
                padding=ft.Padding(left=20, right=20, top=10, bottom=10),
            )

            # Credits section
            credits = ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Text(
                            "Crédits et sources de données",
                            size=18,
                            weight=ft.FontWeight.BOLD,
                        ),
                        ft.Text(
                            "📚 GBIF - Global Biodiversity Information Facility",
                            size=12,
                        ),
                        ft.Text(
                            "   Taxonomie : CC-BY 4.0",
                            size=10,
                            color=ft.Colors.GREY_600,
                        ),
                        ft.Text("🌐 Wikidata - Données structurées", size=12),
                        ft.Text(
                            "   Propriétés : CC0 (domaine public)",
                            size=10,
                            color=ft.Colors.GREY_600,
                        ),
                        ft.Text("📖 Wikipedia - Descriptions", size=12),
                        ft.Text(
                            "   Articles : CC-BY-SA 3.0",
                            size=10,
                            color=ft.Colors.GREY_600,
                        ),
                        ft.Text("🖼️ Wikimedia Commons - Images", size=12),
                        ft.Text(
                            "   Photos : Voir attributions individuelles",
                            size=10,
                            color=ft.Colors.GREY_600,
                        ),
                        ft.Text("📷 GBIF Media - Photos d'occurrences", size=12),
                        ft.Text(
                            "   Photos : CC0, CC-BY, CC-BY-SA",
                            size=10,
                            color=ft.Colors.GREY_600,
                        ),
                        ft.Text("🦎 PhyloPic - Silhouettes", size=12),
                        ft.Text(
                            "   Silhouettes : CC0, CC-BY, CC-BY-SA",
                            size=10,
                            color=ft.Colors.GREY_600,
                        ),
                    ],
                    spacing=8,
                ),
                padding=ft.Padding(left=20, right=20, top=10, bottom=10),
            )

            # Database stats
            db_info = ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Text(
                            "Base de données locale", size=18, weight=ft.FontWeight.BOLD
                        ),
                        ft.Text(
                            f"🔢 {stats['species_count']:,} espèces".replace(",", " "),
                            size=12,
                        ),
                        ft.Text(
                            f"🌍 {stats['vernacular_names']:,} noms vernaculaires".replace(
                                ",", " "
                            ),
                            size=12,
                        ),
                        ft.Text(
                            f"✨ {stats['enriched_count']} espèces enrichies", size=12
                        ),
                    ],
                    spacing=8,
                ),
                padding=ft.Padding(left=20, right=20, top=10, bottom=20),
            )

            # Image cache section
            cache_size_bytes = self.app_state.image_cache.get_cache_size()
            if cache_size_bytes < 1024 * 1024:
                cache_size_text = f"{cache_size_bytes / 1024:.1f} Ko"
            else:
                cache_size_text = f"{cache_size_bytes / (1024 * 1024):.1f} Mo"

            cache_section = ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Text("Cache d'images", size=18, weight=ft.FontWeight.BOLD),
                        ft.Text(f"Taille du cache : {cache_size_text}", size=12),
                        ft.Button(
                            "Vider le cache",
                            icon=ft.Icons.DELETE,
                            on_click=self._on_clear_cache,
                        ),
                    ],
                    spacing=10,
                ),
                padding=ft.Padding(left=20, right=20, top=10, bottom=10),
            )

            # Update content
            self.settings_container.controls = [
                header,
                ft.Divider(),
                app_info,
                ft.Divider(),
                preferences,
                ft.Divider(),
                notifications_section,
                ft.Divider(),
                cache_section,
                ft.Divider(),
                credits,
                ft.Divider(),
                db_info,
            ]

        except Exception as error:
            logger.error(f"Error loading settings: {error}")
            traceback.print_exc()

            # Show error
            self.settings_container.controls = [
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

    def _on_clear_cache(self, e):
        """Handle clear cache button click."""
        try:
            count = self.app_state.image_cache.clear()
            # Reload settings to update cache size display
            asyncio.create_task(self._load_settings())
            logger.info(f"Image cache cleared: {count} images removed")
        except Exception as error:
            logger.error(f"Error in clear_cache: {error}")
            traceback.print_exc()

    def _on_offline_toggle(self, e):
        """Handle forced offline mode toggle."""
        try:
            is_forced = e.control.value
            repo = self.app_state.repository
            repo.set_setting("force_offline", "true" if is_forced else "false")
            repo.connectivity.force_offline = is_forced

            logger.info(f"Force offline mode: {'enabled' if is_forced else 'disabled'}")

            if self.on_offline_change:
                self.on_offline_change()

        except Exception as error:
            logger.error(f"Error in on_offline_toggle: {error}")
            traceback.print_exc()

    def _on_theme_toggle(self, e):
        """Handle theme toggle switch change."""
        try:
            is_dark = e.control.value
            new_theme = "dark" if is_dark else "light"

            # Save to database
            self.app_state.repository.set_setting("theme_mode", new_theme)

            # Apply theme immediately
            self.page.theme_mode = ft.ThemeMode.DARK if is_dark else ft.ThemeMode.LIGHT
            self.page.update()

            logger.info(f"Theme changed to: {new_theme}")

        except Exception as error:
            logger.error(f"Error in on_theme_toggle: {error}")
            traceback.print_exc()

    def _on_notifications_toggle(self, e):
        """Handle notification toggle switch change."""
        try:
            is_enabled = e.control.value
            repo = self.app_state.repository
            repo.set_setting("notifications_enabled", "true" if is_enabled else "false")

            # Start/stop the notification service if available
            notif_service = getattr(self.app_state, "notification_service", None)
            if notif_service:
                if is_enabled:
                    notif_service.start()
                else:
                    notif_service.stop()

            logger.info(f"Notifications: {'enabled' if is_enabled else 'disabled'}")

        except Exception as error:
            logger.error(f"Error in on_notifications_toggle: {error}")
            traceback.print_exc()

    def _on_notification_time_change(self, e):
        """Handle notification time dropdown change."""
        try:
            new_time = e.control.value
            self.app_state.repository.set_setting("notification_time", new_time)

            logger.info(f"Notification time changed to: {new_time}")

        except Exception as error:
            logger.error(f"Error in on_notification_time_change: {error}")
            traceback.print_exc()
