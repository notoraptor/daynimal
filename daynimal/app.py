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
        self.page.title = "Daynimal - Animal du jour"
        self.page.padding = 20
        self.page.scroll = ft.ScrollMode.AUTO

        # Application state
        self.current_animal = None

        # Build UI
        self.build()

    def build(self):
        """Build the user interface."""
        # Header
        self.header = ft.Text(
            "🦁 Daynimal",
            size=32,
            weight=ft.FontWeight.BOLD,
            color=ft.Colors.PRIMARY,
        )

        # Animal display container
        self.animal_container = ft.Column(
            controls=[],
            spacing=10,
            expand=True,
        )

        # Buttons
        self.today_button = ft.Button(
            "Animal du jour",
            icon=ft.Icons.CALENDAR_TODAY,
            on_click=self.show_today,
            style=ft.ButtonStyle(
                color=ft.Colors.WHITE,
                bgcolor=ft.Colors.PRIMARY,
            ),
        )

        self.random_button = ft.Button(
            "Animal aléatoire",
            icon=ft.Icons.SHUFFLE,
            on_click=self.show_random,
            style=ft.ButtonStyle(
                color=ft.Colors.WHITE,
                bgcolor=ft.Colors.BLUE,
            ),
        )

        button_row = ft.Row(
            controls=[self.today_button, self.random_button],
            spacing=10,
        )

        # Main layout
        self.page.add(
            ft.Column(
                controls=[
                    self.header,
                    ft.Divider(),
                    button_row,
                    self.animal_container,
                ],
                spacing=20,
                expand=True,
            )
        )

        # Show welcome message
        self.animal_container.controls = [
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
        ]

    async def show_today(self, e):
        """Show today's animal."""
        await self.load_animal("today")

    async def show_random(self, e):
        """Show a random animal."""
        await self.load_animal("random")

    async def load_animal(self, mode: str):
        """Load and display an animal."""
        # Show loading message in container
        self.animal_container.controls = [
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

            # Display animal
            self.display_animal(animal)

        except Exception as error:
            # Show error
            self.animal_container.controls = [
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

    def display_animal(self, animal):
        """Display animal information."""
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
        self.animal_container.controls = controls
        self.page.update()


def main():
    """Main entry point for the Flet app."""

    def app_main(page: ft.Page):
        DaynimalApp(page)

    # Run as desktop app
    ft.run(main=app_main)


if __name__ == "__main__":
    main()
