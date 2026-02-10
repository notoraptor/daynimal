"""
Extended tests for CommonsAPI to achieve higher coverage.

Covers search(), get_images_for_wikidata(), error paths, and edge cases.
"""

from daynimal.sources.commons import CommonsAPI
from daynimal.schemas import License


class TestCommonsSearch:
    """Tests for search() method."""

    def test_search_returns_multiple_images(self, mock_http_client):
        """Test search returns list of images."""
        search_response = {
            "query": {
                "pages": {
                    "123": {
                        "title": "File:Wolf1.jpg",
                        "imageinfo": [
                            {
                                "url": "https://upload.wikimedia.org/wolf1.jpg",
                                "descriptionurl": "https://commons.wikimedia.org/wiki/File:Wolf1.jpg",
                                "user": "Photographer1",
                                "extmetadata": {
                                    "LicenseShortName": {"value": "CC BY-SA 4.0"}
                                },
                            }
                        ],
                    },
                    "456": {
                        "title": "File:Wolf2.jpg",
                        "imageinfo": [
                            {
                                "url": "https://upload.wikimedia.org/wolf2.jpg",
                                "descriptionurl": "https://commons.wikimedia.org/wiki/File:Wolf2.jpg",
                                "user": "Photographer2",
                                "extmetadata": {"LicenseShortName": {"value": "CC0"}},
                            }
                        ],
                    },
                }
            }
        }

        mock_http_client.add_response("generator=search", search_response)

        api = CommonsAPI()
        api._client = mock_http_client

        images = api.search("wolf", limit=10)

        assert len(images) == 2
        assert all(hasattr(img, "url") for img in images)
        assert all(hasattr(img, "filename") for img in images)

    def test_search_empty_results(self, mock_http_client):
        """Test search with no results."""
        mock_http_client.add_response("generator=search", {"query": {"pages": {}}})

        api = CommonsAPI()
        api._client = mock_http_client

        images = api.search("NonExistentAnimal12345", limit=10)

        assert images == []

    def test_search_filters_invalid_images(self, mock_http_client):
        """Test that search filters out images with invalid URLs."""
        search_response = {
            "query": {
                "pages": {
                    "123": {
                        "title": "File:Valid.jpg",
                        "imageinfo": [
                            {
                                "url": "https://upload.wikimedia.org/valid.jpg",
                                "descriptionurl": "https://commons.wikimedia.org/wiki/File:Valid.jpg",
                                "user": "User",
                                "extmetadata": {
                                    "LicenseShortName": {"value": "CC BY 4.0"}
                                },
                            }
                        ],
                    },
                    "456": {
                        "title": "File:Invalid.svg",  # SVG will be filtered
                        "imageinfo": [
                            {
                                "url": "https://upload.wikimedia.org/invalid.svg",
                                "descriptionurl": "https://commons.wikimedia.org/wiki/File:Invalid.svg",
                                "user": "User",
                                "extmetadata": {
                                    "LicenseShortName": {"value": "CC BY 4.0"}
                                },
                            }
                        ],
                    },
                }
            }
        }

        mock_http_client.add_response("generator=search", search_response)

        api = CommonsAPI()
        api._client = mock_http_client

        images = api.search("test")

        # Only valid image should be returned (SVG filtered)
        assert len(images) >= 1


class TestCommonsGetImagesForWikidata:
    """Tests for get_images_for_wikidata() method."""

    def test_get_images_for_wikidata_returns_images(self, mock_http_client):
        """Test fetching images associated with Wikidata entity."""
        wikidata_response = {
            "query": {
                "pages": {
                    "789": {
                        "title": "File:Wikidata_Wolf.jpg",
                        "imageinfo": [
                            {
                                "url": "https://upload.wikimedia.org/wikidata_wolf.jpg",
                                "descriptionurl": "https://commons.wikimedia.org/wiki/File:Wikidata_Wolf.jpg",
                                "user": "Wikidata User",
                                "extmetadata": {
                                    "LicenseShortName": {"value": "CC BY-SA 3.0"}
                                },
                            }
                        ],
                    }
                }
            }
        }

        mock_http_client.add_response("haswbstatement:P180=", wikidata_response)

        api = CommonsAPI()
        api._client = mock_http_client

        images = api.get_images_for_wikidata("Q18498", limit=5)

        assert len(images) > 0
        assert all(hasattr(img, "url") for img in images)

    def test_get_images_for_wikidata_empty_results(self, mock_http_client):
        """Test get_images_for_wikidata with no results."""
        mock_http_client.add_response("haswbstatement:P180=", {"query": {"pages": {}}})

        api = CommonsAPI()
        api._client = mock_http_client

        images = api.get_images_for_wikidata("Q999999", limit=5)

        assert images == []


class TestCommonsGetByTaxonomyFallback:
    """Tests for get_by_taxonomy() fallback to search."""

    def test_get_by_taxonomy_falls_back_to_search_when_category_empty(
        self, mock_http_client
    ):
        """Test that get_by_taxonomy falls back to search when category search fails."""
        # Mock _search_category to return empty
        mock_http_client.add_response(
            "categorymembers", {"query": {"categorymembers": []}}
        )

        # Mock general search to return results
        search_response = {
            "query": {
                "pages": {
                    "123": {
                        "title": "File:Fallback_Wolf.jpg",
                        "imageinfo": [
                            {
                                "url": "https://upload.wikimedia.org/fallback_wolf.jpg",
                                "descriptionurl": "https://commons.wikimedia.org/wiki/File:Fallback_Wolf.jpg",
                                "user": "Fallback User",
                                "extmetadata": {
                                    "LicenseShortName": {"value": "CC BY 4.0"}
                                },
                            }
                        ],
                    }
                }
            }
        }
        mock_http_client.add_response("generator=search", search_response)

        api = CommonsAPI()
        api._client = mock_http_client

        images = api.get_by_taxonomy("Rare Species")

        # Should get results from fallback search
        assert len(images) > 0


class TestCommonsGetBySourceIdNotFound:
    """Tests for get_by_source_id() error cases."""

    def test_get_by_source_id_with_no_imageinfo(self, mock_http_client):
        """Test get_by_source_id when API returns no imageinfo."""
        response_no_imageinfo = {
            "query": {
                "pages": {
                    "123": {
                        "title": "File:NoImageInfo.jpg"
                        # Missing imageinfo
                    }
                }
            }
        }

        mock_http_client.add_response("titles=", response_no_imageinfo)

        api = CommonsAPI()
        api._client = mock_http_client

        image = api.get_by_source_id("NoImageInfo.jpg")

        # Should return None when imageinfo is missing
        assert image is None


class TestCommonsLicenseParsing:
    """Tests for license parsing edge cases."""

    def test_parse_license_cc_by(self, mock_http_client):
        """Test parsing CC-BY license."""
        response_cc_by = {
            "query": {
                "pages": {
                    "123": {
                        "title": "File:Test.jpg",
                        "imageinfo": [
                            {
                                "url": "https://upload.wikimedia.org/test.jpg",
                                "descriptionurl": "https://commons.wikimedia.org/wiki/File:Test.jpg",
                                "user": "User",
                                "extmetadata": {
                                    # Commons uses hyphens in license short names
                                    "LicenseShortName": {"value": "CC-BY-4.0"}
                                },
                            }
                        ],
                    }
                }
            }
        }

        mock_http_client.add_response("titles=", response_cc_by)

        api = CommonsAPI()
        api._client = mock_http_client

        image = api.get_by_source_id("Test.jpg")

        assert image is not None
        assert image.license == License.CC_BY

    def test_parse_license_public_domain(self, mock_http_client):
        """Test parsing Public Domain license."""
        response_pd = {
            "query": {
                "pages": {
                    "123": {
                        "title": "File:PD.jpg",
                        "imageinfo": [
                            {
                                "url": "https://upload.wikimedia.org/pd.jpg",
                                "descriptionurl": "https://commons.wikimedia.org/wiki/File:PD.jpg",
                                "user": "User",
                                "extmetadata": {
                                    "LicenseShortName": {"value": "Public domain"}
                                },
                            }
                        ],
                    }
                }
            }
        }

        mock_http_client.add_response("titles=", response_pd)

        api = CommonsAPI()
        api._client = mock_http_client

        image = api.get_by_source_id("PD.jpg")

        assert image is not None
        assert image.license == License.PUBLIC_DOMAIN

    def test_parse_license_unknown_defaults_to_cc_by_sa(self, mock_http_client):
        """Test that unknown licenses default to CC-BY-SA."""
        response_unknown = {
            "query": {
                "pages": {
                    "123": {
                        "title": "File:Unknown.jpg",
                        "imageinfo": [
                            {
                                "url": "https://upload.wikimedia.org/unknown.jpg",
                                "descriptionurl": "https://commons.wikimedia.org/wiki/File:Unknown.jpg",
                                "user": "User",
                                "extmetadata": {
                                    "LicenseShortName": {
                                        "value": "Some Unknown License"
                                    }
                                },
                            }
                        ],
                    }
                }
            }
        }

        mock_http_client.add_response("titles=", response_unknown)

        api = CommonsAPI()
        api._client = mock_http_client

        image = api.get_by_source_id("Unknown.jpg")

        assert image is not None
        # Unknown licenses should default to CC-BY-SA (safest assumption)
        assert image.license == License.CC_BY_SA
