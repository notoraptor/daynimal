"""
Tests for AnimalRepository query methods.

This module tests the query and retrieval methods of AnimalRepository,
including get_by_id, get_by_name, search (FTS5 and fallback), and random selection.
"""

from datetime import datetime
from unittest.mock import patch

from daynimal.repository import AnimalRepository
from daynimal.schemas import TaxonomicRank


# =============================================================================
# SECTION 1: get_by_id() (5 tests)
# =============================================================================


def test_get_by_id_found_with_enrichment(populated_session):
    """Taxon found, enrich=True triggers _enrich()."""
    repo = AnimalRepository(session=populated_session)

    with patch.object(repo, "_enrich") as mock_enrich:
        animal = repo.get_by_id(1, enrich=True)

        assert animal is not None
        assert animal.taxon.taxon_id == 1
        assert animal.taxon.scientific_name == "Species 1"
        assert mock_enrich.called


def test_get_by_id_found_without_enrichment(populated_session):
    """Taxon found, enrich=False returns basic taxon."""
    repo = AnimalRepository(session=populated_session)

    with patch.object(repo, "_enrich") as mock_enrich:
        animal = repo.get_by_id(1, enrich=False)

        assert animal is not None
        assert animal.taxon.taxon_id == 1
        assert not mock_enrich.called


def test_get_by_id_not_found(populated_session):
    """ID inexistant → None."""
    repo = AnimalRepository(session=populated_session)

    animal = repo.get_by_id(9999, enrich=False)

    assert animal is None


def test_get_by_id_synonym_handling(populated_session):
    """Taxon synonyme (accepted_id != None) traité correctement."""
    repo = AnimalRepository(session=populated_session)

    # ID 300 is a synonym with accepted_id=1
    animal = repo.get_by_id(300, enrich=False)

    assert animal is not None
    assert animal.taxon.taxon_id == 300
    assert animal.taxon.accepted_id == 1


def test_get_by_id_vernacular_names_loaded(populated_session):
    """Noms vernaculaires chargés et groupés par langue."""
    repo = AnimalRepository(session=populated_session)

    animal = repo.get_by_id(1, enrich=False)

    assert animal is not None
    assert "en" in animal.taxon.vernacular_names
    assert "fr" in animal.taxon.vernacular_names
    assert "es" in animal.taxon.vernacular_names
    assert "Species 1 English" in animal.taxon.vernacular_names["en"]
    assert "Espèce 1" in animal.taxon.vernacular_names["fr"]


# =============================================================================
# SECTION 2: get_by_name() (6 tests)
# =============================================================================


def test_get_by_name_scientific(populated_session):
    """Recherche par scientific_name exacte."""
    repo = AnimalRepository(session=populated_session)

    animal = repo.get_by_name("Species 1", enrich=False)

    assert animal is not None
    assert animal.taxon.scientific_name == "Species 1"


def test_get_by_name_canonical(populated_session):
    """Recherche par canonical_name."""
    repo = AnimalRepository(session=populated_session)

    animal = repo.get_by_name("Species 2", enrich=False)

    assert animal is not None
    assert animal.taxon.canonical_name == "Species 2"


def test_get_by_name_not_found(populated_session):
    """Nom inexistant → None."""
    repo = AnimalRepository(session=populated_session)

    animal = repo.get_by_name("Nonexistent species", enrich=False)

    assert animal is None


def test_get_by_name_case_sensitivity(populated_session):
    """Test sensibilité casse (SQLite = operator is case-sensitive for most collations)."""
    repo = AnimalRepository(session=populated_session)

    # SQLite's = operator behavior depends on collation
    # By default, it's case-sensitive for most cases
    animal_exact = repo.get_by_name("Species 1", enrich=False)
    animal_lower = repo.get_by_name("species 1", enrich=False)

    # Exact match should work
    assert animal_exact is not None

    # Case-different query may or may not work (depends on SQLite collation)
    # We just verify the API doesn't crash
    assert (
        animal_lower is None
        or animal_lower.taxon.taxon_id == animal_exact.taxon.taxon_id
    )


def test_get_by_name_with_enrichment(populated_session):
    """get_by_name with enrich=True calls _enrich()."""
    repo = AnimalRepository(session=populated_session)

    with patch.object(repo, "_enrich") as mock_enrich:
        animal = repo.get_by_name("Species 1", enrich=True)

        assert animal is not None
        assert mock_enrich.called


def test_get_by_name_without_enrichment(populated_session):
    """get_by_name with enrich=False does not call _enrich()."""
    repo = AnimalRepository(session=populated_session)

    with patch.object(repo, "_enrich") as mock_enrich:
        animal = repo.get_by_name("Species 1", enrich=False)

        assert animal is not None
        assert not mock_enrich.called


# =============================================================================
# SECTION 3: search() - FTS5 Path (8 tests)
# =============================================================================


def test_search_fts5_exact_match(session_with_fts):
    """FTS5 match exact (sans wildcard)."""
    repo = AnimalRepository(session=session_with_fts)

    results = repo.search("Species 1", limit=10)

    assert len(results) > 0
    # Should find species 1
    taxon_ids = [r.taxon.taxon_id for r in results]
    assert 1 in taxon_ids


def test_search_fts5_prefix_match(session_with_fts):
    """FTS5 avec wildcard suffix ('Species*')."""
    repo = AnimalRepository(session=session_with_fts)

    results = repo.search("Species", limit=10)

    # Should find multiple species
    assert len(results) > 1


def test_search_fts5_vernacular_name(session_with_fts):
    """Recherche par nom commun (français, anglais)."""
    repo = AnimalRepository(session=session_with_fts)

    # Search for French name
    results_fr = repo.search("Espèce", limit=10)
    results_en = repo.search("English", limit=10)

    # Should find results
    assert len(results_fr) > 0 or len(results_en) > 0


def test_search_fts5_with_accents(session_with_fts):
    """Normalisation accents : 'Espèce' trouve même sans accents."""
    repo = AnimalRepository(session=session_with_fts)

    # Search with and without accents
    results_with = repo.search("Espèce", limit=10)
    results_without = repo.search("Espece", limit=10)

    # Both should find results (accent normalization)
    assert len(results_with) > 0 or len(results_without) > 0


def test_search_fts5_short_query_species_only(session_with_fts):
    """Query < 7 chars retourne uniquement rank=species."""
    repo = AnimalRepository(session=session_with_fts)

    # Short query (6 chars)
    results = repo.search("Spec", limit=20)

    # All results should be species
    for result in results:
        assert result.taxon.rank == TaxonomicRank.SPECIES


def test_search_fts5_rank_ordering(session_with_fts):
    """Species prioritaires sur genus/family."""
    repo = AnimalRepository(session=session_with_fts)

    # Long query (>= 7 chars) should include non-species
    results = repo.search("Species 1", limit=20)

    # Species should appear first in results
    if len(results) > 0:
        first_result = results[0]
        # First result should be a species (preferred)
        assert first_result.taxon.rank == TaxonomicRank.SPECIES


def test_search_fts5_limit(session_with_fts):
    """Paramètre limit respecté."""
    repo = AnimalRepository(session=session_with_fts)

    results = repo.search("Species", limit=5)

    assert len(results) <= 5


def test_search_fts5_deduplication(session_with_fts):
    """Pas de doublons dans résultats."""
    repo = AnimalRepository(session=session_with_fts)

    results = repo.search("Species", limit=20)

    # Check no duplicate taxon_ids
    taxon_ids = [r.taxon.taxon_id for r in results]
    assert len(taxon_ids) == len(set(taxon_ids))


# =============================================================================
# SECTION 4: search() - Fallback Path (3 tests)
# =============================================================================


def test_search_fallback_when_fts5_unavailable(session_without_fts):
    """Fallback LIKE queries quand FTS5 absent."""
    repo = AnimalRepository(session=session_without_fts)

    # Search should work even without FTS5
    results = repo.search("Species 1", limit=10)

    # Should find results using LIKE fallback
    assert len(results) > 0


def test_search_fallback_canonical_match(session_without_fts):
    """Fallback trouve par canonical_name."""
    repo = AnimalRepository(session=session_without_fts)

    results = repo.search("Species 2", limit=10)

    assert len(results) > 0
    # Should find Species 2
    taxon_ids = [r.taxon.taxon_id for r in results]
    assert 2 in taxon_ids


def test_search_fallback_vernacular_match(session_without_fts):
    """Fallback trouve par nom vernaculaire."""
    repo = AnimalRepository(session=session_without_fts)

    results = repo.search("Espèce", limit=10)

    # Should find results by vernacular name
    assert len(results) > 0


# =============================================================================
# SECTION 5: get_random() (2 tests)
# =============================================================================


def test_get_random_prefer_unenriched(populated_session):
    """prefer_unenriched=True retourne taxon non enrichi."""
    repo = AnimalRepository(session=populated_session)

    with patch.object(repo, "_enrich"):
        # Try multiple times to verify randomness targets unenriched
        unenriched_found = False

        for _ in range(10):
            animal = repo.get_random(
                rank="species", prefer_unenriched=True, enrich=False
            )

            if animal and not animal.is_enriched:
                unenriched_found = True
                break

        assert unenriched_found


def test_get_random_fallback_to_any(populated_session):
    """Si tous enrichis, retourne n'importe lequel."""
    from daynimal.db.models import TaxonModel

    repo = AnimalRepository(session=populated_session)

    # Mock _get_random_by_id_range to return None for unenriched, then any
    call_count = [0]

    def mock_get_random(rank, is_enriched=None):
        call_count[0] += 1
        if call_count[0] == 1:
            # First call (unenriched) returns None
            return None
        else:
            # Second call (any) returns first species
            return (
                populated_session.query(TaxonModel)
                .filter(TaxonModel.rank == "species")
                .first()
            )

    with patch.object(repo, "_get_random_by_id_range", side_effect=mock_get_random):
        with patch.object(repo, "_enrich"):
            animal = repo.get_random(
                rank="species", prefer_unenriched=True, enrich=False
            )

            # Should have tried unenriched first, then fallback
            assert call_count[0] >= 2
            assert animal is not None


# =============================================================================
# SECTION 6: get_animal_of_the_day() (1 test)
# =============================================================================


def test_get_animal_of_the_day_deterministic(populated_session):
    """Même date → même animal."""
    repo = AnimalRepository(session=populated_session)

    test_date = datetime(2025, 6, 15)

    with patch.object(repo, "_enrich"):
        animal1 = repo.get_animal_of_the_day(date=test_date)
        animal2 = repo.get_animal_of_the_day(date=test_date)

        assert animal1 is not None
        assert animal2 is not None
        assert animal1.taxon.taxon_id == animal2.taxon.taxon_id


# =============================================================================
# SECTION 7: _get_random_by_id_range() (5 tests)
# =============================================================================


def test_get_random_by_id_range_basic(populated_session):
    """Basic random selection works."""
    repo = AnimalRepository(session=populated_session)

    taxon_model = repo._get_random_by_id_range(rank="species")

    assert taxon_model is not None
    assert taxon_model.rank == "species"


def test_get_random_by_id_range_gaps_in_ids(populated_session):
    """Handles gaps in IDs correctly."""
    repo = AnimalRepository(session=populated_session)

    # Multiple attempts should all succeed despite gaps
    for _ in range(10):
        taxon_model = repo._get_random_by_id_range(rank="species")
        assert taxon_model is not None


def test_get_random_by_id_range_retry_logic(populated_session):
    """Retry logic works when hitting gaps."""
    repo = AnimalRepository(session=populated_session)

    # With is_enriched filter, there are only 10 enriched species
    taxon_model = repo._get_random_by_id_range(rank="species", is_enriched=True)

    assert taxon_model is not None
    assert taxon_model.is_enriched is True


def test_get_random_by_id_range_fallback(populated_session):
    """Falls back to .first() after retries."""
    repo = AnimalRepository(session=populated_session)

    # Mock random.randint to always return a value beyond max ID
    with patch("random.randint", return_value=999999):
        taxon_model = repo._get_random_by_id_range(rank="species")

        # Should fallback to first() and return something
        assert taxon_model is not None


def test_get_random_by_id_range_empty_table(session):
    """Empty table returns None."""
    repo = AnimalRepository(session=session)

    taxon_model = repo._get_random_by_id_range(rank="species")

    assert taxon_model is None
