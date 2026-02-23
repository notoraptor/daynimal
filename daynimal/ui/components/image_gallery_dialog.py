"""Image gallery dialog for lazy-loading and browsing all animal images."""

import asyncio
from typing import TYPE_CHECKING

import flet as ft

from daynimal.schemas import CommonsImage, ImageSource

if TYPE_CHECKING:
    from daynimal.image_cache import ImageCacheService


class ImageGalleryDialog:
    """Dialog that downloads remaining images with progress, then shows a carousel.

    States:
    1. Downloading: progress bar + text
    2. Carousel: full image carousel with navigation
    3. Already cached: shows carousel directly (no progress bar)
    """

    def __init__(
        self,
        images: list[CommonsImage],
        image_cache: "ImageCacheService",
        page: ft.Page,
        animal_display_name: str = "",
        animal_taxon_id: int = 0,
    ):
        self.images = images
        self.image_cache = image_cache
        self.page = page
        self.animal_display_name = animal_display_name
        self.animal_taxon_id = animal_taxon_id
        self.current_index = 0

    def open(self):
        """Open the gallery dialog."""
        if self.image_cache.are_all_cached(self.images):
            self._show_carousel_dialog()
        else:
            self._show_download_dialog()

    def _build_title_row(self) -> ft.Row:
        """Build the dialog title row with title text and close button."""
        return ft.Row(
            controls=[
                ft.Text("Galerie d'images", size=20, weight=ft.FontWeight.BOLD),
                ft.IconButton(
                    icon=ft.Icons.CLOSE,
                    tooltip="Fermer",
                    on_click=lambda e: self.page.pop_dialog(),
                ),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

    def _show_download_dialog(self):
        """Show dialog with progress bar, then switch to carousel when done."""
        self._progress_bar = ft.ProgressBar(value=0, width=300)
        self._progress_text = ft.Text(
            "Téléchargement des images (0/{})...".format(len(self.images)), size=14
        )
        self._dialog_content = ft.Column(
            controls=[self._progress_text, self._progress_bar],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=15,
            tight=True,
        )

        dialog = ft.AlertDialog(
            title=self._build_title_row(),
            content=ft.Container(content=self._dialog_content, width=420, height=400),
            actions=[],
            modal=False,
        )
        self.page.show_dialog(dialog)

        # Start download in background thread
        self.page.run_task(self._download_all)

    async def _download_all(self):
        """Download all images in a thread, updating progress bar."""

        def on_progress(current: int, total: int):
            self._progress_bar.value = current / total if total > 0 else 1
            self._progress_text.value = (
                f"Téléchargement des images ({current}/{total})..."
            )
            self.page.update()

        await asyncio.to_thread(
            self.image_cache.cache_images_with_progress, self.images, on_progress
        )

        # Switch to carousel view
        self._dialog_content.controls = self._build_carousel_controls()
        self.page.update()

    def _show_carousel_dialog(self):
        """Show dialog directly with carousel (images already cached)."""
        self._dialog_content = ft.Column(
            controls=self._build_carousel_controls(),
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=10,
        )

        dialog = ft.AlertDialog(
            title=self._build_title_row(),
            content=ft.Container(content=self._dialog_content, width=420, height=400),
            actions=[],
            modal=False,
        )
        self.page.show_dialog(dialog)

    def _build_carousel_controls(self) -> list[ft.Control]:
        """Build carousel controls for the current image."""
        if not self.images:
            return [ft.Text("Aucune image disponible")]

        if self.current_index >= len(self.images):
            self.current_index = 0

        current_image = self.images[self.current_index]
        total = len(self.images)

        # Resolve image source
        image_src = current_image.url
        for url in [current_image.thumbnail_url, current_image.url]:
            if url:
                local_path = self.image_cache.get_local_path(url)
                if local_path:
                    image_src = str(local_path)
                    break

        counter_text = ft.Text(
            f"{self.current_index + 1}/{total}",
            size=14,
            weight=ft.FontWeight.BOLD,
            color=ft.Colors.BLUE,
        )

        controls = [
            ft.Image(
                src=image_src,
                width=380,
                height=280,
                fit="contain",
                border_radius=10,
                color=ft.Colors.WHITE
                if current_image.image_source == ImageSource.PHYLOPIC
                and self.page.theme_mode == ft.ThemeMode.DARK
                else None,
            )
        ]

        # Navigation row with counter between arrows
        if total > 1:
            controls.append(
                ft.Row(
                    controls=[
                        ft.IconButton(icon=ft.Icons.ARROW_BACK, on_click=self._on_prev),
                        counter_text,
                        ft.IconButton(
                            icon=ft.Icons.ARROW_FORWARD, on_click=self._on_next
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                )
            )
        else:
            controls.append(counter_text)

        # Credit in scrollable container
        if current_image.author:
            controls.append(
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Text(
                                f"Crédit: {current_image.author}"
                                f" — {current_image.source_label}",
                                size=12,
                                color=ft.Colors.GREY_500,
                                italic=True,
                                no_wrap=False,
                            )
                        ],
                        scroll=ft.ScrollMode.AUTO,
                    ),
                    padding=ft.Padding(left=5, right=5, top=0, bottom=0),
                    height=50,
                )
            )

        return controls

    def _on_prev(self, e):
        """Navigate to previous image."""
        self.current_index = (self.current_index - 1) % len(self.images)
        self._refresh_carousel()

    def _on_next(self, e):
        """Navigate to next image."""
        self.current_index = (self.current_index + 1) % len(self.images)
        self._refresh_carousel()

    def _refresh_carousel(self):
        """Refresh the carousel content in the dialog."""
        self._dialog_content.controls = self._build_carousel_controls()
        self.page.update()
