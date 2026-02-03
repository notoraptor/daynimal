"""
Tests for CommonsAPI.

These tests use mocked HTTP responses - no network access required.
"""

from daynimal.sources.commons import CommonsAPI
from daynimal.schemas import License
from tests.fixtures.commons_responses import (
    COMMONS_IMAGE_INFO_WOLF,
    COMMONS_CATEGORY_CANIS_LUPUS,
    COMMONS_NOT_FOUND,
)


class TestCommonsAPI:
    """Tests for CommonsAPI class."""

    def test_get_by_source_id_returns_image(self, mock_http_client):
        """Test fetching image by filename."""
        mock_http_client.add_response("commons.wikimedia.org", COMMONS_IMAGE_INFO_WOLF)

        api = CommonsAPI()
        api._client = mock_http_client

        image = api.get_by_source_id("Eurasian wolf 2.jpg")

        assert image is not None
        assert "Eurasian" in image.filename or "wolf" in image.filename.lower()
        assert image.url is not None
        assert image.author is not None

    def test_get_by_source_id_adds_file_prefix(self, mock_http_client):
        """Test that File: prefix is added if missing."""
        mock_http_client.add_response("commons.wikimedia.org", COMMONS_IMAGE_INFO_WOLF)

        api = CommonsAPI()
        api._client = mock_http_client

        # Should work without File: prefix
        image = api.get_by_source_id("Eurasian wolf 2.jpg")
        assert image is not None

    def test_get_by_taxonomy_returns_images(self, mock_commons_client):
        """Test finding images by scientific name."""
        api = CommonsAPI()
        api._client = mock_commons_client

        images = api.get_by_taxonomy("Canis lupus", limit=5)

        assert len(images) > 0
        for image in images:
            assert image.url is not None

    def test_get_by_source_id_not_found(self, mock_http_client):
        """Test handling of non-existent image."""
        mock_http_client.add_response("commons.wikimedia.org", COMMONS_NOT_FOUND)

        api = CommonsAPI()
        api._client = mock_http_client

        image = api.get_by_source_id("NonExistentImage12345.jpg")

        assert image is None

    def test_parses_license_cc_by_sa(self, mock_http_client):
        """Test parsing CC-BY-SA license."""
        mock_http_client.add_response("commons.wikimedia.org", COMMONS_IMAGE_INFO_WOLF)

        api = CommonsAPI()
        api._client = mock_http_client

        image = api.get_by_source_id("test.jpg")

        assert image.license == License.CC_BY_SA

    def test_parses_license_cc0(self, mock_http_client):
        """Test parsing CC0 license."""
        mock_http_client.add_response(
            "commons.wikimedia.org", COMMONS_CATEGORY_CANIS_LUPUS
        )

        api = CommonsAPI()
        api._client = mock_http_client

        images = api.get_by_taxonomy("Canis lupus")

        # One of the images should be CC0
        licenses = [img.license for img in images]
        assert License.CC0 in licenses or License.CC_BY_SA in licenses

    def test_source_name_and_license(self):
        """Test that source metadata is correct."""
        api = CommonsAPI()

        assert api.source_name == "commons"
        assert "CC" in api.license  # Various CC licenses


class TestCommonsAttributions:
    """Tests for Commons image attribution generation."""

    def test_get_attribution_text(self, mock_http_client):
        """Test attribution text generation."""
        mock_http_client.add_response("commons.wikimedia.org", COMMONS_IMAGE_INFO_WOLF)

        api = CommonsAPI()
        api._client = mock_http_client

        image = api.get_by_source_id("Eurasian wolf 2.jpg")
        attribution = image.get_attribution_text()

        assert "Wikimedia Commons" in attribution
        assert image.author in attribution or "Unknown" in attribution

    def test_get_attribution_html(self, mock_http_client):
        """Test HTML attribution with links."""
        mock_http_client.add_response("commons.wikimedia.org", COMMONS_IMAGE_INFO_WOLF)

        api = CommonsAPI()
        api._client = mock_http_client

        image = api.get_by_source_id("Eurasian wolf 2.jpg")
        html = image.get_attribution_html()

        assert "<a href=" in html
        assert "Wikimedia Commons" in html

    def test_commons_page_url(self, mock_http_client):
        """Test Commons page URL generation."""
        mock_http_client.add_response("commons.wikimedia.org", COMMONS_IMAGE_INFO_WOLF)

        api = CommonsAPI()
        api._client = mock_http_client

        image = api.get_by_source_id("Eurasian wolf 2.jpg")

        assert "commons.wikimedia.org/wiki/File:" in image.commons_page_url

    def test_license_url(self, mock_http_client):
        """Test license URL generation."""
        mock_http_client.add_response("commons.wikimedia.org", COMMONS_IMAGE_INFO_WOLF)

        api = CommonsAPI()
        api._client = mock_http_client

        image = api.get_by_source_id("test.jpg")

        assert "creativecommons.org" in image.license_url

    def test_attribution_required_flag(self, mock_http_client):
        """Test attribution_required is set correctly."""
        mock_http_client.add_response("commons.wikimedia.org", COMMONS_IMAGE_INFO_WOLF)

        api = CommonsAPI()
        api._client = mock_http_client

        image = api.get_by_source_id("test.jpg")

        # CC-BY-SA requires attribution
        assert image.attribution_required is True
