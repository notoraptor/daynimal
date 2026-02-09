"""
Extended tests for CLI commands covering enrichment display and error paths.

Covers print_animal with wikidata/wikipedia/images, empty DB paths,
and cmd_history edge cases.
"""

import io
import sys
from datetime import datetime
from unittest.mock import Mock, patch

from daynimal import AnimalInfo, Taxon
from daynimal.schemas import (
    WikidataEntity,
    WikipediaArticle,
    CommonsImage,
    ConservationStatus,
    License,
)
from daynimal.main import (
    cmd_today,
    cmd_random,
    cmd_history,
    print_animal,
)


def capture_stdout(func, *args, **kwargs):
    """Helper to capture stdout from a function."""
    old_stdout = sys.stdout
    sys.stdout = buffer = io.StringIO()
    try:
        func(*args, **kwargs)
        output = buffer.getvalue()
    finally:
        sys.stdout = old_stdout
    return output


def _make_enriched_animal():
    """Create a fully enriched animal for testing."""
    taxon = Taxon(
        taxon_id=5219173,
        scientific_name="Canis lupus",
        canonical_name="Canis lupus",
        kingdom="Animalia",
        phylum="Chordata",
        class_="Mammalia",
        order="Carnivora",
        family="Canidae",
        genus="Canis",
        rank="species",
        vernacular_names={"en": ["Wolf"], "fr": ["Loup"]},
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
        summary="Le Loup gris (Canis lupus) est un mammifere de la famille des canides.",
    )

    images = [
        CommonsImage(
            filename="Wolf1.jpg",
            url="https://upload.wikimedia.org/wolf1.jpg",
            thumbnail_url="https://upload.wikimedia.org/thumb/wolf1.jpg",
            author="Photographer1",
            license=License.CC_BY_SA,
        ),
    ]

    return AnimalInfo(
        taxon=taxon,
        wikidata=wikidata,
        wikipedia=wikipedia,
        images=images,
        is_enriched=True,
    )


class TestPrintAnimalEnriched:
    """Tests for print_animal with enriched data."""

    def test_displays_wikidata_info(self):
        """Test that Wikidata info is displayed."""
        animal = _make_enriched_animal()
        output = capture_stdout(print_animal, animal)

        assert "Q18498" in output
        assert "LC" in output
        assert "40 kg" in output
        assert "1.5 m" in output
        assert "15 year" in output

    def test_displays_wikipedia_description(self):
        """Test that Wikipedia description is displayed."""
        animal = _make_enriched_animal()
        output = capture_stdout(print_animal, animal)

        assert "Description from Wikipedia" in output
        assert "Loup" in output

    def test_truncates_long_description(self):
        """Test that long description is truncated at 500 chars."""
        animal = _make_enriched_animal()
        animal.wikipedia.summary = "A " * 300  # >500 chars
        output = capture_stdout(print_animal, animal)

        assert "..." in output

    def test_displays_images_with_attribution(self):
        """Test that images are displayed with attribution."""
        animal = _make_enriched_animal()
        output = capture_stdout(print_animal, animal)

        assert "Images" in output
        assert "1 found" in output
        assert "Credit:" in output
        assert "Wolf1.jpg" in output

    def test_wikidata_status_as_string(self):
        """Test that IUCN status works as string (from cache)."""
        animal = _make_enriched_animal()
        animal.wikidata.iucn_status = "LC"  # String instead of enum
        output = capture_stdout(print_animal, animal)

        assert "LC" in output

    def test_wikidata_without_optional_fields(self):
        """Test print_animal when wikidata has no mass/length/lifespan."""
        animal = _make_enriched_animal()
        animal.wikidata.mass = None
        animal.wikidata.length = None
        animal.wikidata.lifespan = None
        animal.wikidata.iucn_status = None
        output = capture_stdout(print_animal, animal)

        assert "Q18498" in output
        assert "Mass" not in output
        assert "Length" not in output
        assert "Lifespan" not in output


class TestCmdTodayNoAnimal:
    """Tests for cmd_today when no animal in DB."""

    @patch("daynimal.main.AnimalRepository")
    def test_no_animal_in_db(self, mock_repo_class):
        """Test cmd_today when get_animal_of_the_day returns None."""
        repo = Mock()
        repo.get_animal_of_the_day.return_value = None
        mock_repo_class.return_value.__enter__.return_value = repo

        output = capture_stdout(cmd_today)
        assert "No animals" in output


class TestCmdRandomNoAnimal:
    """Tests for cmd_random when no animal in DB."""

    @patch("daynimal.main.AnimalRepository")
    def test_no_animal_in_db(self, mock_repo_class):
        """Test cmd_random when get_random returns None."""
        repo = Mock()
        repo.get_random.return_value = None
        mock_repo_class.return_value.__enter__.return_value = repo

        output = capture_stdout(cmd_random)
        assert "No animals" in output


class TestCmdHistoryEdgeCases:
    """Tests for cmd_history edge cases."""

    def test_page_less_than_1(self):
        """Test cmd_history with page < 1."""
        output = capture_stdout(lambda: cmd_history(page=0, per_page=10))
        assert "page must be >= 1" in output

    def test_per_page_less_than_1(self):
        """Test cmd_history with per_page < 1."""
        output = capture_stdout(lambda: cmd_history(page=1, per_page=0))
        assert "per-page must be >= 1" in output

    @patch("daynimal.main.AnimalRepository")
    def test_empty_page_beyond_total(self, mock_repo_class):
        """Test cmd_history when page exceeds total pages."""
        repo = Mock()
        repo.get_history.return_value = ([], 5)  # 5 total but empty on this page
        mock_repo_class.return_value.__enter__.return_value = repo

        output = capture_stdout(lambda: cmd_history(page=10, per_page=5))
        assert "No entries on page" in output

    @patch("daynimal.main.AnimalRepository")
    def test_multi_page_navigation_middle(self, mock_repo_class):
        """Test cmd_history shows both next/previous on middle page."""
        taxon = Taxon(
            taxon_id=1,
            scientific_name="Test Species",
            canonical_name="Test Species",
            rank="species",
            vernacular_names={"en": ["Test"]},
        )
        animal = AnimalInfo(taxon=taxon)
        animal.viewed_at = datetime.now()
        animal.command = "random"

        repo = Mock()
        repo.get_history.return_value = ([animal], 25)
        mock_repo_class.return_value.__enter__.return_value = repo

        output = capture_stdout(lambda: cmd_history(page=2, per_page=10))

        assert "Next page" in output
        assert "Previous page" in output

    @patch("daynimal.main.AnimalRepository")
    def test_last_page_no_next(self, mock_repo_class):
        """Test cmd_history on last page doesn't show 'Next page'."""
        taxon = Taxon(
            taxon_id=1,
            scientific_name="Test Species",
            canonical_name="Test Species",
            rank="species",
            vernacular_names={"en": ["Test"]},
        )
        animal = AnimalInfo(taxon=taxon)
        animal.viewed_at = datetime.now()
        animal.command = "today"

        repo = Mock()
        repo.get_history.return_value = ([animal], 15)
        mock_repo_class.return_value.__enter__.return_value = repo

        output = capture_stdout(lambda: cmd_history(page=2, per_page=10))

        assert "Previous page" in output
        assert "Next page" not in output

    @patch("daynimal.main.AnimalRepository")
    def test_animal_without_viewed_at(self, mock_repo_class):
        """Test cmd_history with animal missing viewed_at."""
        taxon = Taxon(
            taxon_id=1,
            scientific_name="Test Species",
            canonical_name="Test Species",
            rank="species",
            vernacular_names={},
        )
        animal = AnimalInfo(taxon=taxon)
        animal.viewed_at = None
        animal.command = None

        repo = Mock()
        repo.get_history.return_value = ([animal], 1)
        mock_repo_class.return_value.__enter__.return_value = repo

        output = capture_stdout(cmd_history)

        assert "Unknown" in output
        assert "Test Species" in output
