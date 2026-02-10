"""Tests for share text building in TodayView."""

from daynimal.schemas import AnimalInfo, Taxon, TaxonomicRank, WikipediaArticle
from daynimal.ui.views.today_view import TodayView


def _make_taxon(**kwargs):
    defaults = {
        "taxon_id": 5219243,
        "scientific_name": "Panthera leo Linnaeus, 1758",
        "canonical_name": "Panthera leo",
        "rank": TaxonomicRank.SPECIES,
        "vernacular_names": {"fr": ["Lion"], "en": ["Lion"]},
    }
    defaults.update(kwargs)
    return Taxon(**defaults)


def _make_wikipedia(**kwargs):
    defaults = {
        "title": "Lion",
        "language": "fr",
        "page_id": 1234,
        "summary": "Le lion est un grand félin.",
        "url": "https://fr.wikipedia.org/wiki/Lion",
    }
    defaults.update(kwargs)
    return WikipediaArticle(**defaults)


def test_build_share_text_with_full_data():
    """Share text includes name, description, URL, and attribution."""
    animal = AnimalInfo(taxon=_make_taxon(), wikipedia=_make_wikipedia())
    text = TodayView._build_share_text(animal)

    assert "Lion (Panthera leo)" in text
    assert "Le lion est un grand félin." in text
    assert "https://fr.wikipedia.org/wiki/Lion" in text
    assert "GBIF (CC-BY 4.0)" in text
    assert "Wikipedia (CC-BY-SA 4.0)" in text


def test_build_share_text_without_wikipedia():
    """Share text without Wikipedia has no URL section."""
    animal = AnimalInfo(taxon=_make_taxon(), wikipedia=None)
    text = TodayView._build_share_text(animal)

    assert "Lion (Panthera leo)" in text
    assert "wikipedia.org" not in text
    assert "GBIF (CC-BY 4.0)" in text


def test_build_share_text_without_description():
    """Share text without description skips that section."""
    animal = AnimalInfo(taxon=_make_taxon(), wikipedia=_make_wikipedia(summary=None))
    text = TodayView._build_share_text(animal)

    assert "Lion (Panthera leo)" in text
    # URL still present
    assert "https://fr.wikipedia.org/wiki/Lion" in text
    # No description line between name and URL
    lines = text.strip().split("\n")
    assert lines[0] == "Lion (Panthera leo)"


def test_build_share_text_attribution_always_present():
    """Attribution line is always present regardless of data."""
    # Minimal animal with no enrichment
    animal = AnimalInfo(
        taxon=_make_taxon(vernacular_names={}), wikipedia=None, wikidata=None
    )
    text = TodayView._build_share_text(animal)

    assert "Via Daynimal" in text
    assert "GBIF (CC-BY 4.0)" in text
    assert "Wikipedia (CC-BY-SA 4.0)" in text


def test_build_share_text_truncates_long_description():
    """Descriptions longer than 200 chars are truncated with ellipsis."""
    long_desc = "A" * 250
    animal = AnimalInfo(
        taxon=_make_taxon(), wikipedia=_make_wikipedia(summary=long_desc)
    )
    text = TodayView._build_share_text(animal)

    # Description should be 200 chars (197 + "...")
    lines = text.strip().split("\n")
    desc_line = lines[1]
    assert len(desc_line) == 200
    assert desc_line.endswith("...")
