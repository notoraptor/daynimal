"""
Tests for the CLI commands in main.py

These tests verify that CLI commands execute without errors and produce
expected output patterns. They use mocked repositories to avoid database
dependencies.
"""

import io
import sys
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from daynimal import AnimalInfo, Taxon
from daynimal.main import (
    cmd_credits,
    cmd_history,
    cmd_info,
    cmd_random,
    cmd_search,
    cmd_stats,
    main,
    print_animal,
)


@pytest.fixture
def sample_taxon():
    """Create a sample Taxon for testing."""
    return Taxon(
        taxon_id=123456,
        scientific_name="Panthera leo",
        canonical_name="Panthera leo",
        kingdom="Animalia",
        phylum="Chordata",
        class_="Mammalia",
        order="Carnivora",
        family="Felidae",
        genus="Panthera",
        rank="species",
        vernacular_names={"en": ["Lion"], "fr": ["Lion"]},
    )


@pytest.fixture
def sample_animal(sample_taxon):
    """Create a sample AnimalInfo for testing."""
    return AnimalInfo(taxon=sample_taxon)


@pytest.fixture
def mock_repository(sample_animal):
    """Create a mock AnimalRepository with predefined responses."""
    repo = Mock()
    # get_animal_of_the_day removed — "today" is now an alias for "random"
    repo.get_random.return_value = sample_animal
    repo.search.return_value = [sample_animal]
    repo.get_by_name.return_value = sample_animal
    repo.get_by_id.return_value = sample_animal
    repo.get_stats.return_value = {
        "total_taxa": 100000,
        "species_count": 50000,
        "vernacular_names": 200000,
        "enriched_count": 100,
        "enrichment_progress": "100/50000 (0.2%)",
    }
    repo.get_history.return_value = ([sample_animal], 1)
    repo.get_history_count.return_value = 1
    return repo


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


class TestPrintAnimal:
    """Tests for the print_animal function."""

    def test_print_animal_basic(self, sample_animal):
        """Test that print_animal produces output without errors."""
        output = capture_stdout(print_animal, sample_animal)

        # Verify key information is present
        assert "PANTHERA LEO" in output.upper()
        assert "Panthera leo" in output
        assert "ID: 123456" in output
        assert "Classification" in output
        assert "Animalia" in output
        assert "Mammalia" in output

    def test_print_animal_with_vernacular_names(self, sample_animal):
        """Test that vernacular names are displayed."""
        output = capture_stdout(print_animal, sample_animal)

        assert "Common Names" in output
        assert "Lion" in output

    def test_print_animal_with_attribution(self, sample_animal):
        """Test that legal attribution is included."""
        output = capture_stdout(print_animal, sample_animal)

        # Attribution section should be present
        assert "Data Sources" in output or "GBIF" in output


class TestCmdToday:
    """Tests for the 'today' command (now alias for random)."""

    @patch("daynimal.main.cmd_random")
    @patch("daynimal.main.resolve_database", return_value=Path("daynimal.db"))
    @patch("sys.argv", ["daynimal", "today"])
    def test_today_calls_cmd_random(self, _mock_resolve, mock_cmd_random):
        """Test that 'daynimal today' calls cmd_random (alias)."""
        main()
        mock_cmd_random.assert_called_once()


class TestCmdRandom:
    """Tests for the cmd_random command."""

    @patch("daynimal.main.AnimalRepository")
    def test_cmd_random_success(self, mock_repo_class, mock_repository):
        """Test that cmd_random executes without errors."""
        mock_repo_class.return_value.__enter__.return_value = mock_repository

        output = capture_stdout(cmd_random)

        # Verify the repository was called
        mock_repository.get_random.assert_called_once()

        # Verify output contains animal info
        assert "PANTHERA LEO" in output.upper()

    @patch("daynimal.main.AnimalRepository")
    def test_cmd_random_adds_to_history(self, mock_repo_class, mock_repository):
        """Test that cmd_random adds animal to history."""
        mock_repo_class.return_value.__enter__.return_value = mock_repository

        capture_stdout(cmd_random)

        # Verify add_to_history was called
        mock_repository.add_to_history.assert_called_once_with(123456, command="random")


class TestCmdSearch:
    """Tests for the cmd_search command."""

    @patch("daynimal.main.AnimalRepository")
    def test_cmd_search_with_results(self, mock_repo_class, mock_repository):
        """Test search command with results."""
        mock_repo_class.return_value.__enter__.return_value = mock_repository

        output = capture_stdout(cmd_search, "lion")

        # Verify the repository was called
        mock_repository.search.assert_called_once_with("lion", limit=10)

        # Verify output contains results
        assert "Found" in output
        assert "lion" in output.lower()
        assert "123456" in output  # taxon_id
        assert "Panthera leo" in output

    @patch("daynimal.main.AnimalRepository")
    def test_cmd_search_no_results(self, mock_repo_class, mock_repository):
        """Test search command with no results."""
        mock_repository.search.return_value = []
        mock_repo_class.return_value.__enter__.return_value = mock_repository

        output = capture_stdout(cmd_search, "nonexistent")

        # Verify appropriate message
        assert "No results" in output or "0 results" in output


class TestCmdInfo:
    """Tests for the cmd_info command."""

    @patch("daynimal.main.AnimalRepository")
    def test_cmd_info_by_id(self, mock_repo_class, mock_repository):
        """Test info command with taxon ID."""
        mock_repo_class.return_value.__enter__.return_value = mock_repository

        output = capture_stdout(cmd_info, "123456")

        # Verify the repository was called with ID
        mock_repository.get_by_id.assert_called_once_with(123456)

        # Verify output contains animal info
        assert "PANTHERA LEO" in output.upper()

    @patch("daynimal.main.AnimalRepository")
    def test_cmd_info_by_name(self, mock_repo_class, mock_repository):
        """Test info command with scientific name."""
        mock_repo_class.return_value.__enter__.return_value = mock_repository

        output = capture_stdout(cmd_info, "Panthera leo")

        # Verify the repository was called with name
        mock_repository.get_by_name.assert_called_once_with("Panthera leo")

        # Verify output contains animal info
        assert "PANTHERA LEO" in output.upper()

    @patch("daynimal.main.AnimalRepository")
    def test_cmd_info_not_found(self, mock_repo_class, mock_repository):
        """Test info command when animal not found."""
        mock_repository.get_by_id.return_value = None
        mock_repository.get_by_name.return_value = None
        mock_repo_class.return_value.__enter__.return_value = mock_repository

        output = capture_stdout(cmd_info, "999999")

        # Verify appropriate error message
        assert "not found" in output.lower() or "error" in output.lower()

    @patch("daynimal.main.AnimalRepository")
    def test_cmd_info_adds_to_history(self, mock_repo_class, mock_repository):
        """Test that cmd_info adds animal to history."""
        mock_repo_class.return_value.__enter__.return_value = mock_repository

        capture_stdout(cmd_info, "123456")

        # Verify add_to_history was called
        mock_repository.add_to_history.assert_called_once_with(123456, command="info")


class TestCmdStats:
    """Tests for the cmd_stats command."""

    @patch("daynimal.main.AnimalRepository")
    def test_cmd_stats_success(self, mock_repo_class, mock_repository):
        """Test that stats command displays database statistics."""
        mock_repo_class.return_value.__enter__.return_value = mock_repository

        output = capture_stdout(cmd_stats)

        # Verify the repository was called
        mock_repository.get_stats.assert_called_once()

        # Verify output contains statistics
        assert "Statistics" in output or "Total" in output
        assert "100,000" in output or "100000" in output  # total_taxa
        assert "50,000" in output or "50000" in output  # species_count


class TestCmdCredits:
    """Tests for the cmd_credits command."""

    def test_cmd_credits_success(self):
        """Test that credits command displays legal information."""
        output = capture_stdout(cmd_credits)

        # Verify output contains legal information
        assert "GBIF" in output
        assert "CC-BY" in output or "license" in output.lower()


class TestCmdHistory:
    """Tests for the cmd_history command."""

    @patch("daynimal.main.AnimalRepository")
    def test_cmd_history_default(self, mock_repo_class, mock_repository, sample_animal):
        """Test history command with default parameters."""
        sample_animal.viewed_at = datetime.now()
        sample_animal.command = "today"
        mock_repository.get_history.return_value = ([sample_animal], 1)
        mock_repo_class.return_value.__enter__.return_value = mock_repository

        # Call with default parameters (no arguments)
        output = capture_stdout(cmd_history)

        # Verify the repository was called with defaults
        mock_repository.get_history.assert_called_once_with(page=1, per_page=10)

        # Verify output contains history
        assert "History" in output or "Viewed" in output
        assert "Panthera leo" in output

    @patch("daynimal.main.AnimalRepository")
    def test_cmd_history_with_pagination(self, mock_repo_class, mock_repository):
        """Test history command with pagination."""
        mock_repo_class.return_value.__enter__.return_value = mock_repository

        # Call with explicit page and per_page parameters
        _ = capture_stdout(lambda: cmd_history(page=2, per_page=5))

        # Verify the repository was called with correct parameters
        mock_repository.get_history.assert_called_once_with(page=2, per_page=5)

    @patch("daynimal.main.AnimalRepository")
    def test_cmd_history_empty(self, mock_repo_class, mock_repository):
        """Test history command with no history."""
        mock_repository.get_history.return_value = ([], 0)
        mock_repo_class.return_value.__enter__.return_value = mock_repository

        # Call with default parameters
        output = capture_stdout(cmd_history)

        # Verify appropriate message
        assert "No history" in output or "empty" in output.lower()


@patch("daynimal.main.resolve_database", return_value=Path("daynimal.db"))
class TestMainCLI:
    """Tests for the main() CLI entry point and argument parsing."""

    @patch("daynimal.main.cmd_random")
    @patch("sys.argv", ["daynimal"])
    def test_main_no_args_calls_random(self, mock_cmd_random, _mock_resolve):
        """Test that running daynimal with no args calls cmd_random."""
        main()
        mock_cmd_random.assert_called_once()

    @patch("daynimal.main.cmd_random")
    @patch("sys.argv", ["daynimal", "random"])
    def test_main_random_command(self, mock_cmd_random, _mock_resolve):
        """Test that 'daynimal random' calls cmd_random."""
        main()
        mock_cmd_random.assert_called_once()

    @patch("daynimal.main.cmd_search")
    @patch("sys.argv", ["daynimal", "search", "lion"])
    def test_main_search_command_single_word(self, mock_cmd_search, _mock_resolve):
        """Test that 'daynimal search lion' calls cmd_search with 'lion'."""
        main()
        mock_cmd_search.assert_called_once_with("lion")

    @patch("daynimal.main.cmd_search")
    @patch("sys.argv", ["daynimal", "search", "panthera", "leo"])
    def test_main_search_command_multiple_words(self, mock_cmd_search, _mock_resolve):
        """Test that 'daynimal search panthera leo' joins words."""
        main()
        mock_cmd_search.assert_called_once_with("panthera leo")

    @patch("daynimal.main.cmd_info")
    @patch("sys.argv", ["daynimal", "info", "123456"])
    def test_main_info_command_by_id(self, mock_cmd_info, _mock_resolve):
        """Test that 'daynimal info 123456' calls cmd_info with ID."""
        main()
        mock_cmd_info.assert_called_once_with("123456")

    @patch("daynimal.main.cmd_info")
    @patch("sys.argv", ["daynimal", "info", "Panthera leo"])
    def test_main_info_command_by_name(self, mock_cmd_info, _mock_resolve):
        """Test that 'daynimal info Panthera leo' joins name."""
        main()
        mock_cmd_info.assert_called_once_with("Panthera leo")

    @patch("daynimal.main.cmd_stats")
    @patch("sys.argv", ["daynimal", "stats"])
    def test_main_stats_command(self, mock_cmd_stats, _mock_resolve):
        """Test that 'daynimal stats' calls cmd_stats."""
        main()
        mock_cmd_stats.assert_called_once()

    @patch("daynimal.main.cmd_credits")
    @patch("sys.argv", ["daynimal", "credits"])
    def test_main_credits_command(self, mock_cmd_credits, _mock_resolve):
        """Test that 'daynimal credits' calls cmd_credits."""
        main()
        mock_cmd_credits.assert_called_once()

    @patch("daynimal.main.cmd_history")
    @patch("sys.argv", ["daynimal", "history"])
    def test_main_history_command(self, mock_cmd_history, _mock_resolve):
        """Test that 'daynimal history' calls cmd_history with defaults."""
        main()
        # cmd_history now receives named parameters directly from argparse
        mock_cmd_history.assert_called_once_with(page=1, per_page=10)

    @patch("daynimal.main.cmd_history")
    @patch("sys.argv", ["daynimal", "history", "--page", "2"])
    def test_main_history_with_args(self, mock_cmd_history, _mock_resolve):
        """Test that 'daynimal history --page 2' passes page to cmd_history."""
        main()
        # cmd_history now receives parsed integer values
        mock_cmd_history.assert_called_once_with(page=2, per_page=10)

    @patch("daynimal.main.cmd_random")
    @patch("sys.argv", ["daynimal", "--db", "test.db"])
    def test_main_with_db_option(self, mock_cmd_random, _mock_resolve):
        """Test that 'daynimal --db test.db' uses custom DB via context manager."""
        from daynimal.config import settings

        original_url = settings.database_url
        main()

        # Verify settings was restored after context manager (no global pollution)
        assert settings.database_url == original_url

        # Verify command was called
        mock_cmd_random.assert_called_once()

    @patch("daynimal.main.cmd_random")
    @patch("sys.argv", ["daynimal", "--db", "minimal.db", "random"])
    def test_main_with_db_option_and_command(self, mock_cmd_random, _mock_resolve):
        """Test that 'daynimal --db minimal.db random' uses custom DB via context manager."""
        from daynimal.config import settings

        original_url = settings.database_url
        main()

        # Verify settings was restored after context manager (no global pollution)
        assert settings.database_url == original_url

        # Verify command was called
        mock_cmd_random.assert_called_once()

    @patch("sys.argv", ["daynimal", "--db"])
    def test_main_db_without_path_shows_error(self, _mock_resolve):
        """Test that 'daynimal --db' without path shows error."""
        # argparse exits with code 2 for invalid arguments
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 2

    @patch("sys.argv", ["daynimal", "unknown"])
    def test_main_unknown_command_shows_help(self, _mock_resolve):
        """Test that unknown command shows error."""
        # argparse exits with code 2 for invalid subcommands
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 2

    @patch("sys.argv", ["daynimal", "search"])
    def test_main_search_without_query_shows_error(self, _mock_resolve):
        """Test that 'daynimal search' without query shows error."""
        # argparse exits with code 2 for missing required arguments
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 2

    @patch("sys.argv", ["daynimal", "info"])
    def test_main_info_without_arg_shows_error(self, _mock_resolve):
        """Test that 'daynimal info' without argument shows error."""
        # argparse exits with code 2 for missing required arguments
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 2
