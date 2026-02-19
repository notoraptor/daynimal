"""Tests pour daynimal/ui/components/animal_display.py — Affichage détaillé.

Couvre: AnimalDisplay (build, _build_classification, _build_vernacular_names,
_build_wikidata_info, _build_wikipedia_description).

Stratégie: on crée des AnimalInfo avec différents niveaux de données
(minimal, complet, partiel) et on vérifie la structure des contrôles
retournés par build().
"""

from unittest.mock import MagicMock

import flet as ft
import pytest

from daynimal.schemas import (
    AnimalInfo,
    Taxon,
    TaxonomicRank,
    WikidataEntity,
    WikipediaArticle,
    CommonsImage,
    ConservationStatus,
    License,
)


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def minimal_animal():
    """Crée un AnimalInfo minimal (taxon uniquement, sans enrichissement)."""
    # todo: Taxon avec scientific_name, canonical_name, rank=SPECIES
    pass


@pytest.fixture
def full_animal():
    """Crée un AnimalInfo complet avec wikidata, wikipedia, images."""
    # todo: AnimalInfo avec tous les champs remplis
    pass


# =============================================================================
# SECTION 1 : build()
# =============================================================================


class TestAnimalDisplayBuild:
    """Tests pour AnimalDisplay.build()."""

    def test_returns_list_of_controls(self, minimal_animal):
        """Vérifie que build() retourne une liste de ft.Control (pas un seul
        contrôle). La liste doit contenir au minimum le titre, le nom
        scientifique, l'ID et l'attribution."""
        # todo
        pass

    def test_title_is_uppercase_display_name(self, minimal_animal):
        """Vérifie que le premier élément est un ft.Text contenant
        le display_name de l'animal en majuscules (via .upper())."""
        # todo
        pass

    def test_shows_scientific_name(self, minimal_animal):
        """Vérifie qu'un ft.Text contenant le nom scientifique en italique
        est présent dans les contrôles."""
        # todo
        pass

    def test_shows_taxon_id(self, minimal_animal):
        """Vérifie qu'un ft.Text contenant 'ID GBIF: {taxon_id}' est
        présent dans les contrôles."""
        # todo
        pass

    def test_attribution_always_present(self, minimal_animal):
        """Vérifie que le texte d'attribution GBIF est toujours présent
        à la fin des contrôles, même sans enrichissement."""
        # todo
        pass


# =============================================================================
# SECTION 2 : _build_classification
# =============================================================================


class TestBuildClassification:
    """Tests pour AnimalDisplay._build_classification()."""

    def test_all_fields_present(self, full_animal):
        """Vérifie que quand le taxon a kingdom, phylum, class_, order,
        family tous remplis, la classification contient 5 lignes de texte
        plus un titre 'Classification' et un Divider."""
        # todo
        pass

    def test_no_fields_returns_empty(self):
        """Vérifie que quand aucun champ de classification n'est défini
        (kingdom=None, phylum=None, etc.), _build_classification()
        retourne une liste vide."""
        # todo
        pass

    def test_partial_fields(self):
        """Vérifie que seuls les champs non-None sont affichés.
        Par exemple, avec family='Canidae' et order='Carnivora' mais
        phylum=None, seuls 2 champs sont dans la sortie."""
        # todo
        pass


# =============================================================================
# SECTION 3 : _build_vernacular_names
# =============================================================================


class TestBuildVernacularNames:
    """Tests pour AnimalDisplay._build_vernacular_names()."""

    def test_multiple_languages(self):
        """Vérifie que les noms vernaculaires sont affichés groupés par
        langue: 'Français: Loup gris', 'English: Gray Wolf', etc.
        Chaque langue est un ft.Text."""
        # todo
        pass

    def test_truncated_to_5_languages(self):
        """Vérifie que si le taxon a des noms dans plus de 5 langues,
        seules les 5 premières sont affichées et un texte '... et X
        autres langues' est ajouté."""
        # todo
        pass

    def test_truncated_to_3_names_per_language(self):
        """Vérifie que si une langue a plus de 3 noms, seuls les 3 premiers
        sont affichés suivis de '...'."""
        # todo
        pass

    def test_empty_vernacular_names(self):
        """Vérifie que sans noms vernaculaires, _build_vernacular_names()
        retourne une liste vide."""
        # todo
        pass


# =============================================================================
# SECTION 4 : _build_wikidata_info
# =============================================================================


class TestBuildWikidataInfo:
    """Tests pour AnimalDisplay._build_wikidata_info()."""

    def test_iucn_status_displayed(self, full_animal):
        """Vérifie que le statut IUCN est affiché quand wikidata.iucn_status
        est défini (ex: ConservationStatus.LC → 'Préoccupation mineure (LC)')."""
        # todo
        pass

    def test_mass_displayed(self, full_animal):
        """Vérifie que la masse est affichée quand wikidata.mass est défini."""
        # todo
        pass

    def test_length_displayed(self, full_animal):
        """Vérifie que la longueur est affichée quand wikidata.length est défini."""
        # todo
        pass

    def test_lifespan_displayed(self, full_animal):
        """Vérifie que la durée de vie est affichée quand wikidata.lifespan est défini."""
        # todo
        pass

    def test_no_wikidata_returns_empty(self, minimal_animal):
        """Vérifie que sans wikidata, _build_wikidata_info() retourne
        une liste vide."""
        # todo
        pass

    def test_wikidata_with_no_properties(self):
        """Vérifie que si wikidata est défini mais sans iucn_status, mass,
        length ni lifespan, la section n'est pas affichée (liste vide)."""
        # todo
        pass


# =============================================================================
# SECTION 5 : _build_wikipedia_description
# =============================================================================


class TestBuildWikipediaDescription:
    """Tests pour AnimalDisplay._build_wikipedia_description()."""

    def test_summary_displayed(self, full_animal):
        """Vérifie que le résumé Wikipedia est affiché quand
        wikipedia.summary est défini."""
        # todo
        pass

    def test_no_wikipedia_returns_empty(self, minimal_animal):
        """Vérifie que sans wikipedia, _build_wikipedia_description()
        retourne une liste vide."""
        # todo
        pass

    def test_wikipedia_without_summary(self):
        """Vérifie que si wikipedia est défini mais summary est None/vide,
        la section n'est pas affichée."""
        # todo
        pass
