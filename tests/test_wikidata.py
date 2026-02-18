"""
Tests for WikidataAPI.

Complete test suite covering all methods and edge cases.
Uses MockHttpClient pattern matching for mocking.
"""

from daynimal.sources.wikidata import WikidataAPI
from daynimal.schemas import ConservationStatus
from tests.fixtures.wikidata_responses import (
    WIKIDATA_ENTITY_Q18498,
    WIKIDATA_NOT_FOUND,
    WIKIDATA_SEARCH_WOLF,
)


class TestWikidataGetBySourceId:
    """Tests for get_by_source_id() method."""

    def test_returns_entity(self, mock_wikidata_client):
        """Test fetching entity by QID."""
        api = WikidataAPI()
        api._client = mock_wikidata_client

        entity = api.get_by_source_id("Q18498")

        assert entity is not None
        assert entity.qid == "Q18498"
        assert entity.labels["en"] == "Canis lupus"
        assert entity.labels["fr"] == "loup"
        assert entity.gbif_id == 5219173

    def test_normalizes_lowercase_qid(self, mock_wikidata_client):
        """Test that lowercase QID is normalized."""
        api = WikidataAPI()
        api._client = mock_wikidata_client

        entity = api.get_by_source_id("q18498")
        assert entity.qid == "Q18498"

    def test_normalizes_numeric_qid(self, mock_wikidata_client):
        """Test that numeric string gets Q prefix."""
        api = WikidataAPI()
        api._client = mock_wikidata_client

        entity = api.get_by_source_id("18498")
        assert entity.qid == "Q18498"

    def test_not_found(self, mock_http_client):
        """Test handling of non-existent entity."""
        mock_http_client.add_response("wbgetentities", WIKIDATA_NOT_FOUND)

        api = WikidataAPI()
        api._client = mock_http_client

        entity = api.get_by_source_id("Q999999999")
        assert entity is None

    def test_parses_image_url(self, mock_wikidata_client):
        """Test that image URL is correctly parsed from P18."""
        api = WikidataAPI()
        api._client = mock_wikidata_client

        entity = api.get_by_source_id("Q18498")

        assert entity.image_url is not None
        assert "Eurasian_wolf_2.jpg" in entity.image_url
        assert entity.image_url.startswith("https://commons.wikimedia.org")

    def test_parses_image_filename(self, mock_wikidata_client):
        """Test that raw P18 filename is stored in image_filename."""
        api = WikidataAPI()
        api._client = mock_wikidata_client

        entity = api.get_by_source_id("Q18498")

        assert entity.image_filename == "Eurasian_wolf_2.jpg"

    def test_parses_mass_with_unit(self, mock_wikidata_client):
        """Test that mass is parsed with unit."""
        api = WikidataAPI()
        api._client = mock_wikidata_client

        entity = api.get_by_source_id("Q18498")

        assert entity.mass is not None
        assert "40" in entity.mass
        assert "kg" in entity.mass

    def test_parses_iucn_status(self, mock_wikidata_client):
        """Test IUCN status parsing."""
        api = WikidataAPI()
        api._client = mock_wikidata_client

        entity = api.get_by_source_id("Q18498")

        assert entity.iucn_status == ConservationStatus.LEAST_CONCERN

    def test_parses_descriptions(self, mock_wikidata_client):
        """Test description parsing."""
        api = WikidataAPI()
        api._client = mock_wikidata_client

        entity = api.get_by_source_id("Q18498")

        assert entity.descriptions["en"] == "species of mammal"
        assert entity.descriptions["fr"] == "espèce de mammifères"


class TestWikidataGetByTaxonomy:
    """Tests for get_by_taxonomy() method."""

    def test_finds_entity_via_sparql(self, mock_wikidata_client):
        """Test finding entity by scientific name using SPARQL."""
        api = WikidataAPI()
        api._client = mock_wikidata_client

        entity = api.get_by_taxonomy("Canis lupus")

        assert entity is not None
        assert entity.qid == "Q18498"

    def test_returns_none_when_not_found(self, mock_http_client):
        """Test returns None when no entity found."""
        # SPARQL returns empty bindings
        mock_http_client.add_response(
            "query.wikidata.org/sparql", {"results": {"bindings": []}}
        )
        # Search also returns empty
        mock_http_client.add_response("wbsearchentities", {"search": []})

        api = WikidataAPI()
        api._client = mock_http_client

        entity = api.get_by_taxonomy("NonExistentSpecies")
        assert entity is None

    def test_fallback_to_search_when_sparql_fails(self, mock_http_client):
        """Test fallback to search API when SPARQL returns error."""
        # SPARQL returns 500
        mock_http_client.add_response("query.wikidata.org/sparql", {}, status_code=500)
        # Search finds result
        mock_http_client.add_response("wbsearchentities", WIKIDATA_SEARCH_WOLF)
        # _is_taxon check
        mock_http_client.add_response(
            "wbgetclaims",
            {
                "claims": {
                    "P225": [{"mainsnak": {"datavalue": {"value": "Canis lupus"}}}]
                }
            },
        )
        # get_by_source_id
        mock_http_client.add_response("wbgetentities", WIKIDATA_ENTITY_Q18498)

        api = WikidataAPI()
        api._client = mock_http_client

        entity = api.get_by_taxonomy("Canis lupus")

        assert entity is not None
        assert entity.qid == "Q18498"

    def test_fallback_to_search_when_sparql_empty(self, mock_http_client):
        """Test fallback to search when SPARQL returns empty bindings."""
        # SPARQL returns empty
        mock_http_client.add_response(
            "query.wikidata.org/sparql", {"results": {"bindings": []}}
        )
        # Search finds result
        mock_http_client.add_response("wbsearchentities", WIKIDATA_SEARCH_WOLF)
        # _is_taxon check
        mock_http_client.add_response(
            "wbgetclaims",
            {
                "claims": {
                    "P225": [{"mainsnak": {"datavalue": {"value": "Canis lupus"}}}]
                }
            },
        )
        # get_by_source_id
        mock_http_client.add_response("wbgetentities", WIKIDATA_ENTITY_Q18498)

        api = WikidataAPI()
        api._client = mock_http_client

        entity = api.get_by_taxonomy("Canis lupus")
        assert entity is not None


class TestWikidataSearch:
    """Tests for search() method."""

    def test_search_returns_results(self, mock_http_client):
        """Test that search returns entities."""
        # Search response with one result
        mock_http_client.add_response(
            "wbsearchentities", {"search": [{"id": "Q18498", "label": "Canis lupus"}]}
        )
        # get_by_source_id for Q18498
        mock_http_client.add_response("wbgetentities", WIKIDATA_ENTITY_Q18498)

        api = WikidataAPI()
        api._client = mock_http_client

        results = api.search("wolf", limit=10)

        assert len(results) == 1
        assert results[0].qid == "Q18498"

    def test_search_empty_results(self, mock_http_client):
        """Test search with no results."""
        mock_http_client.add_response("wbsearchentities", {"search": []})

        api = WikidataAPI()
        api._client = mock_http_client

        results = api.search("nonexistent", limit=10)
        assert results == []

    def test_search_filters_missing_entities(self, mock_http_client):
        """Test that search filters out entities that can't be fetched."""
        # Search returns two results (Q18498 and Q144)
        mock_http_client.add_response("wbsearchentities", WIKIDATA_SEARCH_WOLF)
        # wbgetentities only has Q18498, so Q144 will return None
        mock_http_client.add_response("wbgetentities", WIKIDATA_ENTITY_Q18498)

        api = WikidataAPI()
        api._client = mock_http_client

        results = api.search("wolf", limit=10)

        # Only Q18498 should be in results (Q144 not in entities → None)
        assert len(results) == 1
        assert results[0].qid == "Q18498"


class TestWikidataSearchTaxonQid:
    """Tests for _search_taxon_qid() private method."""

    def test_finds_taxon_via_search(self, mock_http_client):
        """Test finding taxon QID via search API."""
        mock_http_client.add_response("wbsearchentities", WIKIDATA_SEARCH_WOLF)
        mock_http_client.add_response(
            "wbgetclaims",
            {
                "claims": {
                    "P225": [{"mainsnak": {"datavalue": {"value": "Canis lupus"}}}]
                }
            },
        )

        api = WikidataAPI()
        api._client = mock_http_client

        qid = api._search_taxon_qid("Canis lupus")
        assert qid == "Q18498"

    def test_returns_none_when_no_taxon_found(self, mock_http_client):
        """Test returns None when no search results are taxa."""
        mock_http_client.add_response("wbsearchentities", WIKIDATA_SEARCH_WOLF)
        # _is_taxon returns False for all results (no P225)
        mock_http_client.add_response("wbgetclaims", {"claims": {}})

        api = WikidataAPI()
        api._client = mock_http_client

        qid = api._search_taxon_qid("NotATaxon")
        assert qid is None

    def test_returns_none_on_empty_search(self, mock_http_client):
        """Test returns None when search returns empty."""
        mock_http_client.add_response("wbsearchentities", {"search": []})

        api = WikidataAPI()
        api._client = mock_http_client

        qid = api._search_taxon_qid("NonExistent")
        assert qid is None


class TestWikidataIsTaxon:
    """Tests for _is_taxon() private method."""

    def test_is_taxon_true(self, mock_http_client):
        """Test that entity with P225 is identified as taxon."""
        mock_http_client.add_response(
            "wbgetclaims",
            {
                "claims": {
                    "P225": [{"mainsnak": {"datavalue": {"value": "Canis lupus"}}}]
                }
            },
        )

        api = WikidataAPI()
        api._client = mock_http_client

        assert api._is_taxon("Q18498") is True

    def test_is_taxon_false(self, mock_http_client):
        """Test that entity without P225 is not a taxon."""
        mock_http_client.add_response("wbgetclaims", {"claims": {}})

        api = WikidataAPI()
        api._client = mock_http_client

        assert api._is_taxon("Q12345") is False

    def test_is_taxon_on_api_error(self, mock_http_client):
        """Test that API error returns False."""
        mock_http_client.add_response("wbgetclaims", {}, status_code=500)

        api = WikidataAPI()
        api._client = mock_http_client

        assert api._is_taxon("Q12345") is False


class TestWikidataParseEntity:
    """Tests for _parse_entity() with various claim types."""

    def test_parses_eol_id(self, mock_http_client):
        """Test parsing EOL ID (P830)."""
        entity_data = {
            "labels": {},
            "descriptions": {},
            "claims": {
                "P830": [
                    {"mainsnak": {"datavalue": {"value": "328674", "type": "string"}}}
                ]
            },
        }
        mock_http_client.add_response(
            "wbgetentities", {"entities": {"Q100": entity_data}}
        )

        api = WikidataAPI()
        api._client = mock_http_client

        entity = api.get_by_source_id("Q100")
        assert entity.eol_id == "328674"

    def test_parses_length(self, mock_http_client):
        """Test parsing length (P2043)."""
        entity_data = {
            "labels": {},
            "descriptions": {},
            "claims": {
                "P2043": [
                    {
                        "mainsnak": {
                            "datavalue": {
                                "value": {
                                    "amount": "+1.5",
                                    "unit": "http://www.wikidata.org/entity/Q11573",
                                },
                                "type": "quantity",
                            }
                        }
                    }
                ]
            },
        }
        mock_http_client.add_response(
            "wbgetentities", {"entities": {"Q100": entity_data}}
        )

        api = WikidataAPI()
        api._client = mock_http_client

        entity = api.get_by_source_id("Q100")
        assert entity.length is not None
        assert "1.5" in entity.length
        assert "m" in entity.length

    def test_parses_lifespan(self, mock_http_client):
        """Test parsing lifespan (P2250)."""
        entity_data = {
            "labels": {},
            "descriptions": {},
            "claims": {
                "P2250": [
                    {
                        "mainsnak": {
                            "datavalue": {
                                "value": {
                                    "amount": "+15",
                                    "unit": "http://www.wikidata.org/entity/Q577",
                                },
                                "type": "quantity",
                            }
                        }
                    }
                ]
            },
        }
        mock_http_client.add_response(
            "wbgetentities", {"entities": {"Q100": entity_data}}
        )

        api = WikidataAPI()
        api._client = mock_http_client

        entity = api.get_by_source_id("Q100")
        assert entity.lifespan is not None
        assert "15" in entity.lifespan
        assert "year" in entity.lifespan

    def test_image_filename_none_when_no_p18(self, mock_http_client):
        """Test image_filename is None when P18 is absent."""
        entity_data = {"labels": {}, "descriptions": {}, "claims": {}}
        mock_http_client.add_response(
            "wbgetentities", {"entities": {"Q100": entity_data}}
        )

        api = WikidataAPI()
        api._client = mock_http_client

        entity = api.get_by_source_id("Q100")
        assert entity.image_filename is None
        assert entity.image_url is None

    def test_gbif_id_invalid_value(self, mock_http_client):
        """Test that invalid GBIF ID (non-numeric) is handled."""
        entity_data = {
            "labels": {},
            "descriptions": {},
            "claims": {
                "P846": [
                    {
                        "mainsnak": {
                            "datavalue": {"value": "not-a-number", "type": "string"}
                        }
                    }
                ]
            },
        }
        mock_http_client.add_response(
            "wbgetentities", {"entities": {"Q100": entity_data}}
        )

        api = WikidataAPI()
        api._client = mock_http_client

        entity = api.get_by_source_id("Q100")
        assert entity.gbif_id is None


class TestWikidataHelpers:
    """Tests for helper methods (no HTTP needed)."""

    def test_get_claim_value_empty_list(self):
        """Test _get_claim_value with empty list."""
        api = WikidataAPI()
        assert api._get_claim_value([]) is None

    def test_get_claim_value_string(self):
        """Test _get_claim_value with string value."""
        api = WikidataAPI()
        claim = [{"mainsnak": {"datavalue": {"value": "test_value"}}}]
        assert api._get_claim_value(claim) == "test_value"

    def test_get_claim_value_dict_with_text(self):
        """Test _get_claim_value with dict value containing 'text'."""
        api = WikidataAPI()
        claim = [{"mainsnak": {"datavalue": {"value": {"text": "hello"}}}}]
        assert api._get_claim_value(claim) == "hello"

    def test_get_claim_value_dict_with_id(self):
        """Test _get_claim_value with dict value containing 'id' only."""
        api = WikidataAPI()
        claim = [{"mainsnak": {"datavalue": {"value": {"id": "Q12345"}}}}]
        assert api._get_claim_value(claim) == "Q12345"

    def test_get_claim_value_wikibase_entityid(self):
        """Test _get_claim_value with wikibase-entityid type."""
        api = WikidataAPI()
        claim = [{"mainsnak": {"datavalue": {"value": {"id": "Q237350"}}}}]
        assert api._get_claim_value(claim, value_type="wikibase-entityid") == "Q237350"

    def test_get_quantity_string_empty_list(self):
        """Test _get_quantity_string with empty list."""
        api = WikidataAPI()
        assert api._get_quantity_string([]) is None

    def test_get_quantity_string_with_unit(self):
        """Test _get_quantity_string with known unit."""
        api = WikidataAPI()
        claim = [
            {
                "mainsnak": {
                    "datavalue": {
                        "value": {
                            "amount": "+25",
                            "unit": "http://www.wikidata.org/entity/Q11570",
                        }
                    }
                }
            }
        ]
        assert api._get_quantity_string(claim) == "25 kg"

    def test_get_quantity_string_no_unit(self):
        """Test _get_quantity_string when unit is empty string."""
        api = WikidataAPI()
        claim = [{"mainsnak": {"datavalue": {"value": {"amount": "+42", "unit": ""}}}}]
        assert api._get_quantity_string(claim) == "42"

    def test_get_quantity_string_unknown_unit(self):
        """Test _get_quantity_string with unknown unit QID."""
        api = WikidataAPI()
        claim = [
            {
                "mainsnak": {
                    "datavalue": {
                        "value": {
                            "amount": "+10",
                            "unit": "http://www.wikidata.org/entity/Q99999",
                        }
                    }
                }
            }
        ]
        assert api._get_quantity_string(claim) == "10"

    def test_get_quantity_string_no_amount(self):
        """Test _get_quantity_string returns None when no amount."""
        api = WikidataAPI()
        claim = [{"mainsnak": {"datavalue": {"value": {}}}}]
        assert api._get_quantity_string(claim) is None

    def test_get_commons_url(self):
        """Test Commons URL generation with space replacement."""
        api = WikidataAPI()
        url = api._get_commons_url("Wolf image.jpg")
        assert (
            url == "https://commons.wikimedia.org/wiki/Special:FilePath/Wolf_image.jpg"
        )

    def test_get_commons_url_no_spaces(self):
        """Test Commons URL generation without spaces."""
        api = WikidataAPI()
        url = api._get_commons_url("Wolf.jpg")
        assert url == "https://commons.wikimedia.org/wiki/Special:FilePath/Wolf.jpg"


class TestWikidataMetadata:
    """Tests for source metadata."""

    def test_source_name(self):
        """Test source name."""
        api = WikidataAPI()
        assert api.source_name == "wikidata"

    def test_license(self):
        """Test license."""
        api = WikidataAPI()
        assert api.license == "CC0"


class TestWikidataAttribution:
    """Tests for attribution generation."""

    def test_entity_has_qid_for_attribution(self, mock_wikidata_client):
        """Test that QID is available for attribution URLs."""
        api = WikidataAPI()
        api._client = mock_wikidata_client

        entity = api.get_by_source_id("Q18498")

        attribution_url = f"https://www.wikidata.org/wiki/{entity.qid}"
        assert "Q18498" in attribution_url
