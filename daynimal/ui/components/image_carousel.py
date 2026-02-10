"""Image carousel component for displaying animal images with navigation."""

from typing import TYPE_CHECKING, Callable

import flet as ft

from daynimal.schemas import CommonsImage

if TYPE_CHECKING:
    from daynimal.image_cache import ImageCacheService


class ImageCarousel:
    """
    Image carousel with navigation controls.

    Displays images one at a time with previous/next buttons.
    """

    def __init__(
        self,
        images: list[CommonsImage],
        current_index: int = 0,
        on_index_change: Callable[[int], None] | None = None,
        animal_display_name: str = "",
        animal_taxon_id: int = 0,
        image_cache: "ImageCacheService | None" = None,
    ):
        """
        Initialize ImageCarousel.

        Args:
            images: List of CommonsImage objects to display
            current_index: Index of the current image to display
            on_index_change: Callback when image index changes (receives new index)
            animal_display_name: Display name of the animal (for error messages)
            animal_taxon_id: Taxon ID of the animal (for error messages)
            image_cache: Optional ImageCacheService for local image loading
        """
        self.images = images
        self.current_index = current_index
        self.on_index_change = on_index_change
        self.animal_display_name = animal_display_name
        self.animal_taxon_id = animal_taxon_id
        self.image_cache = image_cache

    def build(self) -> ft.Control:
        """Build the carousel UI."""
        if not self.images:
            return self._build_empty_state()

        # Ensure current_index is valid
        if self.current_index >= len(self.images):
            self.current_index = 0

        current_image = self.images[self.current_index]
        total_images = len(self.images)

        # Resolve image source: prefer local cache, fallback to URL
        image_src = current_image.url
        if self.image_cache:
            # Try thumbnail first, then original
            for url in [current_image.thumbnail_url, current_image.url]:
                if url:
                    local_path = self.image_cache.get_local_path(url)
                    if local_path:
                        image_src = str(local_path)
                        break

        # Image carousel container
        carousel_content = ft.Column(
            controls=[
                # Image counter
                ft.Text(
                    f"Image {self.current_index + 1}/{total_images}",
                    size=14,
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.BLUE,
                ),
                # Image
                ft.Image(
                    src=image_src,
                    width=400,
                    height=300,
                    fit="contain",
                    border_radius=10,
                    error_content=self._build_error_content(current_image),
                ),
                # Navigation controls (only show if more than 1 image)
                (
                    ft.Row(
                        controls=[
                            ft.IconButton(
                                icon=ft.Icons.ARROW_BACK,
                                on_click=self._on_prev,
                                disabled=total_images <= 1,
                            ),
                            ft.Container(expand=True),  # Spacer
                            ft.IconButton(
                                icon=ft.Icons.ARROW_FORWARD,
                                on_click=self._on_next,
                                disabled=total_images <= 1,
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                    )
                    if total_images > 1
                    else ft.Container()
                ),
                # Image credit
                (
                    ft.Text(
                        f"Crédit: {current_image.author}",
                        size=12,
                        color=ft.Colors.GREY_500,
                        italic=True,
                    )
                    if current_image.author
                    else ft.Container()
                ),
            ],
            spacing=10,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )

        return carousel_content

    def _build_empty_state(self) -> ft.Control:
        """Build the empty state UI when no images available."""
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Icon(ft.Icons.IMAGE, size=60, color=ft.Colors.GREY_500),
                    ft.Text(
                        "Aucune image disponible", size=16, weight=ft.FontWeight.BOLD
                    ),
                    ft.Text(
                        "Cet animal n'a pas encore d'image dans Wikimedia Commons",
                        size=12,
                        color=ft.Colors.GREY_500,
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=10,
            ),
            padding=30,
            bgcolor=ft.Colors.GREY_200,
            border_radius=10,
        )

    def _build_error_content(self, image: CommonsImage) -> ft.Control:
        """Build the error content for failed image loads."""
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Icon(ft.Icons.IMAGE, size=60, color=ft.Colors.ERROR),
                    ft.Text(
                        "Erreur de chargement",
                        size=14,
                        color=ft.Colors.ERROR,
                        weight=ft.FontWeight.BOLD,
                    ),
                    ft.Text("L'image n'a pas pu être chargée", size=12),
                    ft.Text(
                        f"URL: {image.url[:80]}...",
                        size=9,
                        color=ft.Colors.GREY_600,
                        italic=True,
                        selectable=True,
                    ),
                    ft.Text(
                        f"Animal: {self.animal_display_name} (ID: {self.animal_taxon_id})",
                        size=8,
                        color=ft.Colors.GREY_500,
                        italic=True,
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=5,
            ),
            width=400,
            height=300,
            bgcolor=ft.Colors.GREY_200,
            border_radius=10,
            padding=20,
        )

    def _on_prev(self, e):
        """Navigate to previous image."""
        if self.images:
            self.current_index = (self.current_index - 1) % len(self.images)
            if self.on_index_change:
                self.on_index_change(self.current_index)

    def _on_next(self, e):
        """Navigate to next image."""
        if self.images:
            self.current_index = (self.current_index + 1) % len(self.images)
            if self.on_index_change:
                self.on_index_change(self.current_index)
