"""
Tests for CommonsAPI.

These tests use mocked HTTP responses - no network access required.
"""

from daynimal.sources.commons import CommonsAPI, rank_images
from daynimal.schemas import CommonsImage, License
from tests.fixtures.commons_responses import (
    COMMONS_IMAGE_INFO_WOLF,
    COMMONS_IMAGE_INFO_FEATURED,
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


class TestParseImageInfoMetadata:
    """Tests for assessment and media_type extraction in _parse_image_info()."""

    def test_extracts_assessment(self, mock_http_client):
        """Test that assessment is extracted from extmetadata."""
        mock_http_client.add_response(
            "commons.wikimedia.org", COMMONS_IMAGE_INFO_FEATURED
        )

        api = CommonsAPI()
        api._client = mock_http_client

        image = api.get_by_source_id("Featured_lion.jpg")
        assert image is not None
        assert image.assessment is not None
        assert "featured" in image.assessment.lower()

    def test_extracts_media_type(self, mock_http_client):
        """Test that media_type is extracted from imageinfo."""
        mock_http_client.add_response(
            "commons.wikimedia.org", COMMONS_IMAGE_INFO_FEATURED
        )

        api = CommonsAPI()
        api._client = mock_http_client

        image = api.get_by_source_id("Featured_lion.jpg")
        assert image is not None
        assert image.media_type == "BITMAP"

    def test_no_assessment_returns_none(self, mock_http_client):
        """Test that missing assessment returns None."""
        mock_http_client.add_response("commons.wikimedia.org", COMMONS_IMAGE_INFO_WOLF)

        api = CommonsAPI()
        api._client = mock_http_client

        image = api.get_by_source_id("Eurasian wolf 2.jpg")
        assert image is not None
        assert image.assessment is None


class TestRankImages:
    """Tests for rank_images() function."""

    def _make_image(
        self,
        filename="test.jpg",
        assessment=None,
        media_type="BITMAP",
        width=1000,
        height=800,
    ):
        return CommonsImage(
            filename=filename,
            url=f"https://example.com/{filename}",
            assessment=assessment,
            media_type=media_type,
            width=width,
            height=height,
        )

    def test_p18_first(self):
        """Test that P18 image is always ranked first."""
        p18 = self._make_image("p18.jpg", width=500, height=400)
        other = self._make_image(
            "other.jpg", assessment="featured", width=4000, height=3000
        )

        result = rank_images([other, p18], p18_filename="p18.jpg")
        assert result[0].filename == "p18.jpg"

    def test_featured_before_quality(self):
        """Test featured > quality > valued > none."""
        featured = self._make_image("feat.jpg", assessment="featured")
        quality = self._make_image("qual.jpg", assessment="quality")
        valued = self._make_image("val.jpg", assessment="valued")
        none_img = self._make_image("none.jpg")

        result = rank_images([none_img, valued, quality, featured])
        assert result[0].filename == "feat.jpg"
        assert result[1].filename == "qual.jpg"
        assert result[2].filename == "val.jpg"
        assert result[3].filename == "none.jpg"

    def test_bitmap_before_drawing(self):
        """Test BITMAP > unknown > DRAWING."""
        bitmap = self._make_image("photo.jpg", media_type="BITMAP")
        drawing = self._make_image("sketch.svg", media_type="DRAWING")

        result = rank_images([drawing, bitmap])
        assert result[0].filename == "photo.jpg"
        assert result[1].filename == "sketch.svg"

    def test_resolution_tiebreaker(self):
        """Test resolution as tiebreaker for same assessment and type."""
        small = self._make_image("small.jpg", width=800, height=600)
        large = self._make_image("large.jpg", width=4000, height=3000)

        result = rank_images([small, large])
        assert result[0].filename == "large.jpg"
        assert result[1].filename == "small.jpg"

    def test_empty_list(self):
        """Test rank_images with empty list."""
        assert rank_images([]) == []

    def test_no_p18(self):
        """Test rank_images without p18_filename."""
        featured = self._make_image("feat.jpg", assessment="featured")
        normal = self._make_image("normal.jpg")

        result = rank_images([normal, featured])
        assert result[0].filename == "feat.jpg"

    def test_combined_criteria(self):
        """Test P18 + featured + BITMAP combination beats everything."""
        best = self._make_image("best.jpg", assessment="featured", media_type="BITMAP")
        drawing = self._make_image(
            "draw.svg", assessment="featured", media_type="DRAWING"
        )

        result = rank_images([drawing, best], p18_filename="best.jpg")
        assert result[0].filename == "best.jpg"
