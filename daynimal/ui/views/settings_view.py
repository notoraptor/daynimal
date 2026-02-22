"""Settings view for app configuration and credits."""

import asyncio
import logging
import traceback
from datetime import datetime

import flet as ft

from daynimal.ui.state import AppState
from daynimal.ui.views.base import BaseView

logger = logging.getLogger("daynimal")


def _format_notification_summary(enabled, start, period_h, period_m):
    """Format a human-readable notification summary.

    Args:
        enabled: Whether notifications are enabled.
        start: Start datetime.
        period_h: Period hours.
        period_m: Period minutes.

    Returns:
        Summary string like "Activées — toutes les 1h 30min depuis le 21/02/2026 à 08:00"
    """
    if not enabled:
        return "Désactivées"

    # Format period
    if period_h > 0 and period_m > 0:
        period_text = f"{period_h}h {period_m:02d}min"
    elif period_h > 0:
        period_text = f"{period_h}h"
    else:
        period_text = f"{period_m}min"

    date_str = start.strftime("%d/%m/%Y")
    time_str = start.strftime("%H:%M")

    return f"Activées — toutes les {period_text} depuis le {date_str} à {time_str}"


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
        self.view_title = "⚙️ Paramètres"
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
                auto_load = repo.get_setting("auto_load_on_start", "true") == "true"
                stats = repo.get_stats()
                return theme_mode, force_offline, auto_load, stats

            theme_mode, force_offline, auto_load, stats = await asyncio.to_thread(
                fetch_data
            )

            # Fetch notification settings
            def fetch_notification_settings():
                repo = self.app_state.repository
                notif_enabled = (
                    repo.get_setting("notifications_enabled", "false") == "true"
                )
                notif_start_raw = repo.get_setting("notification_start", None)
                notif_period_raw = repo.get_setting("notification_period", "24:00")

                # Parse start datetime
                if notif_start_raw:
                    try:
                        notif_start = datetime.fromisoformat(notif_start_raw)
                    except (ValueError, TypeError):
                        notif_start = datetime.now().replace(
                            hour=8, minute=0, second=0, microsecond=0
                        )
                else:
                    # Legacy fallback
                    legacy_time = repo.get_setting("notification_time", "08:00")
                    try:
                        parts = legacy_time.split(":")
                        hour = int(parts[0])
                        minute = int(parts[1]) if len(parts) > 1 else 0
                    except (ValueError, AttributeError, IndexError):
                        hour, minute = 8, 0
                    notif_start = datetime.now().replace(
                        hour=hour, minute=minute, second=0, microsecond=0
                    )

                # Parse period "HH:MM"
                try:
                    p_parts = notif_period_raw.split(":")
                    period_hours = int(p_parts[0])
                    period_minutes = int(p_parts[1]) if len(p_parts) > 1 else 0
                except (ValueError, AttributeError, IndexError):
                    period_hours, period_minutes = 24, 0

                return notif_enabled, notif_start, period_hours, period_minutes

            (
                notif_enabled,
                notif_start,
                period_hours,
                period_minutes,
            ) = await asyncio.to_thread(fetch_notification_settings)
            is_dark = theme_mode == "dark"

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
                        ft.Switch(
                            label="Charger un animal au démarrage",
                            value=auto_load,
                            on_change=self._on_auto_load_toggle,
                        ),
                    ],
                    spacing=10,
                ),
                padding=ft.Padding(left=20, right=20, top=10, bottom=10),
            )

            # Notifications section — read-only summary + "Modifier" button
            summary_text = _format_notification_summary(
                notif_enabled, notif_start, period_hours, period_minutes
            )

            notifications_section = ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Text("Notifications", size=18, weight=ft.FontWeight.BOLD),
                        ft.Text(summary_text, size=14),
                        ft.Button(
                            "Modifier",
                            icon=ft.Icons.SETTINGS,
                            on_click=self._open_notification_dialog,
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

    def _on_auto_load_toggle(self, e):
        """Handle auto-load on start toggle."""
        try:
            is_enabled = e.control.value
            repo = self.app_state.repository
            repo.set_setting("auto_load_on_start", "true" if is_enabled else "false")
            logger.info(
                f"Auto-load on start: {'enabled' if is_enabled else 'disabled'}"
            )
        except Exception as error:
            logger.error(f"Error in _on_auto_load_toggle: {error}")
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

    def _open_notification_dialog(self, e):
        """Open a dialog with the full notification configuration form."""
        try:
            repo = self.app_state.repository

            # Read current values
            notif_enabled = repo.get_setting("notifications_enabled", "false") == "true"
            notif_start_raw = repo.get_setting("notification_start", None)
            notif_period_raw = repo.get_setting("notification_period", "24:00")

            # Parse start datetime
            if notif_start_raw:
                try:
                    notif_start = datetime.fromisoformat(notif_start_raw)
                except (ValueError, TypeError):
                    notif_start = datetime.now().replace(
                        hour=8, minute=0, second=0, microsecond=0
                    )
            else:
                legacy_time = repo.get_setting("notification_time", "08:00")
                try:
                    parts = legacy_time.split(":")
                    hour = int(parts[0])
                    minute = int(parts[1]) if len(parts) > 1 else 0
                except (ValueError, AttributeError, IndexError):
                    hour, minute = 8, 0
                notif_start = datetime.now().replace(
                    hour=hour, minute=minute, second=0, microsecond=0
                )

            # Parse period
            try:
                p_parts = notif_period_raw.split(":")
                period_hours = int(p_parts[0])
                period_minutes = int(p_parts[1]) if len(p_parts) > 1 else 0
            except (ValueError, AttributeError, IndexError):
                period_hours, period_minutes = 24, 0

            # Create dialog controls
            self._dlg_enabled_switch = ft.Switch(
                label="Activer les notifications", value=notif_enabled
            )

            self._dlg_start_date = notif_start.date()
            self._dlg_start_date_button = ft.Button(
                f"{notif_start.strftime('%d/%m/%Y')}",
                icon=ft.Icons.CALENDAR_TODAY,
                on_click=self._on_dlg_date_pick,
            )

            hour_options = [ft.dropdown.Option(f"{h:02d}") for h in range(24)]
            minute_options = [ft.dropdown.Option(f"{m:02d}") for m in range(60)]

            self._dlg_hour_dropdown = ft.Dropdown(
                value=f"{notif_start.hour:02d}",
                options=hour_options,
                width=100,
                label="Heure",
            )
            self._dlg_minute_dropdown = ft.Dropdown(
                value=f"{notif_start.minute:02d}",
                options=minute_options,
                width=100,
                label="Min.",
            )

            self._dlg_period_hours_field = ft.TextField(
                value=str(period_hours),
                label="Heures",
                width=100,
                keyboard_type=ft.KeyboardType.NUMBER,
            )
            self._dlg_period_minutes_field = ft.TextField(
                value=str(period_minutes),
                label="Minutes",
                width=100,
                keyboard_type=ft.KeyboardType.NUMBER,
            )

            dialog = ft.AlertDialog(
                title=ft.Text("Configuration des notifications"),
                content=ft.Container(
                    content=ft.Column(
                        controls=[
                            self._dlg_enabled_switch,
                            ft.Text(
                                "Date de départ", size=14, weight=ft.FontWeight.W_500
                            ),
                            self._dlg_start_date_button,
                            ft.Row(
                                controls=[
                                    self._dlg_hour_dropdown,
                                    self._dlg_minute_dropdown,
                                ],
                                spacing=10,
                            ),
                            ft.Text("Période", size=14, weight=ft.FontWeight.W_500),
                            ft.Row(
                                controls=[
                                    self._dlg_period_hours_field,
                                    self._dlg_period_minutes_field,
                                ],
                                spacing=10,
                            ),
                        ],
                        spacing=10,
                        scroll=ft.ScrollMode.AUTO,
                    ),
                    width=280,
                ),
                actions=[
                    ft.Button("Annuler", on_click=self._on_notif_dialog_cancel),
                    ft.Button("Sauvegarder", on_click=self._on_notif_dialog_save),
                ],
                modal=True,
            )
            self.page.show_dialog(dialog)

        except Exception as error:
            logger.error(f"Error in _open_notification_dialog: {error}")
            traceback.print_exc()

    def _on_dlg_date_pick(self, e):
        """Open DatePicker dialog for notification start date inside the dialog."""
        try:
            picker = ft.DatePicker(
                value=self._dlg_start_date, on_change=self._on_dlg_date_change
            )
            self.page.show_dialog(picker)
        except Exception as error:
            logger.error(f"Error in _on_dlg_date_pick: {error}")
            traceback.print_exc()

    def _on_dlg_date_change(self, e):
        """Handle date picker selection inside the notification dialog."""
        try:
            if e.control.value:
                selected = e.control.value
                if isinstance(selected, datetime):
                    self._dlg_start_date = selected.date()
                else:
                    self._dlg_start_date = selected
                self._dlg_start_date_button.text = self._dlg_start_date.strftime(
                    "%d/%m/%Y"
                )
                self.page.update()
        except Exception as error:
            logger.error(f"Error in _on_dlg_date_change: {error}")
            traceback.print_exc()

    def _on_notif_dialog_save(self, e):
        """Save all notification settings at once and close the dialog."""
        try:
            repo = self.app_state.repository

            # Read values from dialog controls
            is_enabled = self._dlg_enabled_switch.value

            hour = self._dlg_hour_dropdown.value or "08"
            minute = self._dlg_minute_dropdown.value or "00"
            date_str = self._dlg_start_date.isoformat()
            start_str = f"{date_str}T{hour}:{minute}"

            hours_str = self._dlg_period_hours_field.value or "0"
            minutes_str = self._dlg_period_minutes_field.value or "0"
            try:
                p_hours = int(hours_str)
            except ValueError:
                p_hours = 0
            try:
                p_minutes = int(minutes_str)
            except ValueError:
                p_minutes = 0
            if p_hours == 0 and p_minutes == 0:
                p_minutes = 1
            period_str = f"{p_hours}:{p_minutes:02d}"

            # Save all at once
            repo.set_setting("notifications_enabled", "true" if is_enabled else "false")
            repo.set_setting("notification_start", start_str)
            repo.set_setting("notification_period", period_str)

            # Restart or stop the notification service
            notif_service = getattr(self.app_state, "notification_service", None)
            if notif_service:
                if is_enabled:
                    notif_service.start()  # stop() + schedule
                else:
                    notif_service.stop()

            logger.info(
                f"Notifications saved: enabled={is_enabled}, "
                f"start={start_str}, period={period_str}"
            )

            self.page.pop_dialog()
            asyncio.create_task(self._load_settings())

        except Exception as error:
            logger.error(f"Error in _on_notif_dialog_save: {error}")
            traceback.print_exc()

    def _on_notif_dialog_cancel(self, e):
        """Close the notification dialog without saving."""
        self.page.pop_dialog()
