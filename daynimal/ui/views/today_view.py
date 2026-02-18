"""Today view for displaying the animal of the day or random animals."""

import asyncio
import traceback
from typing import Callable

import flet as ft

from daynimal.schemas import AnimalInfo
from daynimal.ui.components.animal_display import AnimalDisplay
from daynimal.ui.components.image_carousel import ImageCarousel
from daynimal.ui.components.widgets import view_header
from daynimal.ui.state import AppState
from daynimal.ui.views.base import BaseView


class TodayView(BaseView):
    """View for displaying the animal of the day or random animals."""

    def __init__(
        self,
        page: ft.Page,
        app_state: AppState | None = None,
        on_favorite_toggle: Callable[[int, bool], None] | None = None,
        debugger=None,
    ):
        """
        Initialize TodayView.

        Args:
            page: Flet page instance
            app_state: Shared application state
            on_favorite_toggle: Callback when favorite button is clicked
                                (receives taxon_id, is_currently_favorite)
            debugger: Optional debugger instance for logging
        """
        super().__init__(page, app_state, debugger)
        self.on_favorite_toggle_callback = on_favorite_toggle
        self.on_load_complete: Callable[[], None] | None = None
        self.today_animal_container = ft.Column(controls=[], spacing=10)
        self.current_animal: AnimalInfo | None = None
        self.current_image_index = 0

    def build(self) -> ft.Control:
        """Build the today view UI."""
        # Header
        header = view_header("🦁 Animal du jour")

        # Buttons
        today_button = ft.Button(
            "Animal du jour",
            icon=ft.Icons.CALENDAR_TODAY,
            on_click=self._load_today_animal,
            style=ft.ButtonStyle(color=ft.Colors.WHITE, bgcolor=ft.Colors.PRIMARY),
        )

        random_button = ft.Button(
            "Animal aléatoire",
            icon=ft.Icons.SHUFFLE,
            on_click=self._load_random_animal,
            style=ft.ButtonStyle(color=ft.Colors.WHITE, bgcolor=ft.Colors.BLUE),
        )

        button_row = ft.Row(
            controls=[today_button, random_button],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=10,
        )

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
                            ),
                            ft.Text("Découvrez un animal chaque jour", size=16),
                            ft.Text(
                                "Cliquez sur 'Animal du jour' pour commencer",
                                size=14,
                                color=ft.Colors.BLUE,
                            ),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=15,
                    ),
                    padding=40,
                )
            ]

        # Content container
        content = ft.Column(
            controls=[
                header,
                ft.Divider(),
                ft.Container(
                    content=button_row,
                    padding=ft.Padding(left=20, right=20, bottom=10, top=0),
                ),
                ft.Container(content=self.today_animal_container, padding=20),
            ]
        )

        return content

    async def _load_today_animal(self, e):
        """Load today's animal."""
        await self._load_animal_for_today_view("today")

    async def _load_random_animal(self, e):
        """Load a random animal."""
        await self._load_animal_for_today_view("random")

    async def _load_animal_for_today_view(self, mode: str):
        """Load and display an animal in the Today view."""
        if self.debugger:
            self.debugger.log_animal_load(mode)

        # Show loading message
        self.today_animal_container.controls = [
            ft.Container(
                content=ft.Column(
                    controls=[
                        ft.ProgressRing(width=60, height=60),
                        ft.Text(
                            "Chargement en cours...", size=18, weight=ft.FontWeight.BOLD
                        ),
                        ft.Text(
                            f"Récupération de l'animal {'du jour' if mode == 'today' else 'aléatoire'}",
                            size=14,
                        ),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=20,
                ),
                padding=40,
            )
        ]
        self.page.update()

        # Small delay to ensure UI updates
        await asyncio.sleep(0.1)

        try:
            # Fetch animal from repository in a separate thread
            def fetch_animal():
                repo = self.app_state.repository
                if mode == "today":
                    animal = repo.get_animal_of_the_day()
                    repo.add_to_history(animal.taxon.taxon_id, command="today")
                else:  # random
                    animal = repo.get_random()
                    repo.add_to_history(animal.taxon.taxon_id, command="random")
                return animal

            animal = await asyncio.to_thread(fetch_animal)
            self.current_animal = animal
            self.current_image_index = 0  # Reset carousel to first image

            if self.debugger:
                self.debugger.log_animal_load(mode, animal.display_name)

            # Display animal in Today view
            self._display_animal(animal)

            # Notify controller (e.g. to update offline banner)
            if self.on_load_complete:
                self.on_load_complete()

        except Exception as error:
            # Log error with full traceback
            error_msg = f"Error in load_animal_for_today_view ({mode}): {error}"
            error_traceback = traceback.format_exc()

            if self.debugger:
                self.debugger.log_error(f"load_animal_for_today_view ({mode})", error)
                self.debugger.logger.error(f"Full traceback:\n{error_traceback}")
            else:
                # Fallback: print to console if no debugger
                print(f"ERROR: {error_msg}")
                print(f"Traceback:\n{error_traceback}")

            # Show error
            self.today_animal_container.controls = [
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Icon(ft.Icons.ERROR, size=60, color=ft.Colors.ERROR),
                            ft.Text(
                                "Erreur lors du chargement",
                                size=20,
                                weight=ft.FontWeight.BOLD,
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
            # Update page after loading
            self.page.update()

    def _display_animal(self, animal: AnimalInfo):
        """Display animal information in the Today view."""
        controls = []

        # Use AnimalDisplay for animal details
        animal_display = AnimalDisplay(animal)
        controls.extend(animal_display.build())

        # Insert favorite button after taxon ID (before first divider)
        # Find first divider index (should be at index 3)
        first_divider_index = 3 if len(controls) > 3 else len(controls)

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

        controls.insert(
            first_divider_index,
            ft.Container(
                content=ft.Row(
                    controls=[
                        favorite_button,
                        ft.Text(
                            "Ajouter aux favoris"
                            if not is_favorite
                            else "Retirer des favoris",
                            size=14,
                        ),
                    ],
                    spacing=5,
                ),
                padding=ft.Padding(top=10, bottom=10, left=0, right=0),
            ),
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

        # Copy image path button (disabled if no cached image)
        has_cached_image = False
        if animal.images and self.app_state and self.app_state.image_cache:
            first_image = animal.images[0]
            url = first_image.thumbnail_url or first_image.url
            local_path = self.app_state.image_cache.get_local_path(url)
            has_cached_image = local_path is not None

        share_buttons.append(
            ft.IconButton(
                icon=ft.Icons.IMAGE,
                icon_size=24,
                tooltip="Copier le chemin de l'image",
                on_click=self._on_copy_image if has_cached_image else None,
                disabled=not has_cached_image,
            )
        )

        controls.insert(
            first_divider_index + 1,
            ft.Container(
                content=ft.Row(
                    controls=[
                        ft.Text("Partager :", size=14, weight=ft.FontWeight.BOLD),
                        *share_buttons,
                    ],
                    spacing=5,
                ),
                padding=ft.Padding(top=0, bottom=10, left=0, right=0),
            ),
        )

        # Add images section with carousel
        controls.append(ft.Divider())
        controls.append(ft.Text("Images", size=20, weight=ft.FontWeight.BOLD))

        # Use ImageCarousel for image display
        carousel = ImageCarousel(
            images=animal.images or [],
            current_index=self.current_image_index,
            on_index_change=self._on_image_index_change,
            animal_display_name=animal.display_name,
            animal_taxon_id=animal.taxon.taxon_id,
            image_cache=self.app_state.image_cache,
        )
        controls.append(carousel.build())

        controls.append(ft.Divider())

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

    def _on_image_index_change(self, new_index: int):
        """Handle image index change in carousel."""
        self.current_image_index = new_index
        # Redraw to update carousel
        if self.current_animal:
            self._display_animal(self.current_animal)

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
        self.page.set_clipboard(text)
        self.page.open(ft.SnackBar(content=ft.Text("Texte copié !")))
        self.page.update()

    def _on_open_wikipedia(self, e):
        """Open Wikipedia article in default browser."""
        if not self.current_animal or not self.current_animal.wikipedia:
            return
        self.page.launch_url(self.current_animal.wikipedia.article_url)

    async def _on_copy_image(self, e):
        """Copy local image path to clipboard."""
        if not self.current_animal or not self.current_animal.images:
            return
        if not self.app_state or not self.app_state.image_cache:
            return
        first_image = self.current_animal.images[0]
        url = first_image.thumbnail_url or first_image.url
        local_path = self.app_state.image_cache.get_local_path(url)
        if local_path:
            self.page.set_clipboard(str(local_path))
            self.page.open(ft.SnackBar(content=ft.Text("Chemin de l'image copié !")))
            self.page.update()
