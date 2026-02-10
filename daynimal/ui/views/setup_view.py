"""Setup view for first-launch database installation."""

import asyncio

import flet as ft

from daynimal.ui.views.base import BaseView


class SetupView(BaseView):
    """View displayed on first launch when no database is found.

    Shows a welcome message and allows the user to download and install
    the minimal database from GitHub Releases.
    """

    def __init__(self, page, app_state, on_setup_complete, debugger=None):
        """Initialize SetupView.

        Args:
            page: Flet page instance.
            app_state: Shared application state.
            on_setup_complete: Callback when setup finishes successfully.
            debugger: Optional debugger for logging.
        """
        super().__init__(page, app_state, debugger)
        self.on_setup_complete = on_setup_complete

        # UI elements
        self.install_button = ft.ElevatedButton(
            text="Installer la base de données",
            icon=ft.Icons.DOWNLOAD,
            on_click=self._on_install_click,
            style=ft.ButtonStyle(padding=20),
        )
        self.progress_bar = ft.ProgressBar(visible=False, width=400)
        self.status_text = ft.Text("", size=14, visible=False)
        self.error_container = ft.Column(controls=[], visible=False)

    def build(self) -> ft.Control:
        """Build the setup view UI."""
        self.container.controls = [
            ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Icon(ft.Icons.PETS, size=80, color=ft.Colors.PRIMARY),
                        ft.Text(
                            "Bienvenue dans Daynimal !",
                            size=28,
                            weight=ft.FontWeight.BOLD,
                            text_align=ft.TextAlign.CENTER,
                        ),
                        ft.Text(
                            "Découvrez un animal chaque jour.\n"
                            "Pour commencer, installez la base de données (~13 MB).",
                            size=16,
                            text_align=ft.TextAlign.CENTER,
                            color=ft.Colors.GREY_600,
                        ),
                        ft.Container(height=20),
                        self.install_button,
                        self.progress_bar,
                        self.status_text,
                        self.error_container,
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=10,
                ),
                padding=40,
                alignment=ft.alignment.center,
                expand=True,
            )
        ]
        return self.container

    def _on_install_click(self, e):
        """Handle install button click — launch async setup."""
        asyncio.create_task(self._start_setup())

    async def _start_setup(self):
        """Run the download and setup process."""
        # Show progress, hide button and errors
        self.install_button.visible = False
        self.progress_bar.visible = True
        self.progress_bar.value = None  # Indeterminate
        self.status_text.visible = True
        self.status_text.value = "Préparation..."
        self.error_container.visible = False
        self.page.update()
        await asyncio.sleep(0.1)

        try:
            from daynimal.db.first_launch import download_and_setup_db

            await asyncio.to_thread(download_and_setup_db, self._update_progress)

            # Success
            self.status_text.value = "Installation terminée !"
            self.progress_bar.value = 1.0
            self.page.update()
            await asyncio.sleep(0.5)

            self.on_setup_complete()

        except Exception as error:
            self.log_error("setup", error)
            self.progress_bar.visible = False
            self.status_text.visible = False
            self.error_container.visible = True
            self.error_container.controls = [
                ft.Icon(ft.Icons.ERROR, size=40, color=ft.Colors.ERROR),
                ft.Text(
                    "Erreur lors de l'installation",
                    size=18,
                    color=ft.Colors.ERROR,
                ),
                ft.Text(str(error), size=12, color=ft.Colors.GREY_600),
                ft.ElevatedButton(
                    text="Réessayer",
                    icon=ft.Icons.REFRESH,
                    on_click=self._on_install_click,
                ),
            ]
            self.install_button.visible = False
            self.page.update()

    def _update_progress(self, stage: str, progress: float | None):
        """Update UI with progress from download_and_setup_db."""
        stage_labels = {
            "download_manifest": "Téléchargement du manifeste...",
            "download_taxa": "Téléchargement des taxons...",
            "download_vernacular": "Téléchargement des noms vernaculaires...",
            "decompress": "Décompression...",
            "build_db": "Construction de la base de données...",
            "build_fts": "Indexation pour la recherche...",
            "cleanup": "Nettoyage...",
        }
        self.status_text.value = stage_labels.get(stage, stage)
        self.progress_bar.value = progress  # None = indeterminate
        try:
            self.page.update()
        except Exception:
            pass

    async def refresh(self):
        """No-op refresh."""
        pass
