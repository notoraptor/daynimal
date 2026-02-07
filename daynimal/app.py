"""
Daynimal Flet App - Desktop/Mobile Application

A cross-platform application built with Flet (Flutter for Python) that displays
daily animal discoveries with enriched information.
"""

import asyncio

import flet as ft

from daynimal.repository import AnimalRepository


class DaynimalApp:
    """Main application class for Daynimal Flet app."""

    def __init__(self, page: ft.Page):
        self.page = page
        self.page.title = "Daynimal"
        self.page.padding = 0
        self.page.scroll = ft.ScrollMode.AUTO

        # Application state
        self.current_animal = None
        self.current_view = "today"

        # Build UI
        self.build()

    def build(self):
        """Build the user interface."""
        # Main content container (will change based on selected tab)
        self.content_container = ft.Column(
            controls=[],
            spacing=10,
            expand=True,
            scroll=ft.ScrollMode.AUTO,
        )

        # Navigation bar
        self.nav_bar = ft.NavigationBar(
            destinations=[
                ft.NavigationBarDestination(
                    icon=ft.Icons.CALENDAR_TODAY,
                    label="Aujourd'hui",
                ),
                ft.NavigationBarDestination(
                    icon=ft.Icons.HISTORY,
                    label="Historique",
                ),
                ft.NavigationBarDestination(
                    icon=ft.Icons.SEARCH,
                    label="Recherche",
                ),
                ft.NavigationBarDestination(
                    icon=ft.Icons.BAR_CHART,
                    label="Statistiques",
                ),
            ],
            selected_index=0,
            on_change=self.on_nav_change,
        )

        # Main layout
        self.page.add(
            ft.Column(
                controls=[
                    self.content_container,
                    self.nav_bar,
                ],
                spacing=0,
                expand=True,
            )
        )

        # Show initial view (Today)
        self.show_today_view()

    def on_nav_change(self, e):
        """Handle navigation bar changes."""
        selected_index = e.control.selected_index

        if selected_index == 0:
            self.show_today_view()
        elif selected_index == 1:
            self.show_history_view()
        elif selected_index == 2:
            self.show_search_view()
        elif selected_index == 3:
            self.show_stats_view()

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
                    ),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            padding=20,
        )

        # Buttons
        today_button = ft.ElevatedButton(
            "Animal du jour",
            icon=ft.Icons.CALENDAR_TODAY,
            on_click=self.load_today_animal,
            style=ft.ButtonStyle(
                color=ft.Colors.WHITE,
                bgcolor=ft.Colors.PRIMARY,
            ),
        )

        random_button = ft.ElevatedButton(
            "Animal aléatoire",
            icon=ft.Icons.SHUFFLE,
            on_click=self.load_random_animal,
            style=ft.ButtonStyle(
                color=ft.Colors.WHITE,
                bgcolor=ft.Colors.BLUE,
            ),
        )

        button_row = ft.Row(
            controls=[today_button, random_button],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=10,
        )

        # Animal display area
        self.today_animal_container = ft.Column(
            controls=[
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Icon(ft.Icons.FAVORITE, size=80, color=ft.Colors.PRIMARY),
                            ft.Text(
                                "Bienvenue sur Daynimal !",
                                size=24,
                                weight=ft.FontWeight.BOLD,
                            ),
                            ft.Text(
                                "Découvrez un animal chaque jour",
                                size=16,
                            ),
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
            ft.Container(content=button_row, padding=ft.padding.only(left=20, right=20, bottom=10)),
            ft.Container(
                content=self.today_animal_container,
                padding=20,
                expand=True,
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
        # Show loading message in container
        self.today_animal_container.controls = [
            ft.Container(
                content=ft.Column(
                    controls=[
                        ft.ProgressRing(width=60, height=60),
                        ft.Text("Chargement en cours...", size=18, weight=ft.FontWeight.BOLD),
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
                with AnimalRepository() as repo:
                    if mode == "today":
                        animal = repo.get_animal_of_the_day()
                        repo.add_to_history(animal.taxon.taxon_id, command="today")
                    else:  # random
                        animal = repo.get_random()
                        repo.add_to_history(animal.taxon.taxon_id, command="random")
                return animal

            animal = await asyncio.to_thread(fetch_animal)
            self.current_animal = animal

            # Display animal in Today view
            self.display_animal_in_today_view(animal)

        except Exception as error:
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
                            ft.Text(
                                str(error),
                                size=14,
                            ),
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
            ft.Text(
                animal.display_name.upper(),
                size=28,
                weight=ft.FontWeight.BOLD,
            )
        )

        # Scientific name
        controls.append(
            ft.Text(
                animal.taxon.scientific_name,
                size=18,
                italic=True,
                color=ft.Colors.BLUE,
            )
        )

        # ID
        controls.append(
            ft.Text(
                f"ID: {animal.taxon.taxon_id}",
                size=14,
                color=ft.Colors.GREY_500,
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

            # Truncate long descriptions
            description = animal.wikipedia.summary
            if len(description) > 500:
                description = description[:500] + "..."

            controls.append(
                ft.Text(
                    description,
                    size=14,
                )
            )

            controls.append(ft.Divider())

        # Images
        controls.append(ft.Divider())
        controls.append(ft.Text("Images", size=20, weight=ft.FontWeight.BOLD))

        if animal.images and len(animal.images) > 0:
            # Show image count for debugging
            controls.append(
                ft.Text(
                    f"📷 {len(animal.images)} image(s) trouvée(s)",
                    size=12,
                    color=ft.Colors.BLUE,
                )
            )

            # Show first image
            first_image = animal.images[0]

            controls.append(
                ft.Image(
                    src=first_image.url,
                    width=400,
                    height=300,
                    fit=ft.ImageFit.CONTAIN,
                    border_radius=10,
                    error_content=ft.Container(
                        content=ft.Column(
                            controls=[
                                ft.Icon(ft.Icons.IMAGE, size=60, color=ft.Colors.ERROR),
                                ft.Text("Erreur de chargement", size=14, color=ft.Colors.ERROR),
                                ft.Text("L'URL existe mais l'image n'a pas pu être chargée", size=10),
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
                )
            )

            # Image credit
            if first_image.artist:
                controls.append(
                    ft.Text(
                        f"Crédit: {first_image.artist}",
                        size=12,
                        color=ft.Colors.GREY_500,
                        italic=True,
                    )
                )
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
                    ),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            padding=20,
        )

        # History list container
        self.history_list = ft.Column(
            controls=[],
            spacing=10,
        )

        # Update content
        self.content_container.controls = [
            header,
            ft.Divider(),
            ft.Container(
                content=self.history_list,
                padding=20,
                expand=True,
            ),
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
                with AnimalRepository() as repo:
                    return repo.get_history(page=1, per_page=50)

            history_items, total = await asyncio.to_thread(fetch_history)

            if not history_items:
                # Empty history
                self.history_list.controls = [
                    ft.Container(
                        content=ft.Column(
                            controls=[
                                ft.Icon(ft.Icons.HISTORY, size=80, color=ft.Colors.GREY_500),
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
                                                item.taxon.canonical_name or item.taxon.scientific_name,
                                                size=18,
                                                weight=ft.FontWeight.BOLD,
                                            ),
                                        ],
                                    ),
                                    ft.Text(
                                        item.taxon.scientific_name,
                                        size=14,
                                        italic=True,
                                        color=ft.Colors.BLUE,
                                    ),
                                    ft.Row(
                                        controls=[
                                            ft.Icon(ft.Icons.HISTORY, size=16, color=ft.Colors.GREY_500),
                                            ft.Text(
                                                viewed_at,
                                                size=12,
                                                color=ft.Colors.GREY_500,
                                            ),
                                        ],
                                        spacing=5,
                                    ),
                                ],
                                spacing=5,
                            ),
                            padding=15,
                        ),
                    )
                    controls.append(card)

                self.history_list.controls = controls

        except Exception as error:
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
                    ),
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
            ft.Container(content=self.search_field, padding=ft.padding.only(left=20, right=20, top=10)),
            ft.Container(
                content=self.search_results,
                padding=20,
                expand=True,
            ),
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
                with AnimalRepository() as repo:
                    return repo.search(query, limit=20)

            results = await asyncio.to_thread(search)

            if not results:
                # No results
                self.search_results.controls = [
                    ft.Container(
                        content=ft.Column(
                            controls=[
                                ft.Icon(ft.Icons.SEARCH, size=60, color=ft.Colors.GREY_500),
                                ft.Text(
                                    "Aucun résultat",
                                    size=20,
                                    weight=ft.FontWeight.BOLD,
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
                        vernacular = ", ".join(names)
                        if len(animal.taxon.vernacular_names[first_lang]) > 2:
                            vernacular += "..."

                    card = ft.Card(
                        content=ft.Container(
                            content=ft.Column(
                                controls=[
                                    ft.Text(
                                        animal.taxon.canonical_name or animal.taxon.scientific_name,
                                        size=18,
                                        weight=ft.FontWeight.BOLD,
                                    ),
                                    ft.Text(
                                        animal.taxon.scientific_name,
                                        size=14,
                                        italic=True,
                                        color=ft.Colors.BLUE,
                                    ),
                                    ft.Text(
                                        vernacular if vernacular else "Pas de nom vernaculaire",
                                        size=12,
                                        color=ft.Colors.GREY_500,
                                    ),
                                ],
                                spacing=5,
                            ),
                            padding=15,
                        ),
                    )
                    controls.append(card)

                self.search_results.controls = controls

        except Exception as error:
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
                    ),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            padding=20,
        )

        # Stats container
        self.stats_container = ft.Column(
            controls=[],
            spacing=10,
        )

        # Update content
        self.content_container.controls = [
            header,
            ft.Divider(),
            ft.Container(
                content=self.stats_container,
                padding=20,
                expand=True,
            ),
        ]
        self.page.update()

        # Load stats asynchronously
        asyncio.create_task(self.load_stats())

    async def load_stats(self):
        """Load statistics from repository."""
        # Show loading
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
                with AnimalRepository() as repo:
                    return repo.get_stats()

            stats = await asyncio.to_thread(fetch_stats)

            # Display stats as cards
            controls = []

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
                                ),
                                ft.Text(
                                    "Taxa totaux",
                                    size=16,
                                    color=ft.Colors.GREY_500,
                                ),
                            ],
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            spacing=5,
                        ),
                        padding=30,
                    ),
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
                                ),
                                ft.Text(
                                    "Espèces",
                                    size=16,
                                    color=ft.Colors.GREY_500,
                                ),
                            ],
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            spacing=5,
                        ),
                        padding=30,
                    ),
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
                                ),
                                ft.Text(
                                    "Animaux enrichis",
                                    size=16,
                                    color=ft.Colors.GREY_500,
                                ),
                                ft.Text(
                                    stats['enrichment_progress'],
                                    size=14,
                                    color=ft.Colors.GREY_500,
                                ),
                            ],
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            spacing=5,
                        ),
                        padding=30,
                    ),
                )
            )

            # Vernacular names
            controls.append(
                ft.Card(
                    content=ft.Container(
                        content=ft.Column(
                            controls=[
                                ft.Icon(ft.Icons.TRANSLATE, size=50, color=ft.Colors.AMBER_500),
                                ft.Text(
                                    f"{stats['vernacular_names']:,}",
                                    size=32,
                                    weight=ft.FontWeight.BOLD,
                                    color=ft.Colors.AMBER_500,
                                ),
                                ft.Text(
                                    "Noms vernaculaires",
                                    size=16,
                                    color=ft.Colors.GREY_500,
                                ),
                            ],
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            spacing=5,
                        ),
                        padding=30,
                    ),
                )
            )

            self.stats_container.controls = controls

        except Exception as error:
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


def main():
    """Main entry point for the Flet app."""

    def app_main(page: ft.Page):
        DaynimalApp(page)

    # Run as desktop app
    ft.run(main=app_main)


if __name__ == "__main__":
    main()
