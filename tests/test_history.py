"""
Tests for animal history functionality.
"""

from datetime import datetime

import pytest
from sqlalchemy.orm import Session

from daynimal.db.models import TaxonModel
from daynimal.repository import AnimalRepository
from daynimal.schemas import AnimalInfo


@pytest.fixture
def sample_taxa(session: Session):
    """Create sample taxa for testing."""
    taxa = []
    for i in range(15):
        taxon = TaxonModel(
            taxon_id=1000 + i,
            scientific_name=f"Testus animalus_{i}",
            canonical_name=f"Testus animalus_{i}",
            rank="species",
            kingdom="Animalia",
        )
        session.add(taxon)
        taxa.append(taxon)
    session.commit()
    return taxa


def test_add_to_history(session: Session, sample_taxa):
    """Test adding an entry to history."""
    repo = AnimalRepository(session=session)

    # Add entry
    entry = repo.add_to_history(taxon_id=1000, command="today")

    # Verify
    assert entry.taxon_id == 1000
    assert entry.command == "today"
    assert entry.viewed_at is not None
    assert isinstance(entry.viewed_at, datetime)

    # Verify it's in the database
    count = repo.get_history_count()
    assert count == 1


def test_add_multiple_history_entries(session: Session, sample_taxa):
    """Test adding multiple entries to history."""
    repo = AnimalRepository(session=session)

    # Add multiple entries
    repo.add_to_history(taxon_id=1000, command="today")
    repo.add_to_history(taxon_id=1001, command="random")
    repo.add_to_history(taxon_id=1000, command="info")  # Same taxon, different command

    # Verify count
    count = repo.get_history_count()
    assert count == 3

    # Verify we can see the same animal twice
    history, total = repo.get_history(page=1, per_page=10)
    assert total == 3
    assert len(history) == 3


def test_get_history_pagination(session: Session, sample_taxa):
    """Test history pagination."""
    repo = AnimalRepository(session=session)

    # Add 15 entries
    for i in range(15):
        repo.add_to_history(taxon_id=1000 + i, command="test")

    # Get first page (10 per page)
    page1, total = repo.get_history(page=1, per_page=10)
    assert total == 15
    assert len(page1) == 10

    # Get second page
    page2, total = repo.get_history(page=2, per_page=10)
    assert total == 15
    assert len(page2) == 5

    # Get third page (should be empty)
    page3, total = repo.get_history(page=3, per_page=10)
    assert total == 15
    assert len(page3) == 0


def test_get_history_custom_per_page(session: Session, sample_taxa):
    """Test history with custom per_page value."""
    repo = AnimalRepository(session=session)

    # Add 15 entries
    for i in range(15):
        repo.add_to_history(taxon_id=1000 + i, command="test")

    # Get with 5 per page
    page1, total = repo.get_history(page=1, per_page=5)
    assert total == 15
    assert len(page1) == 5

    # Get page 3
    page3, total = repo.get_history(page=3, per_page=5)
    assert total == 15
    assert len(page3) == 5


def test_history_ordering(session: Session, sample_taxa):
    """Test that history is ordered from most recent to oldest."""
    repo = AnimalRepository(session=session)

    # Add entries with small delays to ensure different timestamps
    taxon_ids = [1000, 1001, 1002]
    for taxon_id in taxon_ids:
        repo.add_to_history(taxon_id=taxon_id, command="test")

    # Get history
    history, _ = repo.get_history(page=1, per_page=10)

    # Verify order (most recent first)
    assert len(history) == 3
    assert history[0].taxon.taxon_id == 1002  # Last added
    assert history[1].taxon.taxon_id == 1001
    assert history[2].taxon.taxon_id == 1000  # First added

    # Verify timestamps are in descending order
    for i in range(len(history) - 1):
        assert history[i].viewed_at >= history[i + 1].viewed_at


def test_history_empty(session: Session):
    """Test getting history when it's empty."""
    repo = AnimalRepository(session=session)

    history, total = repo.get_history(page=1, per_page=10)

    assert total == 0
    assert len(history) == 0


def test_history_metadata(session: Session, sample_taxa):
    """Test that history entries include metadata (viewed_at, command)."""
    repo = AnimalRepository(session=session)

    # Add entry
    repo.add_to_history(taxon_id=1000, command="random")

    # Get history
    history, _ = repo.get_history(page=1, per_page=10)

    assert len(history) == 1
    animal = history[0]

    # Verify metadata
    assert animal.viewed_at is not None
    assert isinstance(animal.viewed_at, datetime)
    assert animal.command == "random"

    # Verify it's still a valid AnimalInfo object
    assert isinstance(animal, AnimalInfo)
    assert animal.taxon.taxon_id == 1000


def test_clear_history(session: Session, sample_taxa):
    """Test clearing history."""
    repo = AnimalRepository(session=session)

    # Add some entries
    for i in range(5):
        repo.add_to_history(taxon_id=1000 + i, command="test")

    # Verify they're there
    assert repo.get_history_count() == 5

    # Clear history
    deleted = repo.clear_history()
    assert deleted == 5

    # Verify empty
    assert repo.get_history_count() == 0
    history, total = repo.get_history(page=1, per_page=10)
    assert total == 0
    assert len(history) == 0


def test_history_with_enrichment(session: Session, sample_taxa):
    """Test that history entries don't trigger enrichment."""
    repo = AnimalRepository(session=session)

    # Add entry
    repo.add_to_history(taxon_id=1000, command="today")

    # Get history (should not enrich)
    history, _ = repo.get_history(page=1, per_page=10)

    animal = history[0]
    # Verify basic data is there
    assert animal.taxon.taxon_id == 1000

    # Verify no enrichment data (since we didn't enrich)
    assert animal.wikidata is None
    assert animal.wikipedia is None
    assert animal.images == []


def test_history_command_types(session: Session, sample_taxa):
    """Test different command types in history."""
    repo = AnimalRepository(session=session)

    # Add entries with different commands
    commands = ["today", "random", "info", "search", None]
    for i, cmd in enumerate(commands):
        repo.add_to_history(taxon_id=1000 + i, command=cmd)

    # Get history
    history, _ = repo.get_history(page=1, per_page=10)

    # Verify all commands are preserved
    assert len(history) == 5
    commands_in_history = [animal.command for animal in history]
    # Reverse because history is newest first
    assert commands_in_history == list(reversed(commands))


def test_history_same_animal_multiple_times(session: Session, sample_taxa):
    """Test viewing the same animal multiple times appears multiple times in history."""
    repo = AnimalRepository(session=session)

    # View the same animal 3 times with different commands
    repo.add_to_history(taxon_id=1000, command="today")
    repo.add_to_history(taxon_id=1000, command="random")
    repo.add_to_history(taxon_id=1000, command="info")

    # Get history
    history, total = repo.get_history(page=1, per_page=10)

    # Should have 3 entries for the same animal
    assert total == 3
    assert len(history) == 3
    assert all(animal.taxon.taxon_id == 1000 for animal in history)

    # But different commands
    commands = [animal.command for animal in history]
    assert "today" in commands
    assert "random" in commands
    assert "info" in commands
