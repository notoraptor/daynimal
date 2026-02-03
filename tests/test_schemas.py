"""
Tests for data schemas and attribution methods.

These tests verify that attribution is correctly generated for all data types.
"""

import pytest

from daynimal.schemas import (
    AnimalInfo,
    Taxon,
    WikidataEntity,
    WikipediaArticle,
    CommonsImage,
    License,
    TaxonomicRank,
)


class TestTaxon:
    """Tests for Taxon dataclass."""

    def test_create_taxon(self):
        """Test creating a basic Taxon."""
        taxon = Taxon(
            taxon_id=5219173,
            scientific_name="Canis lupus Linnaeus, 1758",
            canonical_name="Canis lupus",
            rank=TaxonomicRank.SPECIES,
            kingdom="Animalia",
            phylum="Chordata",
            class_="Mammalia",
            order="Carnivora",
            family="Canidae",
            genus="Canis",
        )

        assert taxon.taxon_id == 5219173
        assert taxon.canonical_name == "Canis lupus"
        assert taxon.rank == TaxonomicRank.SPECIES

    def test_taxon_with_vernacular_names(self):
        """Test taxon with multiple vernacular names."""
        taxon = Taxon(
            taxon_id=1,
            scientific_name="Canis lupus",
            vernacular_names={
                "fr": ["Loup gris", "Loup commun"],
                "en": ["Gray wolf", "Grey wolf"],
            },
        )

        assert "Loup gris" in taxon.vernacular_names["fr"]
        assert "Gray wolf" in taxon.vernacular_names["en"]


class TestAnimalInfo:
    """Tests for AnimalInfo and its attribution methods."""

    @pytest.fixture
    def sample_animal(self):
        """Create a sample animal with all data populated."""
        taxon = Taxon(
            taxon_id=5219173,
            scientific_name="Canis lupus",
            canonical_name="Canis lupus",
            rank=TaxonomicRank.SPECIES,
            vernacular_names={"fr": ["Loup gris"], "en": ["Gray wolf"]},
        )

        wikidata = WikidataEntity(
            qid="Q18498",
            labels={"en": "Canis lupus", "fr": "loup"},
            descriptions={"en": "species of mammal"},
        )

        wikipedia = WikipediaArticle(
            title="Canis lupus",
            language="fr",
            page_id=3135,
            summary="Le loup est un mammifère carnivore.",
            url="https://fr.wikipedia.org/wiki/Canis_lupus",
        )

        images = [
            CommonsImage(
                filename="Wolf.jpg",
                url="https://upload.wikimedia.org/wolf.jpg",
                author="John Doe",
                license=License.CC_BY_SA,
            ),
            CommonsImage(
                filename="Wolf2.jpg",
                url="https://upload.wikimedia.org/wolf2.jpg",
                author="Jane Smith",
                license=License.CC0,
            ),
        ]

        return AnimalInfo(
            taxon=taxon,
            wikidata=wikidata,
            wikipedia=wikipedia,
            images=images,
            is_enriched=True,
        )

    def test_display_name_prefers_french(self, sample_animal):
        """Test that French name is preferred for display."""
        assert sample_animal.display_name == "Loup gris"

    def test_display_name_falls_back_to_english(self):
        """Test fallback to English if no French name."""
        taxon = Taxon(
            taxon_id=1,
            scientific_name="Canis lupus",
            vernacular_names={"en": ["Gray wolf"]},
        )
        animal = AnimalInfo(taxon=taxon)

        assert animal.display_name == "Gray wolf"

    def test_display_name_falls_back_to_scientific(self):
        """Test fallback to scientific name if no vernacular names."""
        taxon = Taxon(
            taxon_id=1, scientific_name="Canis lupus", canonical_name="Canis lupus"
        )
        animal = AnimalInfo(taxon=taxon)

        assert animal.display_name == "Canis lupus"

    def test_description_from_wikipedia(self, sample_animal):
        """Test that description comes from Wikipedia summary."""
        assert sample_animal.description is not None
        assert "loup" in sample_animal.description.lower()

    def test_main_image(self, sample_animal):
        """Test main_image returns first image."""
        assert sample_animal.main_image is not None
        assert sample_animal.main_image.filename == "Wolf.jpg"

    def test_get_attribution_text_includes_gbif(self, sample_animal):
        """Test that attribution text includes GBIF."""
        attribution = sample_animal.get_attribution_text()

        assert "GBIF" in attribution
        assert "CC-BY" in attribution

    def test_get_attribution_text_includes_wikidata(self, sample_animal):
        """Test that attribution text includes Wikidata."""
        attribution = sample_animal.get_attribution_text()

        assert "Wikidata" in attribution
        assert "Q18498" in attribution
        assert "CC0" in attribution

    def test_get_attribution_text_includes_wikipedia(self, sample_animal):
        """Test that attribution text includes Wikipedia."""
        attribution = sample_animal.get_attribution_text()

        assert "Wikipedia" in attribution
        assert "CC-BY-SA" in attribution
        assert "fr.wikipedia.org" in attribution

    def test_get_attribution_text_includes_images(self, sample_animal):
        """Test that attribution text includes image credits."""
        attribution = sample_animal.get_attribution_text()

        assert "John Doe" in attribution
        assert "Jane Smith" in attribution
        assert "Wikimedia Commons" in attribution

    def test_get_attribution_html_has_links(self, sample_animal):
        """Test that HTML attribution contains links."""
        html = sample_animal.get_attribution_html()

        assert "<a href=" in html
        assert "wikidata.org" in html
        assert "wikipedia.org" in html
        assert "creativecommons.org" in html

    def test_get_required_attributions_summary(self, sample_animal):
        """Test structured attribution summary."""
        summary = sample_animal.get_required_attributions_summary()

        assert "taxonomy" in summary
        assert summary["taxonomy"]["license"] == "CC-BY 4.0"

        assert "wikidata" in summary
        assert summary["wikidata"]["qid"] == "Q18498"

        assert "wikipedia" in summary
        assert summary["wikipedia"]["license"] == "CC-BY-SA 4.0"

        assert "images" in summary
        assert len(summary["images"]) == 2

    def test_attribution_without_enrichment(self):
        """Test attribution when only taxonomy is present."""
        taxon = Taxon(taxon_id=1, scientific_name="Canis lupus")
        animal = AnimalInfo(taxon=taxon)

        attribution = animal.get_attribution_text()

        # Should still have GBIF attribution
        assert "GBIF" in attribution
        # Should not have Wikidata/Wikipedia
        assert "Wikidata" not in attribution
        assert "Wikipedia" not in attribution


class TestCommonsImageAttribution:
    """Tests for CommonsImage attribution methods."""

    def test_attribution_text_cc_by_sa(self):
        """Test attribution text for CC-BY-SA image."""
        image = CommonsImage(
            filename="Wolf.jpg",
            url="https://example.com/wolf.jpg",
            author="John Doe",
            license=License.CC_BY_SA,
        )

        text = image.get_attribution_text()

        assert "Wolf.jpg" in text
        assert "John Doe" in text
        assert "CC-BY-SA" in text
        assert "Wikimedia Commons" in text

    def test_attribution_text_cc0(self):
        """Test attribution text for CC0 image."""
        image = CommonsImage(
            filename="Wolf.jpg",
            url="https://example.com/wolf.jpg",
            author="Jane Smith",
            license=License.CC0,
        )

        text = image.get_attribution_text()

        # CC0 still shows author (it's good practice)
        assert "Jane Smith" in text
        assert "CC0" in text

    def test_attribution_text_unknown_author(self):
        """Test attribution text when author is unknown."""
        image = CommonsImage(
            filename="Wolf.jpg",
            url="https://example.com/wolf.jpg",
            author=None,
            license=License.CC_BY,
        )

        text = image.get_attribution_text()

        assert "Unknown author" in text

    def test_attribution_required_for_cc_by(self):
        """Test that attribution_required is True for CC-BY."""
        image = CommonsImage(
            filename="test.jpg",
            url="https://example.com/test.jpg",
            license=License.CC_BY,
        )

        assert image.attribution_required is True

    def test_attribution_not_required_for_cc0(self):
        """Test that attribution_required is False for CC0."""
        image = CommonsImage(
            filename="test.jpg",
            url="https://example.com/test.jpg",
            license=License.CC0,
            attribution_required=False,
        )

        assert image.attribution_required is False

    def test_commons_page_url_handles_spaces(self):
        """Test that spaces in filename are converted to underscores."""
        image = CommonsImage(
            filename="Wolf in snow.jpg",
            url="https://example.com/wolf.jpg",
            license=License.CC_BY,
        )

        assert "Wolf_in_snow.jpg" in image.commons_page_url
