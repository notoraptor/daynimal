"""Tests for AppState."""

import pytest

from daynimal.repository import AnimalRepository
from daynimal.schemas import AnimalInfo, Taxon
from daynimal.ui.state import AppState


def test_app_state_initialization():
    """Test AppState initializes with correct defaults."""
    state = AppState()

    assert state.current_animal is None
    assert state.current_image_index == 0
    assert state.cached_stats is None
    assert state.current_view_name == "today"
    assert state._repository is None


def test_repository_lazy_initialization():
    """Test repository is created on first access (lazy init)."""
    state = AppState()

    # Repository should not exist yet
    assert state._repository is None

    # Access repository property
    repo = state.repository

    # Repository should now be created
    assert repo is not None
    assert isinstance(repo, AnimalRepository)
    assert state._repository is repo

    # Second access should return same instance
    repo2 = state.repository
    assert repo2 is repo

    # Cleanup
    state.close_repository()


def test_close_repository():
    """Test repository is properly closed."""
    state = AppState()

    # Create repository
    repo = state.repository
    assert repo is not None

    # Close repository
    state.close_repository()

    # Repository should be None
    assert state._repository is None

    # Accessing repository again should create a new instance
    repo2 = state.repository
    assert repo2 is not None
    assert repo2 is not repo  # Different instance

    # Cleanup
    state.close_repository()


def test_close_repository_when_none():
    """Test closing repository when it's None doesn't raise error."""
    state = AppState()

    # Repository not created yet
    assert state._repository is None

    # Should not raise error
    state.close_repository()

    assert state._repository is None


def test_reset_animal_display():
    """Test reset_animal_display clears animal state."""
    state = AppState()

    # Create mock animal
    taxon = Taxon(
        taxon_id=1,
        scientific_name="Test species",
        canonical_name="Test",
        rank="species",
        kingdom="Animalia",
        phylum="Chordata",
        class_="Mammalia",
        order="Carnivora",
        family="Felidae",
        genus="Test",
        parent_id=None,
    )
    animal = AnimalInfo(taxon=taxon)

    # Set animal state
    state.current_animal = animal
    state.current_image_index = 5

    # Reset
    state.reset_animal_display()

    # Should be cleared
    assert state.current_animal is None
    assert state.current_image_index == 0


def test_app_state_can_store_cached_stats():
    """Test AppState can store and retrieve cached stats."""
    state = AppState()

    stats = {
        "total_taxa": 1000,
        "species_count": 500,
        "enriched_count": 250,
        "history_count": 50,
    }

    state.cached_stats = stats

    assert state.cached_stats == stats
    assert state.cached_stats["total_taxa"] == 1000
