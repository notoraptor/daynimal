"""Tests pour daynimal/ui/components/animal_display.py — Affichage détaillé.

Couvre: AnimalDisplay (build, _build_classification, _build_vernacular_names,
_build_wikidata_info, _build_wikipedia_description).

Stratégie: on crée des AnimalInfo avec différents niveaux de données
(minimal, complet, partiel) et on vérifie la structure des contrôles
retournés par build().
"""

import flet as ft
import pytest

from daynimal.schemas import (
    AnimalInfo,
    Taxon,
    WikidataEntity,
    WikipediaArticle,
    CommonsImage,
    ConservationStatus,
    License,
)
from daynimal.ui.components.animal_display import AnimalDisplay


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def minimal_animal():
    """Crée un AnimalInfo minimal (taxon uniquement, sans enrichissement)."""
    taxon = Taxon(
        taxon_id=42,
        scientific_name="Canis lupus",
        canonical_name="Canis lupus",
        rank="species",
        vernacular_names={},
    )
    return AnimalInfo(taxon=taxon)


@pytest.fixture
def full_animal():
    """Crée un AnimalInfo complet avec wikidata, wikipedia, images."""
    taxon = Taxon(
        taxon_id=5219173,
        scientific_name="Canis lupus",
        canonical_name="Canis lupus",
        rank="species",
        kingdom="Animalia",
        phylum="Chordata",
        class_="Mammalia",
        order="Carnivora",
        family="Canidae",
        genus="Canis",
        vernacular_names={"fr": ["Loup gris", "Loup"], "en": ["Gray Wolf"]},
    )

    wikidata = WikidataEntity(
        qid="Q18498",
        labels={"en": "Canis lupus", "fr": "loup"},
        descriptions={"en": "species of mammal"},
        iucn_status=ConservationStatus.LEAST_CONCERN,
        mass="40 kg",
        length="1.5 m",
        lifespan="15 year",
    )

    wikipedia = WikipediaArticle(
        title="Canis lupus",
        language="fr",
        page_id=3135,
        summary="Le Loup gris est un mammifère de la famille des canidés.",
    )

    images = [
        CommonsImage(
            filename="Wolf1.jpg",
            url="https://upload.wikimedia.org/wolf1.jpg",
            thumbnail_url="https://upload.wikimedia.org/thumb/wolf1.jpg",
            author="Photographer1",
            license=License.CC_BY_SA,
        )
    ]

    return AnimalInfo(
        taxon=taxon,
        wikidata=wikidata,
        wikipedia=wikipedia,
        images=images,
        is_enriched=True,
    )


def _text_values(controls):
    """Extrait les valeurs de texte (.value) de tous les ft.Text d'une liste."""
    return [c.value for c in controls if isinstance(c, ft.Text)]


# =============================================================================
# SECTION 1 : build()
# =============================================================================


class TestAnimalDisplayBuild:
    """Tests pour AnimalDisplay.build()."""

    def test_returns_list_of_controls(self, minimal_animal):
        """Vérifie que build() retourne une liste de ft.Control."""
        display = AnimalDisplay(minimal_animal)
        controls = display.build()

        assert isinstance(controls, list)
        assert len(controls) >= 4  # title, scientific name, ID, attribution

    def test_title_is_uppercase_display_name(self, minimal_animal):
        """Vérifie que le premier élément est le display_name en majuscules."""
        display = AnimalDisplay(minimal_animal)
        controls = display.build()

        title = controls[0]
        assert isinstance(title, ft.Text)
        assert title.value == minimal_animal.display_name.upper()

    def test_shows_scientific_name(self, minimal_animal):
        """Vérifie qu'un ft.Text contenant le nom scientifique en italique est présent."""
        display = AnimalDisplay(minimal_animal)
        controls = display.build()

        sci_text = controls[1]
        assert isinstance(sci_text, ft.Text)
        assert sci_text.value == "Canis lupus"
        assert sci_text.italic is True

    def test_shows_taxon_id(self, minimal_animal):
        """Vérifie qu'un ft.Text contenant 'ID: {taxon_id}' est présent."""
        display = AnimalDisplay(minimal_animal)
        controls = display.build()

        texts = _text_values(controls)
        assert any("ID: 42" in t for t in texts if t)

    def test_attribution_always_present(self, minimal_animal):
        """Vérifie que le texte d'attribution GBIF est toujours présent."""
        display = AnimalDisplay(minimal_animal)
        controls = display.build()

        texts = _text_values(controls)
        assert any("GBIF" in t for t in texts if t)


# =============================================================================
# SECTION 2 : _build_classification
# =============================================================================


class TestBuildClassification:
    """Tests pour AnimalDisplay._build_classification()."""

    def test_all_fields_present(self, full_animal):
        """Vérifie que la classification contient les 5 champs."""
        display = AnimalDisplay(full_animal)
        controls = display._build_classification()

        texts = _text_values(controls)
        assert any("Classification" in t for t in texts if t)
        assert any("Animalia" in t for t in texts if t)
        assert any("Chordata" in t for t in texts if t)
        assert any("Mammalia" in t for t in texts if t)
        assert any("Carnivora" in t for t in texts if t)
        assert any("Canidae" in t for t in texts if t)

    def test_no_fields_returns_empty(self):
        """Vérifie que sans champs de classification, retourne liste vide."""
        taxon = Taxon(
            taxon_id=1, scientific_name="Test", canonical_name="Test", rank="species"
        )
        animal = AnimalInfo(taxon=taxon)
        display = AnimalDisplay(animal)

        controls = display._build_classification()
        assert controls == []

    def test_partial_fields(self):
        """Vérifie que seuls les champs non-None sont affichés."""
        taxon = Taxon(
            taxon_id=1,
            scientific_name="Test",
            canonical_name="Test",
            rank="species",
            family="Canidae",
            order="Carnivora",
        )
        animal = AnimalInfo(taxon=taxon)
        display = AnimalDisplay(animal)

        controls = display._build_classification()
        texts = _text_values(controls)

        assert any("Canidae" in t for t in texts if t)
        assert any("Carnivora" in t for t in texts if t)
        assert not any("Chordata" in t for t in texts if t)


# =============================================================================
# SECTION 3 : _build_vernacular_names
# =============================================================================


class TestBuildVernacularNames:
    """Tests pour AnimalDisplay._build_vernacular_names()."""

    def test_multiple_languages(self):
        """Vérifie que les noms vernaculaires sont groupés par langue."""
        taxon = Taxon(
            taxon_id=1,
            scientific_name="Test",
            canonical_name="Test",
            rank="species",
            vernacular_names={"fr": ["Loup gris"], "en": ["Gray Wolf"]},
        )
        animal = AnimalInfo(taxon=taxon)
        display = AnimalDisplay(animal)

        controls = display._build_vernacular_names()
        texts = _text_values(controls)

        assert any("Loup gris" in t for t in texts if t)
        assert any("Gray Wolf" in t for t in texts if t)

    def test_truncated_to_5_languages(self):
        """Vérifie que si le taxon a plus de 5 langues, seules 5 sont affichées."""
        names = {f"lang{i}": [f"Name {i}"] for i in range(8)}
        taxon = Taxon(
            taxon_id=1,
            scientific_name="Test",
            canonical_name="Test",
            rank="species",
            vernacular_names=names,
        )
        animal = AnimalInfo(taxon=taxon)
        display = AnimalDisplay(animal)

        controls = display._build_vernacular_names()
        # Count language entries (texts with [lang] pattern, exclude header and divider)
        lang_texts = [
            c for c in controls if isinstance(c, ft.Text) and "[" in (c.value or "")
        ]
        assert len(lang_texts) == 5

    def test_truncated_to_3_names_per_language(self):
        """Vérifie que si une langue a plus de 3 noms, '...' est ajouté."""
        taxon = Taxon(
            taxon_id=1,
            scientific_name="Test",
            canonical_name="Test",
            rank="species",
            vernacular_names={"en": ["Name1", "Name2", "Name3", "Name4"]},
        )
        animal = AnimalInfo(taxon=taxon)
        display = AnimalDisplay(animal)

        controls = display._build_vernacular_names()
        texts = _text_values(controls)
        assert any("..." in t for t in texts if t)

    def test_empty_vernacular_names(self):
        """Vérifie que sans noms vernaculaires, retourne liste vide."""
        taxon = Taxon(
            taxon_id=1,
            scientific_name="Test",
            canonical_name="Test",
            rank="species",
            vernacular_names={},
        )
        animal = AnimalInfo(taxon=taxon)
        display = AnimalDisplay(animal)

        controls = display._build_vernacular_names()
        assert controls == []


# =============================================================================
# SECTION 4 : _build_wikidata_info
# =============================================================================


class TestBuildWikidataInfo:
    """Tests pour AnimalDisplay._build_wikidata_info()."""

    def test_iucn_status_displayed(self, full_animal):
        """Vérifie que le statut IUCN est affiché."""
        display = AnimalDisplay(full_animal)
        controls = display._build_wikidata_info()

        texts = _text_values(controls)
        assert any("Conservation" in t for t in texts if t)
        assert any("LC" in t and "Préoccupation mineure" in t for t in texts if t)

    def test_mass_displayed(self, full_animal):
        """Vérifie que la masse est affichée."""
        display = AnimalDisplay(full_animal)
        controls = display._build_wikidata_info()

        texts = _text_values(controls)
        assert any("40 kg" in t for t in texts if t)

    def test_length_displayed(self, full_animal):
        """Vérifie que la longueur est affichée."""
        display = AnimalDisplay(full_animal)
        controls = display._build_wikidata_info()

        texts = _text_values(controls)
        assert any("1.5 m" in t for t in texts if t)

    def test_lifespan_displayed(self, full_animal):
        """Vérifie que la durée de vie est affichée."""
        display = AnimalDisplay(full_animal)
        controls = display._build_wikidata_info()

        texts = _text_values(controls)
        assert any("15 year" in t for t in texts if t)

    def test_no_wikidata_returns_empty(self, minimal_animal):
        """Vérifie que sans wikidata, retourne liste vide."""
        display = AnimalDisplay(minimal_animal)
        controls = display._build_wikidata_info()

        assert controls == []

    def test_wikidata_with_no_properties(self):
        """Vérifie que si wikidata n'a aucune propriété, la section est vide (pas de header inutile)."""
        taxon = Taxon(
            taxon_id=1, scientific_name="Test", canonical_name="Test", rank="species"
        )
        wikidata = WikidataEntity(qid="Q123", labels={}, descriptions={})
        animal = AnimalInfo(taxon=taxon, wikidata=wikidata)
        display = AnimalDisplay(animal)

        controls = display._build_wikidata_info()
        assert controls == []


# =============================================================================
# SECTION 5 : _build_wikipedia_description
# =============================================================================


class TestBuildWikipediaDescription:
    """Tests pour AnimalDisplay._build_wikipedia_description()."""

    def test_summary_displayed(self, full_animal):
        """Vérifie que le résumé Wikipedia est affiché."""
        display = AnimalDisplay(full_animal)
        controls = display._build_wikipedia_description()

        texts = _text_values(controls)
        assert any("mammifère" in t for t in texts if t)

    def test_no_wikipedia_returns_empty(self, minimal_animal):
        """Vérifie que sans wikipedia, retourne liste vide."""
        display = AnimalDisplay(minimal_animal)
        controls = display._build_wikipedia_description()

        assert controls == []

    def test_wikipedia_without_summary(self):
        """Vérifie que si wikipedia.summary est None, la section n'est pas affichée."""
        taxon = Taxon(
            taxon_id=1, scientific_name="Test", canonical_name="Test", rank="species"
        )
        wikipedia = WikipediaArticle(
            title="Test", language="en", page_id=1, summary=None
        )
        animal = AnimalInfo(taxon=taxon, wikipedia=wikipedia)
        display = AnimalDisplay(animal)

        controls = display._build_wikipedia_description()
        assert controls == []
