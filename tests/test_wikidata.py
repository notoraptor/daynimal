"""
Tests for WikidataAPI.

These tests use mocked HTTP responses - no network access required.
"""

from daynimal.sources.wikidata import WikidataAPI
from tests.fixtures.wikidata_responses import WIKIDATA_NOT_FOUND


class TestWikidataAPI:
    """Tests for WikidataAPI class."""

    def test_get_by_source_id_returns_entity(self, mock_wikidata_client):
        """Test fetching entity by QID."""
        api = WikidataAPI()
        api._client = mock_wikidata_client

        entity = api.get_by_source_id("Q18498")

        assert entity is not None
        assert entity.qid == "Q18498"
        assert entity.labels["en"] == "Canis lupus"
        assert entity.labels["fr"] == "loup"
        assert entity.gbif_id == 5219173

    def test_get_by_source_id_normalizes_qid(self, mock_wikidata_client):
        """Test that QID is normalized (uppercase, Q prefix)."""
        api = WikidataAPI()
        api._client = mock_wikidata_client

        # Should work with lowercase
        entity = api.get_by_source_id("q18498")
        assert entity.qid == "Q18498"

        # Should work without Q prefix
        entity = api.get_by_source_id("18498")
        assert entity.qid == "Q18498"

    def test_get_by_source_id_not_found(self, mock_http_client):
        """Test handling of non-existent entity."""
        mock_http_client.add_response("wbgetentities", WIKIDATA_NOT_FOUND)

        api = WikidataAPI()
        api._client = mock_http_client

        entity = api.get_by_source_id("Q999999999")

        assert entity is None

    def test_get_by_taxonomy_finds_entity(self, mock_wikidata_client):
        """Test finding entity by scientific name."""
        api = WikidataAPI()
        api._client = mock_wikidata_client

        entity = api.get_by_taxonomy("Canis lupus")

        assert entity is not None
        assert entity.qid == "Q18498"

    def test_parses_image_url(self, mock_wikidata_client):
        """Test that image URL is correctly parsed from P18 property."""
        api = WikidataAPI()
        api._client = mock_wikidata_client

        entity = api.get_by_source_id("Q18498")

        assert entity.image_url is not None
        assert "Eurasian_wolf_2.jpg" in entity.image_url
        assert entity.image_url.startswith("https://commons.wikimedia.org")

    def test_parses_mass_with_unit(self, mock_wikidata_client):
        """Test that mass is parsed with unit."""
        api = WikidataAPI()
        api._client = mock_wikidata_client

        entity = api.get_by_source_id("Q18498")

        assert entity.mass is not None
        assert "40" in entity.mass
        assert "kg" in entity.mass

    def test_source_name_and_license(self):
        """Test that source metadata is correct."""
        api = WikidataAPI()

        assert api.source_name == "wikidata"
        assert api.license == "CC0"


class TestWikidataAttributions:
    """Tests for attribution generation."""

    def test_entity_has_qid_for_attribution(self, mock_wikidata_client):
        """Test that QID is available for attribution URLs."""
        api = WikidataAPI()
        api._client = mock_wikidata_client

        entity = api.get_by_source_id("Q18498")

        # QID should be usable for attribution URL
        attribution_url = f"https://www.wikidata.org/wiki/{entity.qid}"
        assert "Q18498" in attribution_url
