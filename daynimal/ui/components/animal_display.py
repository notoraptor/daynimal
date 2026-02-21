"""Animal display component for showing detailed animal information."""

import flet as ft

from daynimal.schemas import AnimalInfo


class AnimalDisplay:
    """
    Component for displaying detailed animal information.

    Shows title, scientific name, classification, vernacular names,
    Wikidata properties, and Wikipedia description.
    """

    def __init__(self, animal: AnimalInfo):
        """
        Initialize AnimalDisplay.

        Args:
            animal: AnimalInfo object with all data
        """
        self.animal = animal

    def build(self) -> list[ft.Control]:
        """
        Build the animal display UI.

        Returns:
            List of controls to display
        """
        controls = []

        # Title
        controls.append(
            ft.Text(
                self.animal.display_name.upper(), size=28, weight=ft.FontWeight.BOLD
            )
        )

        # Scientific name
        controls.append(
            ft.Text(
                self.animal.taxon.scientific_name,
                size=18,
                italic=True,
                color=ft.Colors.BLUE,
            )
        )

        # ID
        controls.append(
            ft.Text(
                f"ID: {self.animal.taxon.taxon_id}", size=14, color=ft.Colors.GREY_500
            )
        )

        controls.append(ft.Divider())

        # Classification
        controls.extend(self._build_classification())

        # Common names
        controls.extend(self._build_vernacular_names())

        # Wikidata information
        controls.extend(self._build_wikidata_info())

        # Wikipedia description
        controls.extend(self._build_wikipedia_description())

        # Attribution
        sources = ["GBIF (CC-BY 4.0)"]
        if self.animal.wikidata:
            sources.append("Wikidata (CC0)")
        if self.animal.wikipedia:
            sources.append("Wikipedia (CC-BY-SA 4.0)")
        controls.append(
            ft.Text(
                f"Données : {' · '.join(sources)}",
                size=12,
                color=ft.Colors.GREY_500,
                italic=True,
            )
        )

        return controls

    def _build_classification(self) -> list[ft.Control]:
        """Build classification section."""
        controls = []

        if any(
            [
                self.animal.taxon.kingdom,
                self.animal.taxon.phylum,
                self.animal.taxon.class_,
                self.animal.taxon.order,
                self.animal.taxon.family,
            ]
        ):
            controls.append(
                ft.Text("Classification", size=20, weight=ft.FontWeight.BOLD)
            )

            classification = []
            if self.animal.taxon.kingdom:
                classification.append(f"Règne: {self.animal.taxon.kingdom}")
            if self.animal.taxon.phylum:
                classification.append(f"Embranchement: {self.animal.taxon.phylum}")
            if self.animal.taxon.class_:
                classification.append(f"Classe: {self.animal.taxon.class_}")
            if self.animal.taxon.order:
                classification.append(f"Ordre: {self.animal.taxon.order}")
            if self.animal.taxon.family:
                classification.append(f"Famille: {self.animal.taxon.family}")

            for item in classification:
                controls.append(ft.Text(f"  • {item}", size=14))

            controls.append(ft.Divider())

        return controls

    def _build_vernacular_names(self) -> list[ft.Control]:
        """Build vernacular names section."""
        controls = []

        if self.animal.taxon.vernacular_names:
            controls.append(
                ft.Text("Noms vernaculaires", size=20, weight=ft.FontWeight.BOLD)
            )

            # Show first 5 languages
            for lang, names in list(self.animal.taxon.vernacular_names.items())[:5]:
                lang_display = lang if lang else "non spécifié"
                names_str = ", ".join(names[:3])
                if len(names) > 3:
                    names_str += "..."
                controls.append(ft.Text(f"  [{lang_display}] {names_str}", size=14))

            controls.append(ft.Divider())

        return controls

    def _build_wikidata_info(self) -> list[ft.Control]:
        """Build Wikidata information section."""
        controls = []

        if self.animal.wikidata:
            if self.animal.wikidata.iucn_status:
                status = (
                    self.animal.wikidata.iucn_status.value
                    if hasattr(self.animal.wikidata.iucn_status, "value")
                    else self.animal.wikidata.iucn_status
                )
                controls.append(ft.Text(f"  • Conservation: {status}", size=14))

            if self.animal.wikidata.mass:
                controls.append(
                    ft.Text(f"  • Masse: {self.animal.wikidata.mass}", size=14)
                )

            if self.animal.wikidata.length:
                controls.append(
                    ft.Text(f"  • Longueur: {self.animal.wikidata.length}", size=14)
                )

            if self.animal.wikidata.lifespan:
                controls.append(
                    ft.Text(
                        f"  • Durée de vie: {self.animal.wikidata.lifespan}", size=14
                    )
                )

        if controls:
            controls = (
                [ft.Text("Informations Wikidata", size=20, weight=ft.FontWeight.BOLD)]
                + controls
                + [ft.Divider()]
            )

        return controls

    def _build_wikipedia_description(self) -> list[ft.Control]:
        """Build Wikipedia description section."""
        controls = []

        if self.animal.wikipedia and self.animal.wikipedia.summary:
            controls.append(
                ft.Text("Description Wikipedia", size=20, weight=ft.FontWeight.BOLD)
            )

            # Display full introduction (exintro from Wikipedia API)
            description = self.animal.wikipedia.summary

            controls.append(ft.Text(description, size=14))

            controls.append(ft.Divider())

        return controls
