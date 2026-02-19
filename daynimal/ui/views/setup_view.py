"""Setup view for first-launch database installation."""

import asyncio

import flet as ft

from daynimal.ui.views.base import BaseView


# Global progress weights for each stage (total = 1.0)
# Download stages ~70%, build stages ~30%
_STAGE_WEIGHTS = {
    "download_manifest": 0.02,
    "download_taxa": 0.35,
    "download_vernacular": 0.33,
    "decompress": 0.05,
    "build_db": 0.15,
    "build_fts": 0.08,
    "cleanup": 0.02,
}
_STAGE_ORDER = list(_STAGE_WEIGHTS.keys())


def _global_progress(stage: str, local_progress: float | None) -> float | None:
    """Convert a per-stage progress to a global 0.0–1.0 progress."""
    if stage not in _STAGE_WEIGHTS:
        return None
    # Sum weights of all completed stages before current one
    base = sum(_STAGE_WEIGHTS[s] for s in _STAGE_ORDER[: _STAGE_ORDER.index(stage)])
    weight = _STAGE_WEIGHTS[stage]
    if local_progress is None:
        # Indeterminate within this stage — return base (start of stage)
        return base
    return base + weight * local_progress


class SetupView(BaseView):
    """View displayed on first launch when no database is found.

    Three-step onboarding flow:
    1. Welcome screen with "Commencer" button
    2. Progress screen with real progress bar
    3. "Tout est prêt !" then auto-navigate to animal of the day
    """

    def __init__(self, page, app_state, on_setup_complete):
        """Initialize SetupView.

        Args:
            page: Flet page instance.
            app_state: Shared application state.
            on_setup_complete: Callback when setup finishes successfully.
        """
        super().__init__(page, app_state)
        self.on_setup_complete = on_setup_complete

    def build(self) -> ft.Control:
        """Build the setup view UI — shows welcome screen."""
        self._show_welcome()
        return self.container

    def _show_welcome(self):
        """Display welcome screen with Commencer button."""
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
                            "Découvrez un animal chaque jour.",
                            size=16,
                            text_align=ft.TextAlign.CENTER,
                            color=ft.Colors.GREY_600,
                        ),
                        ft.Container(height=30),
                        ft.Button(
                            "Commencer",
                            icon=ft.Icons.ARROW_FORWARD,
                            on_click=self._on_start_click,
                            style=ft.ButtonStyle(padding=20),
                        ),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=10,
                ),
                padding=40,
                alignment=ft.Alignment(0, 0),
                expand=True,
            )
        ]

    def _on_start_click(self, e):
        """Handle Commencer button click — launch async setup."""
        asyncio.create_task(self._start_setup())

    async def _start_setup(self):
        """Run the download and setup process with real progress."""
        # Switch to progress screen
        self.progress_bar = ft.ProgressBar(value=0, width=400)
        self.status_text = ft.Text(
            "Préparation des données sur les animaux...",
            size=14,
            color=ft.Colors.GREY_600,
        )
        self.container.controls = [
            ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Icon(ft.Icons.PETS, size=80, color=ft.Colors.PRIMARY),
                        ft.Text(
                            "Installation en cours",
                            size=24,
                            weight=ft.FontWeight.BOLD,
                            text_align=ft.TextAlign.CENTER,
                        ),
                        ft.Container(height=20),
                        self.progress_bar,
                        self.status_text,
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=10,
                ),
                padding=40,
                alignment=ft.Alignment(0, 0),
                expand=True,
            )
        ]
        self.page.update()
        await asyncio.sleep(0.1)

        try:
            from daynimal.db.first_launch import download_and_setup_db

            await asyncio.to_thread(download_and_setup_db, self._update_progress)

            # Show success screen with animation
            icon_container = ft.Container(
                content=ft.Icon(
                    ft.Icons.CHECK_CIRCLE, size=80, color=ft.Colors.PRIMARY
                ),
                scale=0,
                animate_scale=ft.Animation(800, ft.AnimationCurve.ELASTIC_OUT),
            )
            text_container = ft.Container(
                content=ft.Text(
                    "Tout est prêt !",
                    size=28,
                    weight=ft.FontWeight.BOLD,
                    text_align=ft.TextAlign.CENTER,
                ),
                opacity=0,
                animate_opacity=ft.Animation(600, ft.AnimationCurve.EASE_IN),
            )
            self.container.controls = [
                ft.Container(
                    content=ft.Column(
                        controls=[icon_container, text_container],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=10,
                    ),
                    padding=40,
                    alignment=ft.Alignment(0, 0),
                    expand=True,
                )
            ]
            self.page.update()
            await asyncio.sleep(0.05)

            # Trigger entrance animation
            icon_container.scale = 1
            text_container.opacity = 1
            self.page.update()
            await asyncio.sleep(1.5)

            # Subtle shrink before transition
            icon_container.animate_scale = ft.Animation(400, ft.AnimationCurve.EASE_IN)
            icon_container.scale = 0.8
            text_container.animate_opacity = ft.Animation(
                400, ft.AnimationCurve.EASE_IN
            )
            text_container.opacity = 0
            self.page.update()
            await asyncio.sleep(0.5)

            self.on_setup_complete()

        except Exception as error:
            self.log_error("setup", error)
            self.container.controls = [
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Icon(ft.Icons.ERROR, size=40, color=ft.Colors.ERROR),
                            ft.Text(
                                "Erreur lors de l'installation",
                                size=18,
                                color=ft.Colors.ERROR,
                            ),
                            ft.Text(str(error), size=12, color=ft.Colors.GREY_600),
                            ft.Button(
                                "Réessayer",
                                icon=ft.Icons.REFRESH,
                                on_click=self._on_start_click,
                            ),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=10,
                    ),
                    padding=40,
                    alignment=ft.Alignment(0, 0),
                    expand=True,
                )
            ]
            self.page.update()

    def _update_progress(self, stage: str, progress: float | None):
        """Update UI with weighted global progress."""
        stage_labels = {
            "download_manifest": "Connexion au serveur...",
            "download_taxa": "Téléchargement des données...",
            "download_vernacular": "Téléchargement des noms d'animaux...",
            "decompress": "Préparation des fichiers...",
            "build_db": "Construction de la base de connaissances...",
            "build_fts": "Activation de la recherche...",
            "cleanup": "Finalisation...",
        }
        self.status_text.value = stage_labels.get(stage, stage)
        global_val = _global_progress(stage, progress)
        if global_val is not None:
            self.progress_bar.value = global_val
        try:
            self.page.update()
        except Exception:
            pass

    async def refresh(self):
        """No-op refresh."""
        pass
