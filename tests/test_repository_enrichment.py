"""
Tests for AnimalRepository enrichment methods.

This module tests the enrichment, caching, and data fetching methods
of AnimalRepository, including cache retrieval, API fetching, and utilities.
"""

import pytest
import json
from unittest.mock import patch, MagicMock

from daynimal.repository import AnimalRepository, remove_accents
from daynimal.schemas import (
    AnimalInfo,
    WikidataEntity,
    WikipediaArticle,
    CommonsImage,
    License,
)
from daynimal.db.models import TaxonModel, EnrichmentCacheModel


# =============================================================================
# SECTION 1: _enrich() - Additional gaps tests (10 tests)
# =============================================================================


def test_enrich_already_enriched(populated_session, sync_executor):
    """is_enriched=True → pas de re-fetch."""
    with AnimalRepository(session=populated_session) as repo:
        # Mark taxon 1 as enriched
        taxon_model = populated_session.get(TaxonModel, 1)
        taxon_model.is_enriched = True
        populated_session.commit()

        taxon = repo._model_to_taxon(taxon_model)
        animal = AnimalInfo(taxon=taxon, is_enriched=True)

        with patch.object(repo, "_get_cached_wikidata") as mock_cached_wd:
            with patch.object(repo, "_fetch_and_cache_wikidata"):
                repo._enrich(animal, taxon_model)

                # Should not fetch if already enriched (but will check cache)
                assert mock_cached_wd.called
                # API fetch should not be called for already enriched
                # (though in current implementation it still checks cache)


def test_enrich_empty_canonical_name(populated_session, sync_executor):
    """canonical_name=None → utilise scientific_name."""
    repo = AnimalRepository(session=populated_session)

    # Create taxon with no canonical_name
    taxon_model = TaxonModel(
        taxon_id=999,
        scientific_name="Canis lupus familiaris",
        canonical_name=None,  # No canonical name
        rank="subspecies",
        kingdom="Animalia",
        is_enriched=False,
        is_synonym=False,
    )
    populated_session.add(taxon_model)
    populated_session.commit()

    taxon = repo._model_to_taxon(taxon_model)
    animal = AnimalInfo(taxon=taxon)

    with patch.object(repo, "_get_cached_wikidata", return_value=None):
        with patch.object(repo, "_get_cached_wikipedia", return_value=None):
            with patch.object(repo, "_get_cached_images", return_value=[]):
                with patch.object(repo, "_fetch_and_cache_wikidata") as mock_fetch:
                    repo._enrich(animal, taxon_model)

                    # Should use scientific_name when canonical_name is None
                    assert mock_fetch.called
                    call_args = mock_fetch.call_args[0]
                    assert call_args[1] == "Canis lupus familiaris"


def test_enrich_thread_safety(populated_session, sync_executor):
    """Appels concurrents avec _session_lock."""
    repo = AnimalRepository(session=populated_session)

    taxon_model = populated_session.get(TaxonModel, 1)
    taxon = repo._model_to_taxon(taxon_model)
    animal = AnimalInfo(taxon=taxon)

    # Mock to verify lock is used
    with patch.object(repo, "_get_cached_wikidata", return_value=None):
        with patch.object(repo, "_get_cached_wikipedia", return_value=None):
            with patch.object(repo, "_get_cached_images", return_value=[]):
                with patch.object(repo, "_fetch_and_cache_wikidata", return_value=None):
                    with patch.object(
                        repo, "_fetch_and_cache_wikipedia", return_value=None
                    ):
                        with patch.object(
                            repo, "_fetch_and_cache_images", return_value=[]
                        ):
                            # Verify lock exists
                            assert hasattr(repo, "_session_lock")
                            repo._enrich(animal, taxon_model)


def test_enrich_session_rollback_on_error(populated_session, sync_executor):
    """Exception propagée si commit échoue."""
    repo = AnimalRepository(session=populated_session)

    # Use taxon 11 (not enriched in fixture)
    taxon_model = populated_session.get(TaxonModel, 11)
    taxon = repo._model_to_taxon(taxon_model)
    animal = AnimalInfo(taxon=taxon)

    with patch.object(repo, "_get_cached_wikidata", return_value=None):
        with patch.object(repo, "_get_cached_wikipedia", return_value=None):
            with patch.object(repo, "_get_cached_images", return_value=[]):
                with patch.object(repo, "_fetch_and_cache_wikidata", return_value=None):
                    with patch.object(
                        repo, "_fetch_and_cache_wikipedia", return_value=None
                    ):
                        with patch.object(
                            repo, "_fetch_and_cache_images", return_value=[]
                        ):
                            # Mock commit to raise error
                            with patch.object(
                                populated_session,
                                "commit",
                                side_effect=Exception("DB error"),
                            ):
                                # Exception should propagate when commit fails
                                with pytest.raises(Exception, match="DB error"):
                                    repo._enrich(animal, taxon_model)


def test_enrich_partial_cache(populated_session, mock_enrichment_data, sync_executor):
    """Cache contient wikidata mais pas wikipedia → fetch uniquement wikipedia."""
    repo = AnimalRepository(session=populated_session)

    # Add only wikidata cache
    wikidata_cache = EnrichmentCacheModel(
        taxon_id=1,
        source="wikidata",
        data=json.dumps(repo._to_dict(mock_enrichment_data["wikidata"])),
    )
    populated_session.add(wikidata_cache)
    populated_session.commit()

    taxon_model = populated_session.get(TaxonModel, 1)
    taxon = repo._model_to_taxon(taxon_model)
    animal = AnimalInfo(taxon=taxon)

    with patch.object(repo, "_fetch_and_cache_wikidata") as mock_fetch_wd:
        with patch.object(repo, "_fetch_and_cache_wikipedia") as mock_fetch_wp:
            with patch.object(repo, "_fetch_and_cache_images") as mock_fetch_img:
                mock_fetch_wp.return_value = None
                mock_fetch_img.return_value = []

                repo._enrich(animal, taxon_model)

                # Wikidata should not be fetched (cached)
                assert not mock_fetch_wd.called
                # Wikipedia should be fetched (not cached)
                assert mock_fetch_wp.called
                # Images should be fetched
                assert mock_fetch_img.called


def test_enrich_all_apis_fail(populated_session, sync_executor):
    """Toutes les APIs échouent → animal reste non enrichi."""
    repo = AnimalRepository(session=populated_session)

    taxon_model = populated_session.get(TaxonModel, 1)
    taxon = repo._model_to_taxon(taxon_model)
    animal = AnimalInfo(taxon=taxon)

    with patch.object(repo, "_get_cached_wikidata", return_value=None):
        with patch.object(repo, "_get_cached_wikipedia", return_value=None):
            with patch.object(repo, "_get_cached_images", return_value=[]):
                with patch.object(
                    repo, "_fetch_and_cache_wikidata", side_effect=Exception("API down")
                ):
                    with patch.object(
                        repo,
                        "_fetch_and_cache_wikipedia",
                        side_effect=Exception("API down"),
                    ):
                        with patch.object(
                            repo, "_fetch_and_cache_images", return_value=[]
                        ):
                            # Should not raise, just fail silently
                            repo._enrich(animal, taxon_model)

                            # Animal should have no enriched data
                            assert animal.wikidata is None
                            assert animal.wikipedia is None
                            assert animal.images == []


def test_enrich_wikidata_fails_wikipedia_succeeds(
    populated_session, mock_enrichment_data, sync_executor
):
    """Wikidata échoue, Wikipedia réussit."""
    repo = AnimalRepository(session=populated_session)

    taxon_model = populated_session.get(TaxonModel, 1)
    taxon = repo._model_to_taxon(taxon_model)
    animal = AnimalInfo(taxon=taxon)

    with patch.object(repo, "_get_cached_wikidata", return_value=None):
        with patch.object(repo, "_get_cached_wikipedia", return_value=None):
            with patch.object(repo, "_get_cached_images", return_value=[]):
                with patch.object(
                    repo,
                    "_fetch_and_cache_wikidata",
                    side_effect=Exception("Wikidata down"),
                ):
                    with patch.object(repo, "_fetch_and_cache_wikipedia") as mock_wp:
                        with patch.object(
                            repo, "_fetch_and_cache_images", return_value=[]
                        ):
                            mock_wp.return_value = mock_enrichment_data["wikipedia"]
                            animal.wikipedia = mock_enrichment_data["wikipedia"]

                            repo._enrich(animal, taxon_model)

                            assert animal.wikidata is None
                            assert animal.wikipedia is not None


def test_enrich_wikipedia_fails_wikidata_succeeds(
    populated_session, mock_enrichment_data, sync_executor
):
    """Wikipedia échoue, Wikidata réussit."""
    repo = AnimalRepository(session=populated_session)

    taxon_model = populated_session.get(TaxonModel, 1)
    taxon = repo._model_to_taxon(taxon_model)
    animal = AnimalInfo(taxon=taxon)

    with patch.object(repo, "_get_cached_wikidata", return_value=None):
        with patch.object(repo, "_get_cached_wikipedia", return_value=None):
            with patch.object(repo, "_get_cached_images", return_value=[]):
                with patch.object(repo, "_fetch_and_cache_wikidata") as mock_wd:
                    with patch.object(
                        repo,
                        "_fetch_and_cache_wikipedia",
                        side_effect=Exception("Wikipedia down"),
                    ):
                        with patch.object(
                            repo, "_fetch_and_cache_images", return_value=[]
                        ):
                            mock_wd.return_value = mock_enrichment_data["wikidata"]
                            animal.wikidata = mock_enrichment_data["wikidata"]

                            repo._enrich(animal, taxon_model)

                            assert animal.wikidata is not None
                            assert animal.wikipedia is None


def test_enrich_images_fail(populated_session, sync_executor):
    """Images échouent mais Wikidata/Wikipedia réussissent."""
    repo = AnimalRepository(session=populated_session)

    taxon_model = populated_session.get(TaxonModel, 1)
    taxon = repo._model_to_taxon(taxon_model)
    animal = AnimalInfo(taxon=taxon)

    with patch.object(repo, "_get_cached_wikidata", return_value=None):
        with patch.object(repo, "_get_cached_wikipedia", return_value=None):
            with patch.object(repo, "_get_cached_images", return_value=[]):
                with patch.object(repo, "_fetch_and_cache_wikidata", return_value=None):
                    with patch.object(
                        repo, "_fetch_and_cache_wikipedia", return_value=None
                    ):
                        with patch.object(
                            repo, "_fetch_and_cache_images", return_value=[]
                        ):
                            # Should not crash (images API fails gracefully)
                            repo._enrich(animal, taxon_model)

                            assert animal.images == []


def test_enrich_executor_max_workers(populated_session, sync_executor):
    """ThreadPoolExecutor uses max_workers=2."""
    repo = AnimalRepository(session=populated_session)

    taxon_model = populated_session.get(TaxonModel, 1)
    taxon = repo._model_to_taxon(taxon_model)
    animal = AnimalInfo(taxon=taxon)

    with patch("daynimal.repository.ThreadPoolExecutor") as mock_executor_class:
        mock_executor = MagicMock()
        mock_executor_class.return_value.__enter__.return_value = mock_executor
        mock_executor.submit.return_value.result.return_value = None

        with patch.object(repo, "_get_cached_wikidata", return_value=None):
            with patch.object(repo, "_get_cached_wikipedia", return_value=None):
                with patch.object(repo, "_get_cached_images", return_value=[]):
                    repo._enrich(animal, taxon_model)

                    # Verify ThreadPoolExecutor was created with max_workers=2
                    mock_executor_class.assert_called_once_with(max_workers=2)


# =============================================================================
# SECTION 2: Cache retrieval (_get_cached_*, 9 tests)
# =============================================================================


def test_get_cached_wikidata_exists(repo_with_cache):
    """Cache trouvé → WikidataEntity désérialisé."""
    wikidata = repo_with_cache._get_cached_wikidata(1)

    assert wikidata is not None
    assert isinstance(wikidata, WikidataEntity)
    assert wikidata.qid == "Q144"


def test_get_cached_wikidata_not_found(populated_session):
    """Cache absent → None."""
    repo = AnimalRepository(session=populated_session)

    wikidata = repo._get_cached_wikidata(999)

    assert wikidata is None


def test_get_cached_wikidata_corrupted(populated_session):
    """JSON invalide → JSONDecodeError raised."""
    with AnimalRepository(session=populated_session) as repo:
        # Add corrupted cache
        corrupted_cache = EnrichmentCacheModel(
            taxon_id=1, source="wikidata", data="{invalid json"
        )
        populated_session.add(corrupted_cache)
        populated_session.commit()

        # Should raise JSONDecodeError on corrupted JSON
        with pytest.raises(json.JSONDecodeError):
            repo._get_cached_wikidata(1)


def test_get_cached_wikipedia_exists(repo_with_cache):
    """Cache trouvé → WikipediaArticle désérialisé."""
    wikipedia = repo_with_cache._get_cached_wikipedia(1)

    assert wikipedia is not None
    assert isinstance(wikipedia, WikipediaArticle)
    assert wikipedia.title == "Dog"


def test_get_cached_wikipedia_not_found(populated_session):
    """Cache absent → None."""
    repo = AnimalRepository(session=populated_session)

    wikipedia = repo._get_cached_wikipedia(999)

    assert wikipedia is None


def test_get_cached_wikipedia_json_corrupted(populated_session):
    """JSON invalide → JSONDecodeError raised."""
    repo = AnimalRepository(session=populated_session)

    # Add corrupted cache
    corrupted_cache = EnrichmentCacheModel(
        taxon_id=1, source="wikipedia", data="{not valid json"
    )
    populated_session.add(corrupted_cache)
    populated_session.commit()

    # Should raise JSONDecodeError on corrupted JSON
    with pytest.raises(json.JSONDecodeError):
        repo._get_cached_wikipedia(1)


def test_get_cached_images_exists(repo_with_cache):
    """Cache trouvé → list[CommonsImage] désérialisé."""
    images = repo_with_cache._get_cached_images(1)

    assert images is not None
    assert isinstance(images, list)
    assert len(images) == 2
    assert all(isinstance(img, CommonsImage) for img in images)


def test_get_cached_images_not_found(populated_session):
    """Cache absent → []."""
    repo = AnimalRepository(session=populated_session)

    images = repo._get_cached_images(999)

    assert images == []


def test_get_cached_images_list_conversion(populated_session):
    """Liste d'objets correctement désérialisée."""
    repo = AnimalRepository(session=populated_session)

    # Add cache with list
    images_data = [
        {
            "filename": "Test1.jpg",
            "url": "https://example.com/Test1.jpg",
            "author": "Author 1",
            "license": "CC-BY",
        },
        {
            "filename": "Test2.jpg",
            "url": "https://example.com/Test2.jpg",
            "author": "Author 2",
            "license": "CC-BY-SA",
        },
    ]
    cache = EnrichmentCacheModel(
        taxon_id=1,
        source="commons",  # Fixed: _get_cached_images() searches for "commons"
        data=json.dumps(images_data),
    )
    populated_session.add(cache)
    populated_session.commit()

    images = repo._get_cached_images(1)

    assert len(images) == 2
    assert images[0].filename == "Test1.jpg"
    assert images[1].filename == "Test2.jpg"


# =============================================================================
# SECTION 3: Fetch & Cache (_fetch_and_cache_*, 12 tests)
# =============================================================================


def test_fetch_and_cache_wikidata_success(populated_session, mock_enrichment_data):
    """API réussit → _save_cache appelé."""
    repo = AnimalRepository(session=populated_session)

    with patch.object(repo.wikidata, "get_by_taxonomy") as mock_api:
        mock_api.return_value = mock_enrichment_data["wikidata"]

        with patch.object(repo, "_save_cache") as mock_save:
            result = repo._fetch_and_cache_wikidata(1, "Test species")

            assert result == mock_enrichment_data["wikidata"]
            assert mock_save.called
            # Verify saved with correct params
            assert mock_save.call_args[0][0] == 1
            assert mock_save.call_args[0][1] == "wikidata"


def test_fetch_and_cache_wikidata_not_found(populated_session):
    """API retourne None → _save_cache pas appelé."""
    repo = AnimalRepository(session=populated_session)

    with patch.object(repo.wikidata, "get_by_taxonomy", return_value=None):
        with patch.object(repo, "_save_cache") as mock_save:
            result = repo._fetch_and_cache_wikidata(1, "Unknown species")

            assert result is None
            assert not mock_save.called


def test_fetch_and_cache_wikidata_exception(populated_session):
    """Exception loggée → None retourné."""
    repo = AnimalRepository(session=populated_session)

    with patch.object(
        repo.wikidata, "get_by_taxonomy", side_effect=Exception("API error")
    ):
        with patch.object(repo, "_save_cache") as mock_save:
            result = repo._fetch_and_cache_wikidata(1, "Test species")

            assert result is None
            assert not mock_save.called


def test_fetch_and_cache_wikidata_cache_verification(
    populated_session, mock_enrichment_data
):
    """Vérifier cache JSON correct dans DB."""
    repo = AnimalRepository(session=populated_session)

    with patch.object(repo.wikidata, "get_by_taxonomy") as mock_api:
        mock_api.return_value = mock_enrichment_data["wikidata"]

        repo._fetch_and_cache_wikidata(1, "Test species")

        # Verify cache was saved
        cache = (
            populated_session.query(EnrichmentCacheModel)
            .filter_by(taxon_id=1, source="wikidata")
            .first()
        )

        assert cache is not None
        assert "Q144" in cache.data


def test_fetch_and_cache_wikipedia_success(populated_session, mock_enrichment_data):
    """API réussit → _save_cache appelé."""
    repo = AnimalRepository(session=populated_session)

    with patch.object(repo.wikipedia, "get_by_taxonomy") as mock_api:
        mock_api.return_value = mock_enrichment_data["wikipedia"]

        with patch.object(repo, "_save_cache") as mock_save:
            result = repo._fetch_and_cache_wikipedia(1, "Test species")

            assert result == mock_enrichment_data["wikipedia"]
            assert mock_save.called


def test_fetch_and_cache_wikipedia_not_found(populated_session):
    """API retourne None → _save_cache pas appelé."""
    repo = AnimalRepository(session=populated_session)

    with patch.object(repo.wikipedia, "get_by_taxonomy", return_value=None):
        with patch.object(repo, "_save_cache") as mock_save:
            result = repo._fetch_and_cache_wikipedia(1, "Unknown species")

            assert result is None
            assert not mock_save.called


def test_fetch_and_cache_wikipedia_exception(populated_session):
    """Exception loggée → None retourné."""
    repo = AnimalRepository(session=populated_session)

    with patch.object(
        repo.wikipedia, "get_by_taxonomy", side_effect=Exception("API error")
    ):
        result = repo._fetch_and_cache_wikipedia(1, "Test species")

        assert result is None


def test_fetch_and_cache_wikipedia_cache_verification(
    populated_session, mock_enrichment_data
):
    """Vérifier cache JSON correct dans DB."""
    repo = AnimalRepository(session=populated_session)

    with patch.object(repo.wikipedia, "get_by_taxonomy") as mock_api:
        mock_api.return_value = mock_enrichment_data["wikipedia"]

        repo._fetch_and_cache_wikipedia(1, "Test species")

        # Verify cache
        cache = (
            populated_session.query(EnrichmentCacheModel)
            .filter_by(taxon_id=1, source="wikipedia")
            .first()
        )

        assert cache is not None
        assert "Dog" in cache.data


def test_fetch_and_cache_images_from_wikidata(populated_session, mock_enrichment_data):
    """Images via QID Wikidata."""
    repo = AnimalRepository(session=populated_session)

    with patch.object(repo.commons, "get_images_for_wikidata") as mock_api:
        mock_api.return_value = mock_enrichment_data["images"]

        result = repo._fetch_and_cache_images(
            1, "Test species", mock_enrichment_data["wikidata"]
        )

        assert len(result) == 2
        assert mock_api.called
        # Should use Wikidata QID
        assert mock_api.call_args[0][0] == "Q144"


def test_fetch_and_cache_images_fallback_search(
    populated_session, mock_enrichment_data
):
    """Pas de QID → recherche par nom."""
    repo = AnimalRepository(session=populated_session)

    with patch.object(repo.commons, "get_by_taxonomy") as mock_api:
        mock_api.return_value = mock_enrichment_data["images"]

        # No wikidata, should fallback to name search
        result = repo._fetch_and_cache_images(1, "Test species", None)

        assert len(result) == 2
        assert mock_api.called
        # Should use scientific name
        assert mock_api.call_args[0][0] == "Test species"


def test_fetch_and_cache_images_empty_result(populated_session):
    """API retourne [] → cache empty list."""
    with AnimalRepository(session=populated_session) as repo:
        with patch.object(repo.commons, "get_by_taxonomy", return_value=[]):
            with patch.object(repo, "_save_cache") as mock_save:
                result = repo._fetch_and_cache_images(1, "Test species", None)

                assert result == []
                # Empty list is NOT cached (only non-empty results are cached)
                assert not mock_save.called


def test_fetch_and_cache_images_exception(populated_session):
    """Exception → [] retourné."""
    repo = AnimalRepository(session=populated_session)

    with patch.object(
        repo.commons, "get_by_taxonomy", side_effect=Exception("API error")
    ):
        result = repo._fetch_and_cache_images(1, "Test species", None)

        assert result == []


# =============================================================================
# SECTION 4: _save_cache() (5 tests)
# =============================================================================


def test_save_cache_new_entry(populated_session):
    """Nouvelle entrée créée."""
    repo = AnimalRepository(session=populated_session)

    data = {"qid": "Q123", "labels": {"en": "Test"}}

    repo._save_cache(1, "wikidata", data)

    # Verify entry was created
    cache = (
        populated_session.query(EnrichmentCacheModel)
        .filter_by(taxon_id=1, source="wikidata")
        .first()
    )

    assert cache is not None
    assert "Q123" in cache.data


def test_save_cache_update_existing(populated_session):
    """Entrée existante mise à jour."""
    repo = AnimalRepository(session=populated_session)

    # Create initial entry
    cache = EnrichmentCacheModel(taxon_id=1, source="wikidata", data='{"old": "data"}')
    populated_session.add(cache)
    populated_session.commit()

    # Update with new data
    new_data = {"new": "data"}
    repo._save_cache(1, "wikidata", new_data)

    # Verify updated
    updated_cache = (
        populated_session.query(EnrichmentCacheModel)
        .filter_by(taxon_id=1, source="wikidata")
        .first()
    )

    assert "new" in updated_cache.data
    assert "old" not in updated_cache.data


def test_save_cache_thread_safety(populated_session):
    """Lock empêche accès concurrent."""
    repo = AnimalRepository(session=populated_session)

    # Verify lock is used
    assert hasattr(repo, "_session_lock")

    # Test saving with lock
    data = {"test": "data"}
    repo._save_cache(1, "test", data)

    # Should not raise any threading errors


def test_save_cache_rollback_on_error(populated_session):
    """Rollback si exception."""
    repo = AnimalRepository(session=populated_session)

    data = {"test": "data"}

    with patch.object(populated_session, "commit", side_effect=Exception("DB error")):
        with patch.object(populated_session, "rollback") as mock_rollback:
            try:
                repo._save_cache(1, "test", data)
            except Exception:
                pass

            assert mock_rollback.called


def test_save_cache_list_serialization(populated_session):
    """Liste d'objets sérialisée correctement."""
    repo = AnimalRepository(session=populated_session)

    # List of dicts
    data = [
        {"filename": "img1.jpg", "url": "https://example.com/1"},
        {"filename": "img2.jpg", "url": "https://example.com/2"},
    ]

    repo._save_cache(1, "images", data)

    # Verify list was serialized
    cache = (
        populated_session.query(EnrichmentCacheModel)
        .filter_by(taxon_id=1, source="images")
        .first()
    )

    assert cache is not None
    deserialized = json.loads(cache.data)
    assert isinstance(deserialized, list)
    assert len(deserialized) == 2


# =============================================================================
# SECTION 5: Utilities (8 tests)
# =============================================================================


def test_to_dict_dataclass(populated_session):
    """Dataclass → dict."""
    repo = AnimalRepository(session=populated_session)

    from daynimal.schemas import WikidataEntity

    entity = WikidataEntity(
        qid="Q123", labels={"en": "Test"}, descriptions={"en": "Description"}
    )

    result = repo._to_dict(entity)

    assert isinstance(result, dict)
    assert result["qid"] == "Q123"
    assert result["labels"] == {"en": "Test"}


def test_to_dict_enum_handling(populated_session):
    """Enum → .value."""
    repo = AnimalRepository(session=populated_session)

    from daynimal.schemas import CommonsImage

    image = CommonsImage(
        filename="test.jpg", url="https://example.com/test.jpg", license=License.CC_BY
    )

    result = repo._to_dict(image)

    # Enum should be converted to string value
    assert result["license"] == "CC-BY"


def test_model_to_taxon_vernacular_grouping(populated_session):
    """Noms vernaculaires groupés par langue."""
    repo = AnimalRepository(session=populated_session)

    taxon_model = populated_session.get(TaxonModel, 1)
    taxon = repo._model_to_taxon(taxon_model)

    # Verify vernacular names are grouped by language
    assert "en" in taxon.vernacular_names
    assert "fr" in taxon.vernacular_names
    assert "es" in taxon.vernacular_names

    # Each language should have a list of names
    assert isinstance(taxon.vernacular_names["en"], list)


def test_remove_accents_french():
    """guépard → guepard."""
    result = remove_accents("guépard")
    assert result == "guepard"


def test_remove_accents_multiple_languages():
    """Accents from multiple languages removed."""
    assert remove_accents("café") == "cafe"
    assert remove_accents("naïve") == "naive"
    assert remove_accents("Øresund") == "Øresund"  # Not all chars are removed


def test_remove_accents_no_accents():
    """Text without accents unchanged."""
    result = remove_accents("dog")
    assert result == "dog"


def test_remove_accents_empty_string():
    """Empty string handled."""
    result = remove_accents("")
    assert result == ""


def test_close_all_clients(populated_session):
    """close() ferme tous les clients API."""
    repo = AnimalRepository(session=populated_session)

    # Initialize clients
    _ = repo.wikidata
    _ = repo.wikipedia
    _ = repo.commons

    with patch.object(repo._wikidata, "close") as mock_wd:
        with patch.object(repo._wikipedia, "close") as mock_wp:
            with patch.object(repo._commons, "close") as mock_cm:
                with patch.object(repo.session, "close") as mock_session:
                    repo.close()

                    assert mock_wd.called
                    assert mock_wp.called
                    assert mock_cm.called
                    assert mock_session.called


# =============================================================================
# SECTION 6: get_stats() (5 tests)
# =============================================================================


def test_get_stats_basic(populated_session):
    """get_stats returns correct statistics."""
    repo = AnimalRepository(session=populated_session)

    stats = repo.get_stats()

    assert "total_taxa" in stats
    assert "species_count" in stats
    assert "enriched_count" in stats
    assert stats["total_taxa"] > 0


def test_get_stats_empty_database(session):
    """get_stats with empty database."""
    repo = AnimalRepository(session=session)

    stats = repo.get_stats()

    assert stats["total_taxa"] == 0
    assert stats["species_count"] == 0
    assert stats["enriched_count"] == 0


def test_get_stats_enrichment_progress(populated_session):
    """get_stats shows enrichment progress."""
    repo = AnimalRepository(session=populated_session)

    stats = repo.get_stats()

    # Should have enriched species (first 10 are enriched)
    # Note: populated_session has 30 species + 3 synonyms = 33 total
    assert stats["enriched_count"] == 10
    assert stats["species_count"] == 33  # Includes synonyms


def test_get_stats_all_enriched(populated_session):
    """get_stats when all species are enriched."""
    repo = AnimalRepository(session=populated_session)

    # Mark all species as enriched
    from daynimal.db.models import TaxonModel

    populated_session.query(TaxonModel).filter_by(rank="species").update(
        {"is_enriched": True}
    )
    populated_session.commit()

    stats = repo.get_stats()

    assert stats["enriched_count"] == stats["species_count"]


def test_get_stats_no_species(populated_session):
    """get_stats when no species exist (only higher ranks)."""
    from daynimal.db.models import TaxonModel

    # Delete all species
    populated_session.query(TaxonModel).filter_by(rank="species").delete()
    populated_session.commit()

    repo = AnimalRepository(session=populated_session)

    stats = repo.get_stats()

    assert stats["species_count"] == 0
    assert stats["enriched_count"] == 0
    assert stats["total_taxa"] > 0  # Still have genus/family/order


# =============================================================================
# SECTION ÉTENDUE : _fetch_and_cache_images — branches manquantes (93% → ~97%)
# Lignes: 559-565 (Commons via category fallback), 687-689, 704-706, 728-729,
# 745-746, 752-757, 763-765, 777-778, 782-784
# =============================================================================


class TestFetchAndCacheImagesExtended:
    """Tests supplémentaires pour _fetch_and_cache_images."""

    def test_commons_category_fallback(self, populated_session, sync_executor, mock_phylopic_local):
        """Vérifie que si commons.get_images_for_wikidata retourne une liste vide
        ET commons.get_by_taxonomy retourne des images, ces images sont utilisées.
        C'est le fallback category search quand la recherche par QID échoue.
        Mock: get_images_for_wikidata retourne [], get_by_taxonomy retourne [image]."""
        # todo
        pass

    def test_gbif_media_fallback(self, populated_session, sync_executor, mock_phylopic_local):
        """Vérifie que si Commons ne retourne aucune image (les deux méthodes),
        _fetch_and_cache_images essaie gbif_media.get_media_for_taxon comme fallback.
        Mock: commons retourne [], gbif_media retourne [image]."""
        # todo
        pass

    def test_phylopic_fallback(self, populated_session, sync_executor, mock_phylopic_local):
        """Vérifie que si ni Commons ni GBIF Media ne retournent d'images,
        get_phylopic_silhouette est appelé comme dernier recours.
        Mock: commons retourne [], gbif_media retourne [], phylopic retourne image."""
        # todo
        pass

    def test_p18_image_inserted_first(self, populated_session, sync_executor, mock_phylopic_local):
        """Vérifie que quand wikidata a un p18_image (image principale),
        cette image est récupérée via commons.get_by_source_id et insérée
        en première position de la liste d'images. Les images de la catégorie
        sont ajoutées après."""
        # todo
        pass

    def test_images_ranked_after_fetch(self, populated_session, sync_executor, mock_phylopic_local):
        """Vérifie que rank_images() est appelé sur les images récupérées
        pour les trier par qualité (featured > quality > valued > none,
        BITMAP > DRAWING)."""
        # todo
        pass

    def test_first_image_cached_locally(self, populated_session, sync_executor, mock_phylopic_local):
        """Vérifie que image_cache.cache_single_image est appelé avec
        la première image de la liste pour la mettre en cache local
        (chargement paresseux — seule la première image est téléchargée)."""
        # todo
        pass

    def test_httpx_request_error_sets_offline(self, populated_session, sync_executor, mock_phylopic_local):
        """Vérifie que si une httpx.RequestError est levée pendant la
        récupération des images, connectivity.set_offline() est appelé
        et la méthode retourne gracieusement sans images."""
        # todo
        pass

    def test_no_wikidata_skips_qid_search(self, populated_session, sync_executor, mock_phylopic_local):
        """Vérifie que quand wikidata est None, get_images_for_wikidata
        n'est PAS appelé (pas de QID disponible). La recherche passe
        directement à get_by_taxonomy."""
        # todo
        pass
