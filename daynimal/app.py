"""
Daynimal Flet App - Desktop/Mobile Application

A cross-platform application built with Flet (Flutter for Python) that displays
daily animal discoveries with enriched information.
"""

import asyncio
import traceback

import flet as ft

from daynimal.repository import AnimalRepository

# Try to import debugger (optional)
try:
    import daynimal.debug  # noqa: F401

    DEBUG_AVAILABLE = True
except ImportError:
    DEBUG_AVAILABLE = False


class DaynimalApp:
    """Main application class for Daynimal Flet app."""

    def __init__(self, page: ft.Page):
        self.page = page
        self.page.title = "Daynimal"
        self.page.padding = 0
        self.page.scroll = ft.ScrollMode.AUTO

        # Get debugger from page data if available
        self.debugger = None
        if hasattr(page, "data") and isinstance(page.data, dict):
            self.debugger = page.data.get("debugger")

        # Application state
        self.current_animal = None
        self.current_view = "today"
        self.repository = None
        self.current_image_index = 0  # For image carousel
        self.cached_stats = None  # Cached statistics
        self.stats_displayed = False  # Whether stats have been displayed

        # Log app initialization
        if self.debugger:
            self.debugger.logger.info("DaynimalApp initialized")

        # Register cleanup handlers
        self.page.on_disconnect = self.on_disconnect
        if hasattr(self.page, "on_close"):
            self.page.on_close = self.on_close

        # Build UI
        self.build()

    def build(self):
        """Build the user interface."""
        # Load and apply theme from settings
        self._load_theme()

        # Navigation bar - will be set as page.navigation_bar (fixed at bottom)
        self.nav_bar = ft.NavigationBar(
            destinations=[
                ft.NavigationBarDestination(
                    icon=ft.Icons.CALENDAR_TODAY, label="Aujourd'hui"
                ),
                ft.NavigationBarDestination(icon=ft.Icons.HISTORY, label="Historique"),
                ft.NavigationBarDestination(icon=ft.Icons.FAVORITE, label="Favoris"),
                ft.NavigationBarDestination(icon=ft.Icons.SEARCH, label="Recherche"),
                ft.NavigationBarDestination(
                    icon=ft.Icons.BAR_CHART, label="Statistiques"
                ),
                ft.NavigationBarDestination(icon=ft.Icons.SETTINGS, label="Paramètres"),
            ],
            selected_index=0,
            on_change=self.on_nav_change,
        )

        # Set navigation bar as page property (automatically fixed at bottom)
        self.page.navigation_bar = self.nav_bar

        # Main content container (will change based on selected tab)
        self.content_container = ft.Column(
            controls=[], spacing=10, expand=True, scroll=ft.ScrollMode.AUTO
        )

        # Add content to page (navigation bar is separate, fixed at bottom)
        self.page.add(self.content_container)

        # Show initial view (Today)
        self.show_today_view()

    def _load_theme(self):
        """Load theme preference from database and apply it."""
        try:
            if self.repository:
                theme_mode = self.repository.get_setting("theme_mode", "light")
            else:
                # Initialize repository temporarily to get settings
                with AnimalRepository() as repo:
                    theme_mode = repo.get_setting("theme_mode", "light")

            # Apply theme
            if theme_mode == "dark":
                self.page.theme_mode = ft.ThemeMode.DARK
            else:
                self.page.theme_mode = ft.ThemeMode.LIGHT

            if self.debugger:
                self.debugger.logger.info(f"Theme loaded: {theme_mode}")
        except Exception as error:
            # If theme loading fails, default to light
            self.page.theme_mode = ft.ThemeMode.LIGHT
            if self.debugger:
                self.debugger.log_error("_load_theme", error)
            else:
                print(f"ERROR loading theme: {error}")

    def on_theme_toggle(self, e):
        """Handle theme toggle switch change."""
        try:
            is_dark = e.control.value
            new_theme = "dark" if is_dark else "light"

            # Save to database
            if self.repository:
                self.repository.set_setting("theme_mode", new_theme)
            else:
                with AnimalRepository() as repo:
                    repo.set_setting("theme_mode", new_theme)

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

    def on_carousel_prev(self, e):
        """Navigate to previous image in carousel."""
        if self.current_animal and self.current_animal.images:
            self.current_image_index = (self.current_image_index - 1) % len(
                self.current_animal.images
            )
            self._update_carousel()

    def on_carousel_next(self, e):
        """Navigate to next image in carousel."""
        if self.current_animal and self.current_animal.images:
            self.current_image_index = (self.current_image_index + 1) % len(
                self.current_animal.images
            )
            self._update_carousel()

    def _update_carousel(self):
        """Update the carousel display with the current image."""
        if not self.current_animal or not self.current_animal.images:
            return

        # This will trigger a re-render of the current view
        if self.current_view == "today":
            self.display_animal_in_today_view(self.current_animal)
        # Add other views if they also display carousels in the future

    def on_image_error(self, e):
        """Handle image loading errors."""
        try:
            image_url = e.control.src if hasattr(e.control, "src") else "URL inconnue"

            # Log to debugger if available
            if self.debugger:
                self.debugger.logger.error(f"[IMAGE ERROR] Failed to load: {image_url}")
                if self.current_animal:
                    self.debugger.logger.error(
                        f"  Animal: {self.current_animal.display_name} "
                        f"(ID: {self.current_animal.taxon.taxon_id})"
                    )

            # Always print to console
            print("\n[ERROR] Image loading failed!")
            print(f"  URL: {image_url}")
            if self.current_animal:
                print(f"  Animal: {self.current_animal.display_name}")
                print(f"  Taxon ID: {self.current_animal.taxon.taxon_id}")
            print()

        except Exception as error:
            print(f"[ERROR] Exception in on_image_error: {error}")

    def on_history_item_click(self, e):
        """Handle click on history item - load animal and switch to Today view."""
        try:
            # Get taxon_id from the control's data attribute
            taxon_id = e.control.data

            if self.debugger:
                self.debugger.logger.info(f"History item clicked: taxon_id={taxon_id}")

            # Load the animal asynchronously
            asyncio.create_task(self.load_animal_from_history(taxon_id))

        except Exception as error:
            error_msg = f"Error clicking history item: {error}"
            error_traceback = traceback.format_exc()

            if self.debugger:
                self.debugger.log_error("on_history_item_click", error)
                self.debugger.logger.error(f"Full traceback:\n{error_traceback}")
            else:
                print(f"ERROR: {error_msg}")
                print(f"Traceback:\n{error_traceback}")

    async def load_animal_from_history(self, taxon_id: int):
        """Load an animal by taxon_id and display it in Today view."""
        # Switch to Today view first
        self.nav_bar.selected_index = 0
        self.show_today_view()

        # Show loading indicator
        self.today_animal_container.controls = [
            ft.Container(
                content=ft.Column(
                    controls=[
                        ft.ProgressRing(width=60, height=60),
                        ft.Text("Chargement de l'animal...", size=18),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=20,
                ),
                padding=40,
            )
        ]
        self.page.update()
        await asyncio.sleep(0.1)

        try:
            # Fetch animal
            def fetch_animal():
                if self.repository is None:
                    self.repository = AnimalRepository()
                return self.repository.get_by_id(taxon_id)

            animal = await asyncio.to_thread(fetch_animal)
            self.current_animal = animal
            self.current_image_index = 0  # Reset carousel

            if self.debugger:
                self.debugger.log_animal_load("history", animal.display_name)

            # Display animal in Today view
            self.display_animal_in_today_view(animal)

        except Exception as error:
            error_msg = f"Error loading animal from history (ID {taxon_id}): {error}"
            error_traceback = traceback.format_exc()

            if self.debugger:
                self.debugger.log_error("load_animal_from_history", error)
                self.debugger.logger.error(f"Full traceback:\n{error_traceback}")
            else:
                print(f"ERROR: {error_msg}")
                print(f"Traceback:\n{error_traceback}")

            # Show error in UI
            self.today_animal_container.controls = [
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
            self.page.update()

    def on_nav_change(self, e):
        """Handle navigation bar changes."""
        selected_index = e.control.selected_index

        view_names = ["Today", "History", "Favorites", "Search", "Stats", "Settings"]
        if self.debugger and selected_index < len(view_names):
            self.debugger.log_view_change(view_names[selected_index])

        if selected_index == 0:
            self.show_today_view()
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

    # ============================================
    # TODAY VIEW
    # ============================================

    def show_today_view(self):
        """Show the Today view."""
        self.current_view = "today"

        # Header
        header = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Text(
                        "🦁 Animal du jour",
                        size=28,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.PRIMARY,
                    )
                ],
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            padding=20,
        )

        # Buttons
        today_button = ft.Button(
            "Animal du jour",
            icon=ft.Icons.CALENDAR_TODAY,
            on_click=self.load_today_animal,
            style=ft.ButtonStyle(color=ft.Colors.WHITE, bgcolor=ft.Colors.PRIMARY),
        )

        random_button = ft.Button(
            "Animal aléatoire",
            icon=ft.Icons.SHUFFLE,
            on_click=self.load_random_animal,
            style=ft.ButtonStyle(color=ft.Colors.WHITE, bgcolor=ft.Colors.BLUE),
        )

        button_row = ft.Row(
            controls=[today_button, random_button],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=10,
        )

        # Animal display area - restore previous state if available
        if self.current_animal is not None:
            # Restore the previously displayed animal
            self.today_animal_container = ft.Column(controls=[], spacing=10)
            # Update content first so container is added to page
            self.content_container.controls = [
                header,
                ft.Divider(),
                ft.Container(
                    content=button_row,
                    padding=ft.Padding(left=20, right=20, bottom=10, top=0),
                ),
                ft.Container(
                    content=self.today_animal_container, padding=20, expand=True
                ),
            ]
            self.page.update()
            # Now display the animal
            self.display_animal_in_today_view(self.current_animal)
        else:
            # Show welcome message
            self.today_animal_container = ft.Column(
                controls=[
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
                ],
                spacing=10,
            )
            # Update content
            self.content_container.controls = [
                header,
                ft.Divider(),
                ft.Container(
                    content=button_row,
                    padding=ft.Padding(left=20, right=20, bottom=10, top=0),
                ),
                ft.Container(
                    content=self.today_animal_container, padding=20, expand=True
                ),
            ]
            self.page.update()

    async def load_today_animal(self, e):
        """Load today's animal."""
        await self.load_animal_for_today_view("today")

    async def load_random_animal(self, e):
        """Load a random animal."""
        await self.load_animal_for_today_view("random")

    async def load_animal_for_today_view(self, mode: str):
        """Load and display an animal in the Today view."""
        if self.debugger:
            self.debugger.log_animal_load(mode)

        # Show loading message in container
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
                # Create repository if needed
                if self.repository is None:
                    self.repository = AnimalRepository()

                if mode == "today":
                    animal = self.repository.get_animal_of_the_day()
                    self.repository.add_to_history(
                        animal.taxon.taxon_id, command="today"
                    )
                else:  # random
                    animal = self.repository.get_random()
                    self.repository.add_to_history(
                        animal.taxon.taxon_id, command="random"
                    )
                return animal

            animal = await asyncio.to_thread(fetch_animal)
            self.current_animal = animal
            self.current_image_index = 0  # Reset carousel to first image

            if self.debugger:
                self.debugger.log_animal_load(mode, animal.display_name)

            # Display animal in Today view
            self.display_animal_in_today_view(animal)

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

    def display_animal_in_today_view(self, animal):
        """Display animal information in the Today view."""
        controls = []

        # Title
        controls.append(
            ft.Text(animal.display_name.upper(), size=28, weight=ft.FontWeight.BOLD)
        )

        # Scientific name
        controls.append(
            ft.Text(
                animal.taxon.scientific_name, size=18, italic=True, color=ft.Colors.BLUE
            )
        )

        # ID
        controls.append(
            ft.Text(f"ID: {animal.taxon.taxon_id}", size=14, color=ft.Colors.GREY_500)
        )

        # Favorite button
        is_favorite = False
        if self.repository:
            is_favorite = self.repository.is_favorite(animal.taxon.taxon_id)

        favorite_button = ft.IconButton(
            icon=ft.Icons.FAVORITE if is_favorite else ft.Icons.FAVORITE_BORDER,
            icon_color=ft.Colors.RED if is_favorite else ft.Colors.GREY_500,
            icon_size=32,
            tooltip="Ajouter aux favoris" if not is_favorite else "Retirer des favoris",
            data=animal.taxon.taxon_id,
            on_click=self.on_favorite_toggle,
        )

        controls.append(
            ft.Container(
                content=ft.Row(
                    controls=[
                        favorite_button,
                        ft.Text(
                            "Ajouter aux favoris" if not is_favorite else "Retirer des favoris",
                            size=14,
                        ),
                    ],
                    spacing=5,
                ),
                padding=ft.Padding(top=10, bottom=10, left=0, right=0),
            )
        )

        controls.append(ft.Divider())

        # Classification
        if any(
            [
                animal.taxon.kingdom,
                animal.taxon.phylum,
                animal.taxon.class_,
                animal.taxon.order,
                animal.taxon.family,
            ]
        ):
            controls.append(
                ft.Text("Classification", size=20, weight=ft.FontWeight.BOLD)
            )

            classification = []
            if animal.taxon.kingdom:
                classification.append(f"Règne: {animal.taxon.kingdom}")
            if animal.taxon.phylum:
                classification.append(f"Embranchement: {animal.taxon.phylum}")
            if animal.taxon.class_:
                classification.append(f"Classe: {animal.taxon.class_}")
            if animal.taxon.order:
                classification.append(f"Ordre: {animal.taxon.order}")
            if animal.taxon.family:
                classification.append(f"Famille: {animal.taxon.family}")

            for item in classification:
                controls.append(ft.Text(f"  • {item}", size=14))

            controls.append(ft.Divider())

        # Common names
        if animal.taxon.vernacular_names:
            controls.append(
                ft.Text("Noms vernaculaires", size=20, weight=ft.FontWeight.BOLD)
            )

            # Show first 5 languages
            for lang, names in list(animal.taxon.vernacular_names.items())[:5]:
                lang_display = lang if lang else "non spécifié"
                names_str = ", ".join(names[:3])
                if len(names) > 3:
                    names_str += "..."
                controls.append(ft.Text(f"  [{lang_display}] {names_str}", size=14))

            controls.append(ft.Divider())

        # Wikidata information
        if animal.wikidata:
            controls.append(
                ft.Text("Informations Wikidata", size=20, weight=ft.FontWeight.BOLD)
            )

            if animal.wikidata.iucn_status:
                status = (
                    animal.wikidata.iucn_status.value
                    if hasattr(animal.wikidata.iucn_status, "value")
                    else animal.wikidata.iucn_status
                )
                controls.append(ft.Text(f"  • Conservation: {status}", size=14))

            if animal.wikidata.mass:
                controls.append(ft.Text(f"  • Masse: {animal.wikidata.mass}", size=14))

            if animal.wikidata.length:
                controls.append(
                    ft.Text(f"  • Longueur: {animal.wikidata.length}", size=14)
                )

            if animal.wikidata.lifespan:
                controls.append(
                    ft.Text(f"  • Durée de vie: {animal.wikidata.lifespan}", size=14)
                )

            controls.append(ft.Divider())

        # Wikipedia description
        if animal.wikipedia and animal.wikipedia.summary:
            controls.append(
                ft.Text("Description Wikipedia", size=20, weight=ft.FontWeight.BOLD)
            )

            # Display full introduction (exintro from Wikipedia API)
            description = animal.wikipedia.summary

            controls.append(ft.Text(description, size=14))

            controls.append(ft.Divider())

        # Images
        controls.append(ft.Divider())
        controls.append(ft.Text("Images", size=20, weight=ft.FontWeight.BOLD))

        if animal.images and len(animal.images) > 0:
            # Ensure current_image_index is valid
            if self.current_image_index >= len(animal.images):
                self.current_image_index = 0

            current_image = animal.images[self.current_image_index]
            total_images = len(animal.images)

            # Image carousel container
            carousel_content = ft.Column(
                controls=[
                    # Image counter
                    ft.Text(
                        f"Image {self.current_image_index + 1}/{total_images}",
                        size=14,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.BLUE,
                    ),
                    # Image
                    ft.Image(
                        src=current_image.url,
                        width=400,
                        height=300,
                        fit="contain",
                        border_radius=10,
                        error_content=ft.Container(
                            content=ft.Column(
                                controls=[
                                    ft.Icon(
                                        ft.Icons.IMAGE, size=60, color=ft.Colors.ERROR
                                    ),
                                    ft.Text(
                                        "Erreur de chargement",
                                        size=14,
                                        color=ft.Colors.ERROR,
                                        weight=ft.FontWeight.BOLD,
                                    ),
                                    ft.Text("L'image n'a pas pu être chargée", size=12),
                                    ft.Text(
                                        f"URL: {current_image.url[:80]}...",
                                        size=9,
                                        color=ft.Colors.GREY_600,
                                        italic=True,
                                        selectable=True,
                                    ),
                                    ft.Text(
                                        f"Animal: {animal.display_name} (ID: {animal.taxon.taxon_id})",
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
                        ),
                    ),
                    # Navigation controls (only show if more than 1 image)
                    ft.Row(
                        controls=[
                            ft.IconButton(
                                icon=ft.Icons.ARROW_BACK,
                                on_click=self.on_carousel_prev,
                                disabled=total_images <= 1,
                            ),
                            ft.Container(expand=True),  # Spacer
                            ft.IconButton(
                                icon=ft.Icons.ARROW_FORWARD,
                                on_click=self.on_carousel_next,
                                disabled=total_images <= 1,
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                    )
                    if total_images > 1
                    else ft.Container(),
                    # Image credit
                    ft.Text(
                        f"Crédit: {current_image.author}"
                        if current_image.author
                        else "",
                        size=12,
                        color=ft.Colors.GREY_500,
                        italic=True,
                    )
                    if current_image.author
                    else ft.Container(),
                ],
                spacing=10,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            )

            controls.append(carousel_content)
        else:
            # No images available
            controls.append(
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Icon(ft.Icons.IMAGE, size=60, color=ft.Colors.GREY_500),
                            ft.Text(
                                "Aucune image disponible",
                                size=16,
                                weight=ft.FontWeight.BOLD,
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
            )

            controls.append(ft.Divider())

        # Attribution
        controls.append(
            ft.Text(
                "Données: GBIF Backbone Taxonomy (CC-BY 4.0)",
                size=12,
                color=ft.Colors.GREY_500,
                italic=True,
            )
        )

        # Update container
        self.today_animal_container.controls = controls
        self.page.update()

    # ============================================
    # HISTORY VIEW
    # ============================================

    def show_history_view(self):
        """Show the History view."""
        self.current_view = "history"

        # Header
        header = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Text(
                        "📚 Historique",
                        size=28,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.PRIMARY,
                    )
                ],
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            padding=20,
        )

        # History list container
        self.history_list = ft.Column(controls=[], spacing=10)

        # Update content
        self.content_container.controls = [
            header,
            ft.Divider(),
            ft.Container(content=self.history_list, padding=20, expand=True),
        ]
        self.page.update()

        # Load history asynchronously
        asyncio.create_task(self.load_history())

    async def load_history(self):
        """Load history from repository."""
        # Show loading
        self.history_list.controls = [
            ft.Container(
                content=ft.Column(
                    controls=[
                        ft.ProgressRing(width=60, height=60),
                        ft.Text("Chargement de l'historique...", size=18),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=20,
                ),
                padding=40,
            )
        ]
        self.page.update()
        await asyncio.sleep(0.1)

        try:
            # Fetch history
            def fetch_history():
                # Create repository if needed
                if self.repository is None:
                    self.repository = AnimalRepository()
                return self.repository.get_history(page=1, per_page=50)

            history_items, total = await asyncio.to_thread(fetch_history)

            if not history_items:
                # Empty history
                self.history_list.controls = [
                    ft.Container(
                        content=ft.Column(
                            controls=[
                                ft.Icon(
                                    ft.Icons.HISTORY, size=80, color=ft.Colors.GREY_500
                                ),
                                ft.Text(
                                    "Aucun historique",
                                    size=20,
                                    weight=ft.FontWeight.BOLD,
                                ),
                                ft.Text(
                                    "Consultez des animaux pour les voir apparaître ici",
                                    size=14,
                                    color=ft.Colors.GREY_500,
                                ),
                            ],
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            spacing=10,
                        ),
                        padding=40,
                    )
                ]
            else:
                # Display history items
                controls = [
                    ft.Text(
                        f"{total} animal(aux) consulté(s)",
                        size=16,
                        color=ft.Colors.GREY_500,
                    )
                ]

                for item in history_items:
                    # Format datetime
                    viewed_at = item.viewed_at.strftime("%d/%m/%Y %H:%M")

                    card = ft.Card(
                        content=ft.Container(
                            content=ft.Column(
                                controls=[
                                    ft.Row(
                                        controls=[
                                            ft.Text(
                                                item.taxon.canonical_name
                                                or item.taxon.scientific_name,
                                                size=18,
                                                weight=ft.FontWeight.BOLD,
                                            )
                                        ]
                                    ),
                                    ft.Text(
                                        item.taxon.scientific_name,
                                        size=14,
                                        italic=True,
                                        color=ft.Colors.BLUE,
                                    ),
                                    ft.Row(
                                        controls=[
                                            ft.Icon(
                                                ft.Icons.HISTORY,
                                                size=16,
                                                color=ft.Colors.GREY_500,
                                            ),
                                            ft.Text(
                                                viewed_at,
                                                size=12,
                                                color=ft.Colors.GREY_500,
                                            ),
                                            ft.Container(expand=True),  # Spacer
                                            ft.Icon(
                                                ft.Icons.ARROW_FORWARD,
                                                size=16,
                                                color=ft.Colors.GREY_400,
                                            ),
                                        ],
                                        spacing=5,
                                    ),
                                ],
                                spacing=5,
                            ),
                            padding=15,
                            data=item.taxon.taxon_id,  # Store taxon_id for click handler
                            on_click=self.on_history_item_click,
                            ink=True,  # Add ink ripple effect on click
                        )
                    )
                    controls.append(card)

                self.history_list.controls = controls

        except Exception as error:
            # Log error with full traceback
            error_msg = f"Error in load_history_view: {error}"
            error_traceback = traceback.format_exc()

            if self.debugger:
                self.debugger.log_error("load_history_view", error)
                self.debugger.logger.error(f"Full traceback:\n{error_traceback}")
            else:
                # Fallback: print to console if no debugger
                print(f"ERROR: {error_msg}")
                print(f"Traceback:\n{error_traceback}")

            # Show error
            self.history_list.controls = [
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

    # ============================================
    # FAVORITES VIEW
    # ============================================

    def show_favorites_view(self):
        """Show the Favorites view."""
        self.current_view = "favorites"

        # Header
        header = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Text(
                        "⭐ Favoris",
                        size=28,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.PRIMARY,
                    )
                ],
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            padding=20,
        )

        # Favorites list container
        self.favorites_list = ft.Column(controls=[], spacing=10)

        # Update content
        self.content_container.controls = [
            header,
            ft.Divider(),
            ft.Container(content=self.favorites_list, padding=20, expand=True),
        ]
        self.page.update()

        # Load favorites asynchronously
        asyncio.create_task(self.load_favorites())

    async def load_favorites(self):
        """Load favorites from repository."""
        # Show loading
        self.favorites_list.controls = [
            ft.Container(
                content=ft.Column(
                    controls=[
                        ft.ProgressRing(width=60, height=60),
                        ft.Text("Chargement des favoris...", size=18),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=20,
                ),
                padding=40,
            )
        ]
        self.page.update()
        await asyncio.sleep(0.1)

        try:
            # Fetch favorites
            def fetch_favorites():
                # Create repository if needed
                if self.repository is None:
                    self.repository = AnimalRepository()
                return self.repository.get_favorites(page=1, per_page=50)

            favorites_items, total = await asyncio.to_thread(fetch_favorites)

            if not favorites_items:
                # Empty favorites
                self.favorites_list.controls = [
                    ft.Container(
                        content=ft.Column(
                            controls=[
                                ft.Icon(
                                    ft.Icons.FAVORITE, size=80, color=ft.Colors.GREY_500
                                ),
                                ft.Text(
                                    "Aucun favori",
                                    size=20,
                                    weight=ft.FontWeight.BOLD,
                                ),
                                ft.Text(
                                    "Ajoutez des animaux à vos favoris",
                                    size=14,
                                    color=ft.Colors.GREY_500,
                                ),
                            ],
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            spacing=10,
                        ),
                        padding=40,
                    )
                ]
            else:
                # Display favorites items
                controls = [
                    ft.Text(
                        f"{total} favori(s)",
                        size=16,
                        color=ft.Colors.GREY_500,
                    )
                ]

                for item in favorites_items:
                    card = ft.Card(
                        content=ft.Container(
                            content=ft.Column(
                                controls=[
                                    ft.Row(
                                        controls=[
                                            ft.Text(
                                                item.taxon.canonical_name
                                                or item.taxon.scientific_name,
                                                size=18,
                                                weight=ft.FontWeight.BOLD,
                                            )
                                        ]
                                    ),
                                    ft.Text(
                                        item.taxon.scientific_name,
                                        size=14,
                                        italic=True,
                                        color=ft.Colors.BLUE,
                                    ),
                                    ft.Row(
                                        controls=[
                                            ft.Icon(
                                                ft.Icons.FAVORITE,
                                                size=16,
                                                color=ft.Colors.RED,
                                            ),
                                            ft.Text(
                                                "Favori",
                                                size=12,
                                                color=ft.Colors.GREY_500,
                                            ),
                                            ft.Container(expand=True),  # Spacer
                                            ft.Icon(
                                                ft.Icons.ARROW_FORWARD,
                                                size=16,
                                                color=ft.Colors.GREY_400,
                                            ),
                                        ],
                                        spacing=5,
                                    ),
                                ],
                                spacing=5,
                            ),
                            padding=15,
                            data=item.taxon.taxon_id,  # Store taxon_id for click handler
                            on_click=self.on_favorite_item_click,
                            ink=True,  # Add ink ripple effect on click
                        )
                    )
                    controls.append(card)

                self.favorites_list.controls = controls

        except Exception as error:
            # Log error with full traceback
            error_msg = f"Error in load_favorites: {error}"
            error_traceback = traceback.format_exc()

            if self.debugger:
                self.debugger.log_error("load_favorites", error)
                self.debugger.logger.error(f"Full traceback:\n{error_traceback}")
            else:
                # Fallback: print to console if no debugger
                print(f"ERROR: {error_msg}")
                print(f"Traceback:\n{error_traceback}")

            # Show error
            self.favorites_list.controls = [
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

    async def on_favorite_item_click(self, e):
        """Handle click on a favorite item."""
        taxon_id = e.control.data
        asyncio.create_task(self.load_animal_from_favorite(taxon_id))

    async def load_animal_from_favorite(self, taxon_id: int):
        """Load and display an animal from favorites."""
        # Switch to today view
        self.nav_bar.selected_index = 0
        self.show_today_view()

        # Show loading in today view
        self.today_animal_container.controls = [
            ft.Container(
                content=ft.Column(
                    controls=[
                        ft.ProgressRing(width=60, height=60),
                        ft.Text("Chargement de l'animal...", size=18),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=20,
                ),
                padding=40,
            )
        ]
        self.page.update()
        await asyncio.sleep(0.1)

        try:
            # Fetch animal
            def fetch_animal():
                if self.repository is None:
                    self.repository = AnimalRepository()
                return self.repository.get_by_id(taxon_id, enrich=True)

            animal = await asyncio.to_thread(fetch_animal)

            if animal:
                self.current_animal = animal
                self.current_image_index = 0  # Reset carousel
                self.display_animal_in_today_view(animal)
            else:
                self.today_animal_container.controls = [
                    ft.Container(
                        content=ft.Column(
                            controls=[
                                ft.Icon(ft.Icons.ERROR, size=60, color=ft.Colors.ERROR),
                                ft.Text(
                                    "Animal introuvable",
                                    size=20,
                                    color=ft.Colors.ERROR,
                                ),
                            ],
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            spacing=10,
                        ),
                        padding=40,
                    )
                ]

        except Exception as error:
            error_msg = f"Error in load_animal_from_favorite: {error}"
            error_traceback = traceback.format_exc()

            if self.debugger:
                self.debugger.log_error("load_animal_from_favorite", error)
                self.debugger.logger.error(f"Full traceback:\n{error_traceback}")
            else:
                print(f"ERROR: {error_msg}")
                print(f"Traceback:\n{error_traceback}")

            self.today_animal_container.controls = [
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

    def on_favorite_toggle(self, e):
        """Toggle favorite status for an animal."""
        taxon_id = e.control.data

        if self.repository is None:
            self.repository = AnimalRepository()

        is_favorite = self.repository.is_favorite(taxon_id)

        try:
            if is_favorite:
                # Remove from favorites
                success = self.repository.remove_favorite(taxon_id)
                if success:
                    # Show snackbar
                    snack_bar = ft.SnackBar(
                        content=ft.Text("Retiré des favoris"),
                    )
                    self.page.snack_bar = snack_bar
                    snack_bar.open = True
                    self.page.update()

                    # Refresh display if in today view
                    if self.current_view == "today" and self.current_animal:
                        self.display_animal_in_today_view(self.current_animal)
            else:
                # Add to favorites
                success = self.repository.add_favorite(taxon_id)
                if success:
                    # Show snackbar
                    snack_bar = ft.SnackBar(
                        content=ft.Text("Ajouté aux favoris"),
                    )
                    self.page.snack_bar = snack_bar
                    snack_bar.open = True
                    self.page.update()

                    # Refresh display if in today view
                    if self.current_view == "today" and self.current_animal:
                        self.display_animal_in_today_view(self.current_animal)

        except Exception as error:
            error_msg = f"Error in on_favorite_toggle: {error}"
            error_traceback = traceback.format_exc()

            if self.debugger:
                self.debugger.log_error("on_favorite_toggle", error)
                self.debugger.logger.error(f"Full traceback:\n{error_traceback}")
            else:
                print(f"ERROR: {error_msg}")
                print(f"Traceback:\n{error_traceback}")

            # Show error snackbar
            snack_bar = ft.SnackBar(
                content=ft.Text(f"Erreur: {str(error)}"),
                bgcolor=ft.Colors.ERROR,
            )
            self.page.snack_bar = snack_bar
            snack_bar.open = True
            self.page.update()

    # ============================================
    # SEARCH VIEW
    # ============================================

    def show_search_view(self):
        """Show the Search view."""
        self.current_view = "search"

        # Header
        header = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Text(
                        "🔍 Recherche",
                        size=28,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.PRIMARY,
                    )
                ],
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            padding=20,
        )

        # Search field
        self.search_field = ft.TextField(
            label="Rechercher un animal",
            hint_text="Nom scientifique ou vernaculaire",
            prefix_icon=ft.Icons.SEARCH,
            on_change=self.on_search_change,
            autofocus=True,
        )

        # Results container
        self.search_results = ft.Column(
            controls=[
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Icon(ft.Icons.SEARCH, size=80, color=ft.Colors.GREY_500),
                            ft.Text(
                                "Recherchez un animal",
                                size=20,
                                weight=ft.FontWeight.BOLD,
                            ),
                            ft.Text(
                                "Entrez un nom scientifique ou vernaculaire",
                                size=14,
                                color=ft.Colors.GREY_500,
                            ),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=10,
                    ),
                    padding=40,
                )
            ],
            spacing=10,
        )

        # Update content
        self.content_container.controls = [
            header,
            ft.Divider(),
            ft.Container(
                content=self.search_field,
                padding=ft.Padding(left=20, right=20, top=10, bottom=0),
            ),
            ft.Container(content=self.search_results, padding=20, expand=True),
        ]
        self.page.update()

    def on_search_change(self, e):
        """Handle search field changes."""
        query = e.control.value.strip()

        if not query:
            # Reset to empty state
            self.search_results.controls = [
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Icon(ft.Icons.SEARCH, size=80, color=ft.Colors.GREY_500),
                            ft.Text(
                                "Recherchez un animal",
                                size=20,
                                weight=ft.FontWeight.BOLD,
                            ),
                            ft.Text(
                                "Entrez un nom scientifique ou vernaculaire",
                                size=14,
                                color=ft.Colors.GREY_500,
                            ),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=10,
                    ),
                    padding=40,
                )
            ]
            self.page.update()
            return

        # Perform search asynchronously
        asyncio.create_task(self.perform_search(query))

    async def perform_search(self, query: str):
        """Perform search in repository."""
        if self.debugger:
            self.debugger.logger.debug(f"Search started: '{query}'")

        # Show loading
        self.search_results.controls = [
            ft.Container(
                content=ft.Column(
                    controls=[
                        ft.ProgressRing(width=40, height=40),
                        ft.Text("Recherche en cours...", size=16),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=10,
                ),
                padding=20,
            )
        ]
        self.page.update()
        await asyncio.sleep(0.1)

        try:
            # Search
            def search():
                # Create repository if needed
                if self.repository is None:
                    self.repository = AnimalRepository()
                return self.repository.search(query, limit=20)

            results = await asyncio.to_thread(search)

            if self.debugger:
                self.debugger.log_search(query, len(results))

            if not results:
                # No results
                self.search_results.controls = [
                    ft.Container(
                        content=ft.Column(
                            controls=[
                                ft.Icon(
                                    ft.Icons.SEARCH, size=60, color=ft.Colors.GREY_500
                                ),
                                ft.Text(
                                    "Aucun résultat", size=20, weight=ft.FontWeight.BOLD
                                ),
                                ft.Text(
                                    f"Aucun animal trouvé pour '{query}'",
                                    size=14,
                                    color=ft.Colors.GREY_500,
                                ),
                            ],
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            spacing=10,
                        ),
                        padding=40,
                    )
                ]
            else:
                # Display results
                controls = [
                    ft.Text(
                        f"{len(results)} résultat(s) trouvé(s)",
                        size=16,
                        color=ft.Colors.GREY_500,
                    )
                ]

                for animal in results:
                    # Get vernacular names
                    vernacular = ""
                    if animal.taxon.vernacular_names:
                        first_lang = list(animal.taxon.vernacular_names.keys())[0]
                        names = animal.taxon.vernacular_names[first_lang][:2]
                        # Filter out None values
                        names = [n for n in names if n is not None]
                        if names:
                            vernacular = ", ".join(names)
                            if len(animal.taxon.vernacular_names[first_lang]) > 2:
                                vernacular += "..."

                    card = ft.Card(
                        content=ft.Container(
                            content=ft.Column(
                                controls=[
                                    ft.Row(
                                        controls=[
                                            ft.Text(
                                                animal.taxon.canonical_name
                                                or animal.taxon.scientific_name,
                                                size=18,
                                                weight=ft.FontWeight.BOLD,
                                            )
                                        ]
                                    ),
                                    ft.Text(
                                        animal.taxon.scientific_name,
                                        size=14,
                                        italic=True,
                                        color=ft.Colors.BLUE,
                                    ),
                                    ft.Row(
                                        controls=[
                                            ft.Text(
                                                vernacular
                                                if vernacular
                                                else "Pas de nom vernaculaire",
                                                size=12,
                                                color=ft.Colors.GREY_500,
                                            ),
                                            ft.Container(expand=True),  # Spacer
                                            ft.Icon(
                                                ft.Icons.ARROW_FORWARD,
                                                size=16,
                                                color=ft.Colors.GREY_400,
                                            ),
                                        ],
                                        spacing=5,
                                    ),
                                ],
                                spacing=5,
                            ),
                            padding=15,
                            data=animal.taxon.taxon_id,  # Store taxon_id for click handler
                            on_click=self.on_search_result_click,
                            ink=True,  # Add ink ripple effect on click
                        )
                    )
                    controls.append(card)

                self.search_results.controls = controls

        except Exception as error:
            # Log error with full traceback
            error_msg = f"Error in perform_search: {error}"
            error_traceback = traceback.format_exc()

            if self.debugger:
                self.debugger.log_error("perform_search", error)
                self.debugger.logger.error(f"Full traceback:\n{error_traceback}")
            else:
                # Fallback: print to console if no debugger
                print(f"ERROR: {error_msg}")
                print(f"Traceback:\n{error_traceback}")

            # Show error
            self.search_results.controls = [
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Icon(ft.Icons.ERROR, size=60, color=ft.Colors.ERROR),
                            ft.Text(
                                "Erreur lors de la recherche",
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

    async def on_search_result_click(self, e):
        """Handle click on a search result."""
        taxon_id = e.control.data
        asyncio.create_task(self.load_animal_from_search(taxon_id))

    async def load_animal_from_search(self, taxon_id: int):
        """Load and display an animal from search results."""
        # Switch to today view
        self.nav_bar.selected_index = 0
        self.show_today_view()

        # Show loading in today view
        self.today_animal_container.controls = [
            ft.Container(
                content=ft.Column(
                    controls=[
                        ft.ProgressRing(width=60, height=60),
                        ft.Text("Chargement de l'animal...", size=18),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=20,
                ),
                padding=40,
            )
        ]
        self.page.update()
        await asyncio.sleep(0.1)

        try:
            # Fetch animal
            def fetch_animal():
                if self.repository is None:
                    self.repository = AnimalRepository()
                return self.repository.get_by_id(taxon_id, enrich=True)

            animal = await asyncio.to_thread(fetch_animal)

            if animal:
                self.current_animal = animal
                self.current_image_index = 0  # Reset carousel
                self.display_animal_in_today_view(animal)
                # Add to history
                if self.repository:
                    self.repository.add_to_history(taxon_id, command="search")
            else:
                self.today_animal_container.controls = [
                    ft.Container(
                        content=ft.Column(
                            controls=[
                                ft.Icon(ft.Icons.ERROR, size=60, color=ft.Colors.ERROR),
                                ft.Text(
                                    "Animal introuvable",
                                    size=20,
                                    color=ft.Colors.ERROR,
                                ),
                            ],
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            spacing=10,
                        ),
                        padding=40,
                    )
                ]

        except Exception as error:
            error_msg = f"Error in load_animal_from_search: {error}"
            error_traceback = traceback.format_exc()

            if self.debugger:
                self.debugger.log_error("load_animal_from_search", error)
                self.debugger.logger.error(f"Full traceback:\n{error_traceback}")
            else:
                print(f"ERROR: {error_msg}")
                print(f"Traceback:\n{error_traceback}")

            self.today_animal_container.controls = [
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

    # ============================================
    # STATS VIEW
    # ============================================

    def show_stats_view(self):
        """Show the Statistics view."""
        self.current_view = "stats"

        # Header
        header = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Text(
                        "📊 Statistiques",
                        size=28,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.PRIMARY,
                    )
                ],
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            padding=20,
        )

        # Stats container - horizontal layout with wrap
        self.stats_container = ft.Row(
            controls=[],
            spacing=15,
            wrap=True,
            run_spacing=15,
            alignment=ft.MainAxisAlignment.CENTER,
            vertical_alignment=ft.CrossAxisAlignment.START,  # Align cards to top
        )

        # Update content
        self.content_container.controls = [
            header,
            ft.Divider(),
            ft.Container(content=self.stats_container, padding=20, expand=True),
        ]
        self.page.update()

        # If stats already cached, display them immediately
        if self.cached_stats is not None:
            self._display_stats(self.cached_stats)
            self.page.update()

        # Load/refresh stats asynchronously (will update if DB changed)
        asyncio.create_task(self.load_stats())

    def _display_stats(self, stats: dict):
        """Display statistics cards."""
        controls = []

        # Uniform card height for consistent layout
        card_min_height = 220

        # Total taxa
        controls.append(
            ft.Card(
                content=ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Icon(ft.Icons.PETS, size=50, color=ft.Colors.PRIMARY),
                            ft.Text(
                                f"{stats['total_taxa']:,}",
                                size=32,
                                weight=ft.FontWeight.BOLD,
                                color=ft.Colors.PRIMARY,
                                no_wrap=True,
                            ),
                            ft.Text("Taxa totaux", size=16, color=ft.Colors.GREY_500),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=5,
                        tight=True,
                    ),
                    padding=30,
                    height=card_min_height,
                )
            )
        )

        # Species count
        controls.append(
            ft.Card(
                content=ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Icon(ft.Icons.FAVORITE, size=50, color=ft.Colors.BLUE),
                            ft.Text(
                                f"{stats['species_count']:,}",
                                size=32,
                                weight=ft.FontWeight.BOLD,
                                color=ft.Colors.BLUE,
                                no_wrap=True,
                            ),
                            ft.Text("Espèces", size=16, color=ft.Colors.GREY_500),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=5,
                        tight=True,
                    ),
                    padding=30,
                    height=card_min_height,
                )
            )
        )

        # Enriched count
        controls.append(
            ft.Card(
                content=ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Icon(ft.Icons.INFO, size=50, color=ft.Colors.GREEN_500),
                            ft.Text(
                                f"{stats['enriched_count']:,}",
                                size=32,
                                weight=ft.FontWeight.BOLD,
                                color=ft.Colors.GREEN_500,
                                no_wrap=True,
                            ),
                            ft.Text(
                                "Animaux enrichis", size=16, color=ft.Colors.GREY_500
                            ),
                            ft.Text(
                                stats["enrichment_progress"],
                                size=14,
                                color=ft.Colors.GREY_500,
                            ),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=5,
                        tight=True,
                    ),
                    padding=30,
                    height=card_min_height,
                )
            )
        )

        # Vernacular names
        controls.append(
            ft.Card(
                content=ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Icon(
                                ft.Icons.TRANSLATE, size=50, color=ft.Colors.AMBER_500
                            ),
                            ft.Text(
                                f"{stats['vernacular_names']:,}",
                                size=32,
                                weight=ft.FontWeight.BOLD,
                                color=ft.Colors.AMBER_500,
                                no_wrap=True,
                            ),
                            ft.Text(
                                "Noms vernaculaires", size=16, color=ft.Colors.GREY_500
                            ),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=5,
                        tight=True,
                    ),
                    padding=30,
                    height=card_min_height,
                )
            )
        )

        self.stats_container.controls = controls

    async def load_stats(self):
        """Load statistics from repository."""
        # Show loading only if no cached stats
        if self.cached_stats is None:
            self.stats_container.controls = [
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.ProgressRing(width=60, height=60),
                            ft.Text("Chargement des statistiques...", size=18),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=20,
                    ),
                    padding=40,
                )
            ]
            self.page.update()
            await asyncio.sleep(0.1)

        try:
            # Fetch stats
            def fetch_stats():
                # Create repository if needed
                if self.repository is None:
                    self.repository = AnimalRepository()
                return self.repository.get_stats()

            stats = await asyncio.to_thread(fetch_stats)

            # Update cache
            self.cached_stats = stats

            # Display stats
            self._display_stats(stats)
            self.page.update()

        except Exception as error:
            # Log error with full traceback
            error_msg = f"Error in load_stats_view: {error}"
            error_traceback = traceback.format_exc()

            if self.debugger:
                self.debugger.log_error("load_stats_view", error)
                self.debugger.logger.error(f"Full traceback:\n{error_traceback}")
            else:
                # Fallback: print to console if no debugger
                print(f"ERROR: {error_msg}")
                print(f"Traceback:\n{error_traceback}")

            # Show error
            self.stats_container.controls = [
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

    # ============================================
    # SETTINGS VIEW
    # ============================================

    def show_settings_view(self):
        """Show the Settings/About view."""
        self.current_view = "settings"

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
        # Load current theme setting
        try:
            if self.repository:
                theme_mode = self.repository.get_setting("theme_mode", "light")
            else:
                with AnimalRepository() as repo:
                    theme_mode = repo.get_setting("theme_mode", "light")
            is_dark = theme_mode == "dark"
        except Exception:
            is_dark = False

        preferences = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text("Préférences", size=18, weight=ft.FontWeight.BOLD),
                    ft.Switch(
                        label="Thème sombre",
                        value=is_dark,
                        on_change=self.on_theme_toggle,
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
                        "   Taxonomie : CC-BY 4.0", size=10, color=ft.Colors.GREY_600
                    ),
                    ft.Text("🌐 Wikidata - Données structurées", size=12),
                    ft.Text(
                        "   Propriétés : CC0 (domaine public)",
                        size=10,
                        color=ft.Colors.GREY_600,
                    ),
                    ft.Text("📖 Wikipedia - Descriptions", size=12),
                    ft.Text(
                        "   Articles : CC-BY-SA 3.0", size=10, color=ft.Colors.GREY_600
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
        if self.repository:
            stats = self.repository.get_stats()
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
        else:
            db_info = ft.Container()

        # Update content
        self.content_container.controls = [
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
        self.page.update()

    # ============================================
    # CLEANUP METHODS
    # ============================================

    def cleanup(self):
        """
        Clean up resources (close connections, database, etc.).

        This is called when the app is closing to properly release resources.
        Designed to be fast to avoid blocking the app closure.
        """
        if self.debugger:
            self.debugger.logger.info("Cleaning up application resources...")

        # Close repository and all its connections (fast operation)
        if self.repository:
            try:
                # Close API connections
                self.repository.close()
                if self.debugger:
                    self.debugger.logger.info("Repository closed successfully")
            except Exception as e:
                if self.debugger:
                    self.debugger.logger.error(f"Error closing repository: {e}")

        if self.debugger:
            self.debugger.logger.info("Cleanup completed")

    def on_disconnect(self, e):
        """Handle page disconnect event (when user closes the window)."""
        if self.debugger:
            self.debugger.logger.info("Page disconnected, cleaning up...")
        try:
            self.cleanup()
        except Exception as error:
            if self.debugger:
                self.debugger.logger.error(f"Error during disconnect cleanup: {error}")

    def on_close(self, e):
        """Handle page close event."""
        if self.debugger:
            self.debugger.logger.info("Page closed, cleaning up...")
        try:
            self.cleanup()
        except Exception as error:
            if self.debugger:
                self.debugger.logger.error(f"Error during close cleanup: {error}")


def main():
    """Main entry point for the Flet app."""

    def app_main(page: ft.Page):
        DaynimalApp(page)

    # Run as desktop app
    ft.run(main=app_main)


if __name__ == "__main__":
    main()
