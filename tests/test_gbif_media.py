"""
Tests for GBIF Media API client.

Tests license filtering, image parsing, and error handling.
"""

import pytest

from daynimal.schemas import ImageSource, License
from daynimal.sources.gbif_media import GbifMediaAPI, _parse_gbif_license


class TestParseGbifLicense:
    """Tests for GBIF license URL parsing."""

    def test_cc_by_accepted(self):
        assert (
            _parse_gbif_license("http://creativecommons.org/licenses/by/4.0/")
            == License.CC_BY
        )

    def test_cc_by_sa_accepted(self):
        assert (
            _parse_gbif_license("http://creativecommons.org/licenses/by-sa/4.0/")
            == License.CC_BY_SA
        )

    def test_cc0_accepted(self):
        assert (
            _parse_gbif_license("http://creativecommons.org/publicdomain/zero/1.0/")
            == License.CC0
        )

    def test_cc_by_nc_rejected(self):
        assert (
            _parse_gbif_license("http://creativecommons.org/licenses/by-nc/4.0/")
            is None
        )

    def test_cc_by_nd_rejected(self):
        assert (
            _parse_gbif_license("http://creativecommons.org/licenses/by-nd/4.0/")
            is None
        )

    def test_cc_by_nc_sa_rejected(self):
        assert (
            _parse_gbif_license("http://creativecommons.org/licenses/by-nc-sa/4.0/")
            is None
        )

    def test_none_rejected(self):
        assert _parse_gbif_license(None) is None

    def test_empty_rejected(self):
        assert _parse_gbif_license("") is None

    def test_unknown_rejected(self):
        assert _parse_gbif_license("http://example.com/custom-license") is None


class TestGbifMediaAPI:
    """Tests for GbifMediaAPI."""

    @pytest.fixture
    def api(self, mock_http_client):
        """Create a GbifMediaAPI with mock client."""
        api = GbifMediaAPI()
        api._client = mock_http_client
        return api

    def test_get_media_filters_nc_licenses(self, api, mock_http_client):
        """Test that NC-licensed images are filtered out."""
        from tests.fixtures.gbif_media_responses import GBIF_MEDIA_MIXED_LICENSES

        mock_http_client.add_response("api.gbif.org", GBIF_MEDIA_MIXED_LICENSES)
        images = api.get_media_for_taxon(5219173, limit=10)

        # Should have 3 images: CC-BY, CC0, CC-BY-SA (NC, NC-SA, ND rejected, Sound filtered)
        assert len(images) == 3

        licenses = {img.license for img in images}
        assert License.CC_BY in licenses
        assert License.CC0 in licenses
        assert License.CC_BY_SA in licenses

    def test_image_source_is_gbif(self, api, mock_http_client):
        """Test that returned images have image_source == GBIF."""
        from tests.fixtures.gbif_media_responses import GBIF_MEDIA_MIXED_LICENSES

        mock_http_client.add_response("api.gbif.org", GBIF_MEDIA_MIXED_LICENSES)
        images = api.get_media_for_taxon(5219173)

        for img in images:
            assert img.image_source == ImageSource.GBIF

    def test_attribution_mentions_gbif(self, api, mock_http_client):
        """Test that attribution text mentions GBIF."""
        from tests.fixtures.gbif_media_responses import GBIF_MEDIA_MIXED_LICENSES

        mock_http_client.add_response("api.gbif.org", GBIF_MEDIA_MIXED_LICENSES)
        images = api.get_media_for_taxon(5219173)

        assert len(images) > 0
        for img in images:
            assert "GBIF" in img.get_attribution_text()

    def test_all_nc_returns_empty(self, api, mock_http_client):
        """Test that all-NC response returns empty list."""
        from tests.fixtures.gbif_media_responses import GBIF_MEDIA_ALL_NC

        mock_http_client.add_response("api.gbif.org", GBIF_MEDIA_ALL_NC)
        images = api.get_media_for_taxon(5219173)
        assert images == []

    def test_empty_response(self, api, mock_http_client):
        """Test empty API response."""
        from tests.fixtures.gbif_media_responses import GBIF_MEDIA_EMPTY

        mock_http_client.add_response("api.gbif.org", GBIF_MEDIA_EMPTY)
        images = api.get_media_for_taxon(5219173)
        assert images == []

    def test_network_error_returns_empty(self, api, mock_http_client):
        """Test that network errors return empty list."""
        # Don't add any response — will raise ValueError from MockHttpClient
        # Instead, set a default empty response simulating failure
        mock_http_client.add_response("api.gbif.org", {}, status_code=500)
        images = api.get_media_for_taxon(5219173)
        assert images == []

    def test_limit_respected(self, api, mock_http_client):
        """Test that limit parameter is respected."""
        from tests.fixtures.gbif_media_responses import GBIF_MEDIA_MIXED_LICENSES

        mock_http_client.add_response("api.gbif.org", GBIF_MEDIA_MIXED_LICENSES)
        images = api.get_media_for_taxon(5219173, limit=1)
        assert len(images) == 1

    def test_source_page_url_set(self, api, mock_http_client):
        """Test that source_page_url is set from references field."""
        from tests.fixtures.gbif_media_responses import GBIF_MEDIA_MIXED_LICENSES

        mock_http_client.add_response("api.gbif.org", GBIF_MEDIA_MIXED_LICENSES)
        images = api.get_media_for_taxon(5219173)

        # First image has references field
        assert images[0].source_page_url == "https://www.gbif.org/occurrence/123"
