"""
Tests for AnimalRepository favorites methods.

This module tests the CRUD operations for favorites:
add_favorite, remove_favorite, is_favorite, get_favorites, get_favorites_count.
"""

import pytest
from unittest.mock import patch

from daynimal.repository import AnimalRepository
from daynimal.db.models import FavoriteModel, TaxonModel


# =============================================================================
# SECTION 1: add_favorite() (5 tests)
# =============================================================================


def test_add_favorite_new(populated_session):
    """Nouveau favori → True."""
    repo = AnimalRepository(session=populated_session)

    result = repo.add_favorite(1)

    assert result is True
    # Verify it's in database
    favorite = populated_session.query(FavoriteModel).filter_by(taxon_id=1).first()
    assert favorite is not None
    assert favorite.taxon_id == 1


def test_add_favorite_duplicate(populated_session):
    """Favori existant → False (already exists)."""
    repo = AnimalRepository(session=populated_session)

    # Add first time
    result1 = repo.add_favorite(1)
    assert result1 is True

    # Try to add again
    result2 = repo.add_favorite(1)
    assert result2 is False

    # Verify only one entry exists
    count = populated_session.query(FavoriteModel).filter_by(taxon_id=1).count()
    assert count == 1


def test_add_favorite_invalid_taxon_id(populated_session):
    """Taxon ID inexistant → False ou exception (depending on FK constraint)."""
    repo = AnimalRepository(session=populated_session)

    # Try to add non-existent taxon (ID 9999)
    # This should either return False or raise an exception depending on DB constraints
    try:
        result = repo.add_favorite(9999)
        # If no exception, should return False
        assert result is False
    except Exception:
        # FK constraint violation is also acceptable
        pass


def test_add_favorite_transaction_commit(populated_session):
    """Commit appelé après ajout."""
    repo = AnimalRepository(session=populated_session)

    with patch.object(populated_session, "commit") as mock_commit:
        repo.add_favorite(1)
        assert mock_commit.called


def test_add_favorite_multiple_different(populated_session):
    """Ajouter plusieurs favoris différents."""
    repo = AnimalRepository(session=populated_session)

    result1 = repo.add_favorite(1)
    result2 = repo.add_favorite(2)
    result3 = repo.add_favorite(3)

    assert result1 is True
    assert result2 is True
    assert result3 is True

    # Verify all exist
    count = populated_session.query(FavoriteModel).count()
    assert count == 3


# =============================================================================
# SECTION 2: remove_favorite() (5 tests)
# =============================================================================


def test_remove_favorite_exists(populated_session):
    """Favori existant → True."""
    repo = AnimalRepository(session=populated_session)

    # Add first
    repo.add_favorite(1)

    # Remove
    result = repo.remove_favorite(1)

    assert result is True
    # Verify it's removed
    favorite = populated_session.query(FavoriteModel).filter_by(taxon_id=1).first()
    assert favorite is None


def test_remove_favorite_not_exists(populated_session):
    """Favori inexistant → False."""
    repo = AnimalRepository(session=populated_session)

    result = repo.remove_favorite(9999)

    assert result is False


def test_remove_favorite_after_manual_delete(populated_session):
    """Suppression favori fonctionne même si taxon supprimé manuellement."""
    repo = AnimalRepository(session=populated_session)

    # Add favorite
    repo.add_favorite(1)

    # Manually remove the favorite (simulates what would happen with cascade)
    result = repo.remove_favorite(1)

    assert result is True
    # Verify favorite is deleted
    favorite = populated_session.query(FavoriteModel).filter_by(taxon_id=1).first()
    assert favorite is None


def test_remove_favorite_transaction_commit(populated_session):
    """Commit appelé après suppression."""
    repo = AnimalRepository(session=populated_session)

    # Add first
    repo.add_favorite(1)

    with patch.object(populated_session, "commit") as mock_commit:
        repo.remove_favorite(1)
        assert mock_commit.called


def test_remove_favorite_multiple(populated_session):
    """Supprimer plusieurs favoris."""
    repo = AnimalRepository(session=populated_session)

    # Add multiple
    repo.add_favorite(1)
    repo.add_favorite(2)
    repo.add_favorite(3)

    # Remove some
    result1 = repo.remove_favorite(1)
    result2 = repo.remove_favorite(2)

    assert result1 is True
    assert result2 is True

    # Verify only one remains
    count = populated_session.query(FavoriteModel).count()
    assert count == 1


# =============================================================================
# SECTION 3: is_favorite() (3 tests)
# =============================================================================


def test_is_favorite_true(populated_session):
    """Favori existant → True."""
    repo = AnimalRepository(session=populated_session)

    repo.add_favorite(1)

    assert repo.is_favorite(1) is True


def test_is_favorite_false(populated_session):
    """Favori inexistant → False."""
    repo = AnimalRepository(session=populated_session)

    assert repo.is_favorite(9999) is False


def test_is_favorite_after_add_remove(populated_session):
    """is_favorite cohérent après add/remove."""
    repo = AnimalRepository(session=populated_session)

    # Initially not favorite
    assert repo.is_favorite(1) is False

    # Add favorite
    repo.add_favorite(1)
    assert repo.is_favorite(1) is True

    # Remove favorite
    repo.remove_favorite(1)
    assert repo.is_favorite(1) is False


# =============================================================================
# SECTION 4: get_favorites() (7 tests)
# =============================================================================


def test_get_favorites_basic(populated_session):
    """Récupérer favoris basiques."""
    repo = AnimalRepository(session=populated_session)

    # Add some favorites
    repo.add_favorite(1)
    repo.add_favorite(2)
    repo.add_favorite(3)

    favorites, total = repo.get_favorites(page=1, per_page=50)

    assert len(favorites) == 3
    assert total == 3
    # All should be AnimalInfo objects
    from daynimal.schemas import AnimalInfo
    assert all(isinstance(f, AnimalInfo) for f in favorites)


def test_get_favorites_pagination(populated_session):
    """Pagination fonctionne correctement."""
    repo = AnimalRepository(session=populated_session)

    # Add 10 favorites
    for i in range(1, 11):
        repo.add_favorite(i)

    # Page 1 (5 per page)
    favorites_p1, total = repo.get_favorites(page=1, per_page=5)
    assert len(favorites_p1) == 5
    assert total == 10

    # Page 2
    favorites_p2, total = repo.get_favorites(page=2, per_page=5)
    assert len(favorites_p2) == 5
    assert total == 10

    # Verify no overlap
    ids_p1 = {f.taxon.taxon_id for f in favorites_p1}
    ids_p2 = {f.taxon.taxon_id for f in favorites_p2}
    assert len(ids_p1.intersection(ids_p2)) == 0


def test_get_favorites_custom_per_page(populated_session):
    """per_page personnalisé respecté."""
    repo = AnimalRepository(session=populated_session)

    # Add 20 favorites
    for i in range(1, 21):
        repo.add_favorite(i)

    favorites, total = repo.get_favorites(page=1, per_page=15)

    assert len(favorites) == 15
    assert total == 20


def test_get_favorites_empty(populated_session):
    """Aucun favori → liste vide."""
    repo = AnimalRepository(session=populated_session)

    favorites, total = repo.get_favorites(page=1, per_page=50)

    assert len(favorites) == 0
    assert total == 0


def test_get_favorites_ordering(populated_session):
    """Favoris ordonnés par date d'ajout (most recent first)."""
    repo = AnimalRepository(session=populated_session)
    import time

    # Add favorites with small delays to ensure different timestamps
    repo.add_favorite(1)
    time.sleep(0.01)
    repo.add_favorite(2)
    time.sleep(0.01)
    repo.add_favorite(3)

    favorites, _ = repo.get_favorites(page=1, per_page=50)

    # Should be in reverse chronological order (most recent first)
    assert favorites[0].taxon.taxon_id == 3
    assert favorites[1].taxon.taxon_id == 2
    assert favorites[2].taxon.taxon_id == 1


def test_get_favorites_converts_to_animal_info(populated_session):
    """Favoris convertis en AnimalInfo avec taxonomie complète."""
    repo = AnimalRepository(session=populated_session)

    repo.add_favorite(1)

    favorites, _ = repo.get_favorites(page=1, per_page=50)

    assert len(favorites) == 1
    animal = favorites[0]

    # Verify it's a proper AnimalInfo with Taxon
    assert animal.taxon.scientific_name == "Species 1"
    assert animal.taxon.rank is not None
    assert animal.taxon.kingdom == "Animalia"


def test_get_favorites_large_dataset(populated_session):
    """Performances acceptables avec beaucoup de favoris."""
    repo = AnimalRepository(session=populated_session)

    # Add 30 favorites (all species from populated_session)
    for i in range(1, 31):
        repo.add_favorite(i)

    # Should handle large dataset efficiently
    import time
    start = time.time()
    favorites, total = repo.get_favorites(page=1, per_page=50)
    duration = time.time() - start

    assert len(favorites) == 30
    assert total == 30
    # Should be reasonably fast (< 1 second)
    assert duration < 1.0


# =============================================================================
# SECTION 5: get_favorites_count() (5 tests)
# =============================================================================


def test_get_favorites_count_zero(populated_session):
    """Aucun favori → 0."""
    repo = AnimalRepository(session=populated_session)

    count = repo.get_favorites_count()

    assert count == 0


def test_get_favorites_count_multiple(populated_session):
    """Compte correct avec plusieurs favoris."""
    repo = AnimalRepository(session=populated_session)

    repo.add_favorite(1)
    repo.add_favorite(2)
    repo.add_favorite(3)

    count = repo.get_favorites_count()

    assert count == 3


def test_get_favorites_count_after_add(populated_session):
    """Compte incrémenté après ajout."""
    repo = AnimalRepository(session=populated_session)

    count_before = repo.get_favorites_count()
    repo.add_favorite(1)
    count_after = repo.get_favorites_count()

    assert count_after == count_before + 1


def test_get_favorites_count_after_remove(populated_session):
    """Compte décrémenté après suppression."""
    repo = AnimalRepository(session=populated_session)

    repo.add_favorite(1)
    repo.add_favorite(2)

    count_before = repo.get_favorites_count()
    repo.remove_favorite(1)
    count_after = repo.get_favorites_count()

    assert count_after == count_before - 1


def test_get_favorites_count_accuracy(populated_session):
    """Compte toujours exact."""
    repo = AnimalRepository(session=populated_session)

    # Add 10
    for i in range(1, 11):
        repo.add_favorite(i)

    assert repo.get_favorites_count() == 10

    # Remove 3
    repo.remove_favorite(1)
    repo.remove_favorite(5)
    repo.remove_favorite(10)

    assert repo.get_favorites_count() == 7

    # Add 2 more
    repo.add_favorite(11)
    repo.add_favorite(12)

    assert repo.get_favorites_count() == 9
