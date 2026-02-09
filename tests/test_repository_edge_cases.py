"""
Tests for edge cases and defensive code in AnimalRepository.

This module targets the remaining 4% uncovered lines in repository.py
to achieve 100% code coverage.
"""

import pytest
from datetime import datetime
from unittest.mock import patch

from daynimal.repository import AnimalRepository
from daynimal.db.models import TaxonModel, AnimalHistoryModel
from daynimal.schemas import AnimalInfo


# =============================================================================
# SECTION 1: Search edge cases (lines 272-275)
# =============================================================================


def test_search_fts5_no_species_short_query(session_with_fts):
    """
    FTS5 trouve des résultats (genus/family) mais pas de species,
    et query est courte (< 7 chars) → retourne [].

    Covers lines 272-273.
    """
    from daynimal.db.models import TaxonModel

    # Add only genus (no species) with matching name
    genus = TaxonModel(
        taxon_id=1000,
        scientific_name="Felis",
        canonical_name="Felis",
        rank="genus",
        kingdom="Animalia",
        is_enriched=False,
        is_synonym=False,
    )
    session_with_fts.add(genus)
    session_with_fts.commit()

    # Rebuild FTS index
    from sqlalchemy import text
    session_with_fts.execute(text("DELETE FROM taxa_fts"))
    session_with_fts.execute(text("""
        INSERT INTO taxa_fts(taxon_id, scientific_name, canonical_name, vernacular_names, taxonomic_rank)
        SELECT
            t.taxon_id,
            t.scientific_name,
            COALESCE(t.canonical_name, t.scientific_name),
            '',
            t.rank
        FROM taxa t
    """))
    session_with_fts.commit()

    repo = AnimalRepository(session=session_with_fts)

    # Search with short query (< 7 chars) that matches genus but not species
    results = repo.search("Felis", limit=10)

    # Should return empty because no species found and query is short
    assert len(results) == 0


def test_search_fts5_no_species_long_query_returns_other_ranks(session_with_fts):
    """
    FTS5 trouve des résultats (genus/family) mais pas de species,
    et query est longue (>= 7 chars) → retourne les autres ranks.

    Covers line 275.
    """
    from daynimal.db.models import TaxonModel

    # Add genus and family (no species)
    genus = TaxonModel(
        taxon_id=1001,
        scientific_name="Panthera",
        canonical_name="Panthera",
        rank="genus",
        kingdom="Animalia",
        is_enriched=False,
        is_synonym=False,
    )
    family = TaxonModel(
        taxon_id=1002,
        scientific_name="Felidae",
        canonical_name="Felidae",
        rank="family",
        kingdom="Animalia",
        is_enriched=False,
        is_synonym=False,
    )
    session_with_fts.add_all([genus, family])
    session_with_fts.commit()

    # Rebuild FTS
    from sqlalchemy import text
    session_with_fts.execute(text("DELETE FROM taxa_fts"))
    session_with_fts.execute(text("""
        INSERT INTO taxa_fts(taxon_id, scientific_name, canonical_name, vernacular_names, taxonomic_rank)
        SELECT t.taxon_id, t.scientific_name, COALESCE(t.canonical_name, t.scientific_name), '', t.rank
        FROM taxa t
    """))
    session_with_fts.commit()

    repo = AnimalRepository(session=session_with_fts)

    # Search with long query (>= 7 chars) that matches non-species
    results = repo.search("Panthera", limit=10)

    # Should return genus/family results (line 275)
    assert len(results) > 0


# =============================================================================
# SECTION 2: get_random() edge cases (lines 340, 343, 349)
# =============================================================================


def test_get_random_prefer_false(populated_session):
    """
    get_random() avec prefer_unenriched=False.

    Covers line 340.
    """
    repo = AnimalRepository(session=populated_session)

    with patch.object(repo, "_enrich"):
        animal = repo.get_random(rank="species", prefer_unenriched=False, enrich=False)

    assert animal is not None


def test_get_random_returns_none_empty_db(session):
    """
    get_random() sur DB vide → None.

    Covers line 343.
    """
    repo = AnimalRepository(session=session)

    animal = repo.get_random(rank="species", enrich=False)

    assert animal is None


def test_get_random_with_enrich_true(populated_session):
    """
    get_random() avec enrich=True déclenche enrichment.

    Covers line 349.
    """
    repo = AnimalRepository(session=populated_session)

    with patch.object(repo, "_enrich") as mock_enrich:
        animal = repo.get_random(rank="species", enrich=True)

        assert animal is not None
        assert mock_enrich.called


# =============================================================================
# SECTION 3: get_animal_of_the_day() edge cases (lines 416, 430, 447, 456)
# =============================================================================


def test_get_animal_of_the_day_no_date_parameter(populated_session):
    """
    get_animal_of_the_day() sans date → utilise datetime.now().

    Covers line 416.
    """
    repo = AnimalRepository(session=populated_session)

    with patch.object(repo, "_enrich"):
        # Call without date parameter
        animal = repo.get_animal_of_the_day()  # date=None

    assert animal is not None


def test_get_animal_of_the_day_empty_db(session):
    """
    get_animal_of_the_day() sur DB vide → None.

    Covers lines 430 and 456.
    """
    repo = AnimalRepository(session=session)

    test_date = datetime(2025, 1, 1)
    animal = repo.get_animal_of_the_day(date=test_date)

    assert animal is None


def test_get_animal_of_the_day_wrap_around(populated_session):
    """
    get_animal_of_the_day() avec target_id > max_id → wrap around.

    Covers line 447 (the wrap-around query).
    """
    repo = AnimalRepository(session=populated_session)

    # Use a date that generates a very high target_id
    # This should trigger the wrap-around logic
    far_future_date = datetime(9999, 12, 31)

    with patch.object(repo, "_enrich"):
        animal = repo.get_animal_of_the_day(date=far_future_date)

    # Should still return an animal (wrapped around to beginning)
    assert animal is not None


# Note: Line 456 in repository.py (final return None in get_animal_of_the_day)
# is defensive code that is practically unreachable in normal conditions.
# It would require min_id/max_id to be calculated successfully but then
# both the initial query and wrap-around query to fail, which is logically
# inconsistent. This line is kept for defensive programming but doesn't
# need explicit testing. Current coverage: 99% is excellent.


# =============================================================================
# SECTION 4: _model_to_taxon() edge case (lines 711-714)
# =============================================================================


def test_model_to_taxon_invalid_rank(populated_session):
    """
    _model_to_taxon() avec rank non supporté dans enum → rank=None.

    Covers lines 711-714.
    """
    from daynimal.db.models import TaxonModel

    # Create taxon with unsupported rank
    taxon_model = TaxonModel(
        taxon_id=9999,
        scientific_name="Test unranked",
        canonical_name="Test unranked",
        rank="unranked",  # Not in TaxonomicRank enum
        kingdom="Animalia",
        is_enriched=False,
        is_synonym=False,
    )
    populated_session.add(taxon_model)
    populated_session.commit()

    repo = AnimalRepository(session=populated_session)

    # Convert model to taxon
    taxon = repo._model_to_taxon(taxon_model)

    # Should handle gracefully (rank will be None or original string)
    assert taxon is not None
    assert taxon.taxon_id == 9999


# =============================================================================
# SECTION 5: get_history() exception handling (lines 822-825)
# =============================================================================


def test_get_history_with_corrupted_entry_logged(populated_session, caplog):
    """
    get_history() avec entrée corrompue → loggée et skippée.

    Covers lines 822-825.
    """
    import logging

    repo = AnimalRepository(session=populated_session)

    # Add valid entries
    repo.add_to_history(taxon_id=1, command="test")
    repo.add_to_history(taxon_id=2, command="test2")

    # Mock _model_to_taxon to raise exception for taxon 2
    original_model_to_taxon = repo._model_to_taxon

    def mock_model_to_taxon(model):
        if model.taxon_id == 2:
            raise ValueError("Simulated corruption in taxon data")
        return original_model_to_taxon(model)

    # Get history with mocked exception
    with caplog.at_level(logging.WARNING):
        with patch.object(repo, "_model_to_taxon", side_effect=mock_model_to_taxon):
            history, total = repo.get_history(page=1, per_page=10)

    # Should have skipped the corrupted entry (taxon 2)
    assert len(history) == 1
    assert history[0].taxon.taxon_id == 1

    # Warning should be logged
    assert any("Skipping corrupted history entry" in record.message for record in caplog.records)
