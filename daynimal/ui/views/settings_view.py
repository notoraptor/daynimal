"""Settings view for app configuration and credits."""

import asyncio
import traceback

import flet as ft

from daynimal.ui.state import AppState
from daynimal.ui.views.base import BaseView


class SettingsView(BaseView):
    """View for app settings, preferences, and credits."""

    def __init__(
        self,
        page: ft.Page,
        app_state: AppState | None = None,
        debugger=None,
    ):
        """
        Initialize SettingsView.

        Args:
            page: Flet page instance
            app_state: Shared application state
            debugger: Optional debugger instance for logging
        """
        super().__init__(page, app_state, debugger)
        self.settings_container = ft.Column(controls=[], spacing=0)

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
                stats = repo.get_stats()
                return theme_mode, stats

            theme_mode, stats = await asyncio.to_thread(fetch_data)
            is_dark = theme_mode == "dark"

            # Header
            header = ft.Container(
                content=ft.Row(
                    controls=[
                        ft.Icon(ft.Icons.SETTINGS, size=32, color=ft.Colors.PRIMARY),
                        ft.Text(
                            "Paramètres",
                            size=28,
                            weight=ft.FontWeight.BOLD,
                            color=ft.Colors.PRIMARY,
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
                padding=20,
            )

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
                            "📚 GBIF - Global Biodiversity Information Facility", size=12
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

            # Update content
            self.settings_container.controls = [
                header,
                ft.Divider(),
                app_info,
                ft.Divider(),
                preferences,
                ft.Divider(),
                credits,
                ft.Divider(),
                db_info,
            ]

        except Exception as error:
            error_msg = f"Error loading settings: {error}"
            error_traceback = traceback.format_exc()

            if self.debugger:
                self.debugger.log_error("load_settings", error)
                self.debugger.logger.error(f"Full traceback:\n{error_traceback}")
            else:
                print(f"ERROR: {error_msg}")
                print(f"Traceback:\n{error_traceback}")

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

            if self.debugger:
                self.debugger.logger.info(f"Theme changed to: {new_theme}")

        except Exception as error:
            error_msg = f"Error toggling theme: {error}"
            error_traceback = traceback.format_exc()

            if self.debugger:
                self.debugger.log_error("on_theme_toggle", error)
                self.debugger.logger.error(f"Full traceback:\n{error_traceback}")
            else:
                print(f"ERROR: {error_msg}")
                print(f"Traceback:\n{error_traceback}")
