"""Discovery view for displaying random animals."""

import asyncio
import logging
import traceback
from typing import Callable

import flet as ft

from daynimal.schemas import AnimalInfo, ImageSource
from daynimal.ui.components.animal_display import AnimalDisplay
from daynimal.ui.components.image_gallery_dialog import ImageGalleryDialog
from daynimal.ui.components.widgets import ErrorWidget, LoadingWidget
from daynimal.ui.state import AppState
from daynimal.ui.views.base import BaseView

logger = logging.getLogger("daynimal")


class TodayView(BaseView):
    """View for discovering random animals."""

    def __init__(
        self,
        page: ft.Page,
        app_state: AppState | None = None,
        on_favorite_toggle: Callable[[int, bool], None] | None = None,
    ):
        """
        Initialize TodayView.

        Args:
            page: Flet page instance
            app_state: Shared application state
            on_favorite_toggle: Callback when favorite button is clicked
                                (receives taxon_id, is_currently_favorite)
        """
        super().__init__(page, app_state)
        self.view_title = "🦁 Découverte"
        self.random_button = ft.IconButton(
            icon=ft.Icons.SHUFFLE,
            tooltip="Animal aléatoire",
            on_click=self._load_random_animal,
            style=ft.ButtonStyle(
                bgcolor=ft.Colors.BLUE,
                color=ft.Colors.WHITE,
                shape=ft.CircleBorder(),
            ),
        )
        self.view_title_actions = [self.random_button]
        self.on_favorite_toggle_callback = on_favorite_toggle
        self.on_load_complete: Callable[[], None] | None = None
        self.on_loading_change: Callable[[bool], None] | None = None
        self.today_animal_container = ft.Column(controls=[], spacing=10)
        self.current_animal: AnimalInfo | None = None

    def build(self) -> ft.Control:
        """Build the today view UI."""
        # Restore previous animal if available
        if self.current_animal is not None:
            self._display_animal(self.current_animal)
        else:
            # Show welcome message
            self.today_animal_container.controls = [
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Icon(
                                ft.Icons.FAVORITE, size=80, color=ft.Colors.PRIMARY
                            ),
                            ft.Text(
                                "Bienvenue sur Daynimal !",
                                size=24,
                                weight=ft.FontWeight.BOLD,
                                text_align=ft.TextAlign.CENTER,
                            ),
                            ft.Text(
                                "Découvrez un animal chaque jour",
                                size=16,
                                text_align=ft.TextAlign.CENTER,
                            ),
                            ft.Text(
                                "Cliquez sur le bouton 🔀 pour découvrir",
                                size=14,
                                color=ft.Colors.BLUE,
                                text_align=ft.TextAlign.CENTER,
                            ),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=15,
                    ),
                    padding=40,
                    expand=True,
                    alignment=ft.Alignment(0, 0),
                )
            ]

        # Content container
        content = ft.Column(
            controls=[
                ft.Container(content=self.today_animal_container, padding=20),
            ]
        )

        return content

    async def _load_random_animal(self, e):
        """Load a random animal."""
        logger.info("Loading random animal...")

        # Signal loading started
        if self.on_loading_change:
            self.on_loading_change(True)

        # Show loading message
        self.today_animal_container.controls = [
            LoadingWidget(subtitle="Récupération de l'animal aléatoire")
        ]
        self.page.update()

        # Small delay to ensure UI updates
        await asyncio.sleep(0.1)

        try:
            # Fetch animal from repository in a separate thread
            def fetch_animal():
                repo = self.app_state.repository
                animal = repo.get_random()
                repo.add_to_history(animal.taxon.taxon_id, command="random")
                return animal

            animal = await asyncio.to_thread(fetch_animal)
            self.current_animal = animal

            logger.info(f"Loading random animal: {animal.display_name}")

            # Display animal in Today view
            self._display_animal(animal)

            # Notify controller (e.g. to update offline banner)
            if self.on_load_complete:
                self.on_load_complete()

        except Exception as error:
            logger.error(f"Error in _load_random_animal: {error}")
            traceback.print_exc()

            # Show error
            self.today_animal_container.controls = [
                ErrorWidget(title="Erreur lors du chargement", details=str(error))
            ]

        finally:
            # Signal loading ended
            if self.on_loading_change:
                self.on_loading_change(False)
            # Update page after loading
            self.page.update()

    def _display_animal(self, animal: AnimalInfo):
        """Display animal information in the Today view."""
        controls = []

        # Hero image at the top
        images = animal.images or []
        if images:
            first_image = images[0]

            # Resolve image source: prefer local cache, fallback to URL
            image_src = first_image.url
            if self.app_state and self.app_state.image_cache:
                for url in [first_image.thumbnail_url, first_image.url]:
                    if url:
                        local_path = self.app_state.image_cache.get_local_path(url)
                        if local_path:
                            image_src = str(local_path)
                            break

            is_dark = self.page.theme_mode == ft.ThemeMode.DARK
            phylopic_color = ft.Colors.WHITE if is_dark else None

            image_controls: list[ft.Control] = [
                ft.Image(
                    src=image_src,
                    width=400,
                    height=300,
                    fit=ft.BoxFit.CONTAIN,
                    border_radius=10,
                    color=phylopic_color
                    if first_image.image_source == ImageSource.PHYLOPIC
                    else None,
                )
            ]

            # Silhouette badge (PhyloPic only)
            if first_image.image_source == ImageSource.PHYLOPIC:
                image_controls.append(
                    ft.Container(
                        content=ft.Text(
                            "Silhouette", size=10, color=ft.Colors.GREY_700
                        ),
                        bgcolor=ft.Colors.GREY_300,
                        border_radius=8,
                        padding=ft.Padding(left=8, right=8, top=2, bottom=2),
                    )
                )

            # Credit
            if first_image.author:
                image_controls.append(
                    ft.Text(
                        f"Crédit: {first_image.author} — {first_image.source_label}",
                        size=12,
                        color=ft.Colors.GREY_500,
                        italic=True,
                    )
                )

            # "More images" button
            if len(images) > 1:
                image_controls.append(
                    ft.Button(
                        f"Plus d'images ({len(images)} disponibles)...",
                        icon=ft.Icons.IMAGE,
                        on_click=lambda e, imgs=images, a=animal: self._open_gallery(
                            imgs, a
                        ),
                    )
                )

            controls.append(
                ft.Column(
                    controls=image_controls,
                    spacing=10,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                )
            )
            controls.append(ft.Divider())
        else:
            controls.append(
                ft.Container(
                    content=ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.IMAGE_NOT_SUPPORTED, size=18, color=ft.Colors.GREY_500),
                            ft.Text(
                                "Aucune image disponible",
                                size=14,
                                color=ft.Colors.GREY_500,
                                italic=True,
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=8,
                    ),
                    padding=ft.Padding(left=0, right=0, top=10, bottom=10),
                )
            )
            controls.append(ft.Divider())

        # Animal details (title, classification, description, etc.)
        animal_display = AnimalDisplay(animal)
        controls.extend(animal_display.build())

        # Insert favorite/share buttons after taxon ID (before first divider)
        # AnimalDisplay starts with: title, scientific name, ID, Divider, ...
        # The image section is already prepended, so offset by the image controls count
        image_offset = 2 if images else 0  # image column + divider
        first_divider_index = (image_offset + 3) if len(controls) > (image_offset + 3) else len(controls)

        # Favorite button
        is_favorite = (
            self.app_state.repository.is_favorite(animal.taxon.taxon_id)
            if self.app_state
            else False
        )

        favorite_button = ft.IconButton(
            icon=ft.Icons.FAVORITE if is_favorite else ft.Icons.FAVORITE_BORDER,
            icon_color=ft.Colors.RED if is_favorite else ft.Colors.GREY_500,
            icon_size=32,
            tooltip="Ajouter aux favoris" if not is_favorite else "Retirer des favoris",
            data=animal.taxon.taxon_id,
            on_click=self._on_favorite_toggle,
        )

        # Share buttons row
        share_buttons = []

        # Copy text button
        share_buttons.append(
            ft.IconButton(
                icon=ft.Icons.CONTENT_COPY,
                icon_size=24,
                tooltip="Copier le texte",
                on_click=self._on_copy_text,
            )
        )

        # Open Wikipedia button (disabled if no Wikipedia article)
        has_wikipedia = animal.wikipedia is not None
        share_buttons.append(
            ft.IconButton(
                icon=ft.Icons.LANGUAGE,
                icon_size=24,
                tooltip="Ouvrir Wikipedia",
                on_click=self._on_open_wikipedia if has_wikipedia else None,
                disabled=not has_wikipedia,
            )
        )

        # Open GBIF button (always available — taxon_id is always present)
        share_buttons.append(
            ft.IconButton(
                icon=ft.Icons.OPEN_IN_NEW,
                icon_size=24,
                tooltip="Ouvrir GBIF",
                on_click=self._on_open_gbif,
            )
        )

        controls.insert(
            first_divider_index,
            ft.Container(
                content=ft.Row(
                    controls=[
                        ft.Container(
                            content=ft.Text("Favori:", size=14),
                            data=animal.taxon.taxon_id,
                            on_click=self._on_favorite_toggle,
                            ink=True,
                        ),
                        favorite_button,
                        ft.Text("Partager:", size=14),
                        *share_buttons,
                    ],
                    spacing=5,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                padding=ft.Padding(top=10, bottom=10, left=0, right=0),
            ),
        )

        # Update container
        self.today_animal_container.controls = controls
        self.page.update()

    def _on_favorite_toggle(self, e):
        """Handle favorite button toggle."""
        if self.on_favorite_toggle_callback and self.current_animal:
            taxon_id = e.control.data
            is_favorite = (
                self.app_state.repository.is_favorite(taxon_id)
                if self.app_state
                else False
            )

            # Call the callback
            self.on_favorite_toggle_callback(taxon_id, is_favorite)

            # Refresh display
            if self.current_animal:
                self._display_animal(self.current_animal)

    def _open_gallery(self, images: list, animal: AnimalInfo):
        """Open the image gallery dialog."""
        if self.app_state:
            gallery = ImageGalleryDialog(
                images=images,
                image_cache=self.app_state.image_cache,
                page=self.page,
                animal_display_name=animal.display_name,
                animal_taxon_id=animal.taxon.taxon_id,
            )
            gallery.open()

    @staticmethod
    def _build_share_text(animal: AnimalInfo) -> str:
        """Build formatted share text for an animal."""
        scientific = animal.taxon.canonical_name or animal.taxon.scientific_name
        lines = [f"{animal.display_name} ({scientific})"]

        description = animal.description
        if description:
            if len(description) > 200:
                description = description[:197] + "..."
            lines.append(description)

        if animal.wikipedia:
            lines.append(f"\n{animal.wikipedia.article_url}")

        lines.append(
            "\nVia Daynimal — Sources : GBIF (CC-BY 4.0), Wikipedia (CC-BY-SA 4.0)"
        )

        return "\n".join(lines)

    async def _on_copy_text(self, e):
        """Copy formatted animal text to clipboard."""
        if not self.current_animal:
            return
        text = self._build_share_text(self.current_animal)
        await ft.Clipboard().set(text)
        self.page.show_dialog(
            ft.SnackBar(ft.Text("Texte copié !"), show_close_icon=True)
        )

    def _on_open_wikipedia(self, e):
        """Open Wikipedia article in default browser."""
        if not self.current_animal or not self.current_animal.wikipedia:
            return
        url = self.current_animal.wikipedia.article_url
        # page.launch_url() is async internally but wrapped in a sync
        # @deprecated decorator — use the underlying UrlLauncher directly
        self.page.run_task(ft.UrlLauncher().launch_url, url)

    def _on_open_gbif(self, e):
        """Open GBIF species page in default browser."""
        if not self.current_animal:
            return
        url = f"https://www.gbif.org/species/{self.current_animal.taxon.taxon_id}"
        self.page.run_task(ft.UrlLauncher().launch_url, url)
