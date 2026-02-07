"""
Tests for parallel API calls in AnimalRepository.

This module tests that the repository correctly parallelizes
Wikidata and Wikipedia API calls for better performance.
"""

import time
from unittest.mock import MagicMock, patch

import pytest

from daynimal.db.models import TaxonModel
from daynimal.repository import AnimalRepository
from daynimal.schemas import AnimalInfo, Taxon


@pytest.fixture
def mock_taxon_model():
    """Create a mock TaxonModel."""
    taxon = TaxonModel(
        taxon_id=1,
        scientific_name="Panthera leo",
        canonical_name="Panthera leo",
        rank="SPECIES",
        kingdom="Animalia",
        phylum="Chordata",
        class_="Mammalia",
        order="Carnivora",
        family="Felidae",
        genus="Panthera",
        is_enriched=False,
    )
    return taxon


@pytest.fixture
def animal_info():
    """Create an AnimalInfo object."""
    taxon = Taxon(
        taxon_id=1,
        scientific_name="Panthera leo",
        canonical_name="Panthera leo",
        rank="SPECIES",
        kingdom="Animalia",
        phylum="Chordata",
        class_="Mammalia",
        order="Carnivora",
        family="Felidae",
        genus="Panthera",
    )
    return AnimalInfo(taxon=taxon)


def test_parallel_api_calls_timing(mock_taxon_model, animal_info):
    """
    Test that Wikidata and Wikipedia calls are executed in parallel.

    This test verifies that parallel execution is faster than sequential
    by using mock functions with delays.
    """
    # Create a mock session
    mock_session = MagicMock()
    mock_session.commit = MagicMock()

    with (
        patch.object(AnimalRepository, "_get_cached_wikidata", return_value=None),
        patch.object(AnimalRepository, "_get_cached_wikipedia", return_value=None),
        patch.object(AnimalRepository, "_get_cached_images", return_value=[]),
        patch.object(AnimalRepository, "_fetch_and_cache_wikidata") as mock_wikidata,
        patch.object(AnimalRepository, "_fetch_and_cache_wikipedia") as mock_wikipedia,
        patch.object(AnimalRepository, "_fetch_and_cache_images") as mock_images,
    ):
        # Configure mocks to simulate API delay
        def slow_wikidata(*args):
            time.sleep(0.1)  # 100ms delay
            return None

        def slow_wikipedia(*args):
            time.sleep(0.1)  # 100ms delay
            return None

        mock_wikidata.side_effect = slow_wikidata
        mock_wikipedia.side_effect = slow_wikipedia
        mock_images.return_value = []

        repo = AnimalRepository(session=mock_session)

        # Measure execution time
        start = time.time()
        repo._enrich(animal_info, mock_taxon_model)
        duration = time.time() - start

        # With parallel execution: ~0.1s (max of both)
        # With sequential execution: ~0.2s (sum of both)
        # Allow some overhead but should be much less than 0.2s
        assert duration < 0.15, (
            f"Expected parallel execution (~0.1s), got {duration:.3f}s"
        )

        # Verify both functions were called
        assert mock_wikidata.called
        assert mock_wikipedia.called


def test_parallel_api_calls_error_handling(mock_taxon_model, animal_info):
    """
    Test that errors in one parallel call don't block the other.

    If Wikidata fails, Wikipedia should still succeed (and vice versa).
    """
    # Create a mock session
    mock_session = MagicMock()
    mock_session.commit = MagicMock()

    with (
        patch.object(AnimalRepository, "_get_cached_wikidata", return_value=None),
        patch.object(AnimalRepository, "_get_cached_wikipedia", return_value=None),
        patch.object(AnimalRepository, "_get_cached_images", return_value=[]),
        patch.object(AnimalRepository, "_fetch_and_cache_wikidata") as mock_wikidata,
        patch.object(AnimalRepository, "_fetch_and_cache_wikipedia") as mock_wikipedia,
        patch.object(AnimalRepository, "_fetch_and_cache_images") as mock_images,
    ):
        # Simulate Wikidata error but Wikipedia success
        mock_wikidata.side_effect = Exception("Wikidata API error")
        mock_wikipedia.return_value = MagicMock()  # Success
        mock_images.return_value = []

        repo = AnimalRepository(session=mock_session)

        # Should not raise exception
        repo._enrich(animal_info, mock_taxon_model)

        # Wikipedia should still have been called and succeeded
        assert mock_wikipedia.called
        # Wikidata should be None due to error
        assert animal_info.wikidata is None
        # Wikipedia should have succeeded
        assert animal_info.wikipedia is not None


def test_only_missing_data_fetched(mock_taxon_model, animal_info):
    """
    Test that only missing data is fetched from APIs.

    If data is already cached, it should not be fetched again.
    """
    mock_wikidata_cached = MagicMock()
    mock_wikipedia_cached = MagicMock()

    # Create a mock session
    mock_session = MagicMock()
    mock_session.commit = MagicMock()

    with (
        patch.object(
            AnimalRepository, "_get_cached_wikidata", return_value=mock_wikidata_cached
        ),
        patch.object(
            AnimalRepository,
            "_get_cached_wikipedia",
            return_value=mock_wikipedia_cached,
        ),
        patch.object(AnimalRepository, "_get_cached_images", return_value=[]),
        patch.object(AnimalRepository, "_fetch_and_cache_wikidata") as mock_fetch_wd,
        patch.object(AnimalRepository, "_fetch_and_cache_wikipedia") as mock_fetch_wp,
        patch.object(AnimalRepository, "_fetch_and_cache_images") as mock_fetch_img,
    ):
        mock_fetch_img.return_value = []

        repo = AnimalRepository(session=mock_session)

        repo._enrich(animal_info, mock_taxon_model)

        # Should not fetch Wikidata or Wikipedia (already cached)
        assert not mock_fetch_wd.called
        assert not mock_fetch_wp.called

        # Should fetch images (not cached)
        assert mock_fetch_img.called

        # Cached data should be used
        assert animal_info.wikidata == mock_wikidata_cached
        assert animal_info.wikipedia == mock_wikipedia_cached


def test_images_fetched_after_parallel_calls(mock_taxon_model, animal_info):
    """
    Test that images are fetched after Wikidata/Wikipedia (sequential).

    Images may depend on Wikidata results, so they must be fetched after.
    """
    call_order = []

    def track_wikidata(*args):
        call_order.append("wikidata")
        return None

    def track_wikipedia(*args):
        call_order.append("wikipedia")
        return None

    def track_images(*args):
        call_order.append("images")
        return []

    # Create a mock session
    mock_session = MagicMock()
    mock_session.commit = MagicMock()

    with (
        patch.object(AnimalRepository, "_get_cached_wikidata", return_value=None),
        patch.object(AnimalRepository, "_get_cached_wikipedia", return_value=None),
        patch.object(AnimalRepository, "_get_cached_images", return_value=[]),
        patch.object(
            AnimalRepository, "_fetch_and_cache_wikidata", side_effect=track_wikidata
        ),
        patch.object(
            AnimalRepository, "_fetch_and_cache_wikipedia", side_effect=track_wikipedia
        ),
        patch.object(
            AnimalRepository, "_fetch_and_cache_images", side_effect=track_images
        ),
    ):
        repo = AnimalRepository(session=mock_session)

        repo._enrich(animal_info, mock_taxon_model)

        # Verify images was called after wikidata and wikipedia
        assert "images" in call_order
        assert call_order.index("images") > call_order.index("wikidata")
        assert call_order.index("images") > call_order.index("wikipedia")


def test_enrichment_flag_set(mock_taxon_model, animal_info):
    """Test that is_enriched flag is set after enrichment."""
    # Create a mock session
    mock_session = MagicMock()
    mock_session.commit = MagicMock()

    with (
        patch.object(AnimalRepository, "_get_cached_wikidata", return_value=None),
        patch.object(AnimalRepository, "_get_cached_wikipedia", return_value=None),
        patch.object(AnimalRepository, "_get_cached_images", return_value=[]),
        patch.object(AnimalRepository, "_fetch_and_cache_wikidata", return_value=None),
        patch.object(AnimalRepository, "_fetch_and_cache_wikipedia", return_value=None),
        patch.object(AnimalRepository, "_fetch_and_cache_images", return_value=[]),
    ):
        repo = AnimalRepository(session=mock_session)

        # Initially not enriched
        assert not mock_taxon_model.is_enriched
        assert not animal_info.is_enriched

        repo._enrich(animal_info, mock_taxon_model)

        # Should be marked as enriched
        assert mock_taxon_model.is_enriched
        assert animal_info.is_enriched
        assert mock_taxon_model.enriched_at is not None
        assert mock_session.commit.called
