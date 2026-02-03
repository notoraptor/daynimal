"""
Tests for WikipediaAPI.

These tests use mocked HTTP responses - no network access required.
"""

from daynimal.sources.wikipedia import WikipediaAPI
from daynimal.schemas import License
from tests.fixtures.wikipedia_responses import (
    WIKIPEDIA_ARTICLE_CANIS_LUPUS_FR,
    WIKIPEDIA_ARTICLE_CANIS_LUPUS_EN,
    WIKIPEDIA_NOT_FOUND,
)


class TestWikipediaAPI:
    """Tests for WikipediaAPI class."""

    def test_get_by_source_id_returns_article(self, mock_wikipedia_client):
        """Test fetching article by page ID."""
        api = WikipediaAPI(languages=["fr", "en"])
        api._client = mock_wikipedia_client

        article = api.get_by_source_id("3135", language="fr")

        assert article is not None
        assert article.title == "Canis lupus"
        assert article.language == "fr"
        assert article.page_id == 3135
        assert "Loup" in article.summary

    def test_get_by_source_id_by_title(self, mock_wikipedia_client):
        """Test fetching article by title."""
        api = WikipediaAPI(languages=["fr", "en"])
        api._client = mock_wikipedia_client

        article = api.get_by_source_id("Canis lupus", language="fr")

        assert article is not None
        assert article.title == "Canis lupus"

    def test_get_by_taxonomy_prefers_french(self, mock_http_client):
        """Test that French Wikipedia is tried first."""
        mock_http_client.add_response(
            "fr.wikipedia.org", WIKIPEDIA_ARTICLE_CANIS_LUPUS_FR
        )
        mock_http_client.add_response(
            "en.wikipedia.org", WIKIPEDIA_ARTICLE_CANIS_LUPUS_EN
        )

        api = WikipediaAPI(languages=["fr", "en"])
        api._client = mock_http_client

        article = api.get_by_taxonomy("Canis lupus")

        assert article is not None
        assert article.language == "fr"

    def test_get_by_source_id_not_found(self, mock_http_client):
        """Test handling of non-existent article."""
        mock_http_client.add_response("fr.wikipedia.org", WIKIPEDIA_NOT_FOUND)

        api = WikipediaAPI(languages=["fr"])
        api._client = mock_http_client

        article = api.get_by_source_id("NonExistentArticle12345", language="fr")

        assert article is None

    def test_license_is_cc_by_sa(self, mock_wikipedia_client):
        """Test that license is always CC-BY-SA."""
        api = WikipediaAPI(languages=["fr"])
        api._client = mock_wikipedia_client

        article = api.get_by_source_id("3135", language="fr")

        assert article.license == License.CC_BY_SA

    def test_source_name_and_license(self):
        """Test that source metadata is correct."""
        api = WikipediaAPI()

        assert api.source_name == "wikipedia"
        assert api.license == "CC-BY-SA"


class TestWikipediaAttributions:
    """Tests for Wikipedia attribution generation."""

    def test_get_attribution_text(self, mock_wikipedia_client):
        """Test attribution text generation."""
        api = WikipediaAPI(languages=["fr"])
        api._client = mock_wikipedia_client

        article = api.get_by_source_id("3135", language="fr")
        attribution = article.get_attribution_text()

        assert "Canis lupus" in attribution
        assert "Wikipedia" in attribution
        assert "CC-BY-SA" in attribution
        assert "fr.wikipedia.org" in attribution

    def test_get_attribution_html(self, mock_wikipedia_client):
        """Test HTML attribution with links."""
        api = WikipediaAPI(languages=["fr"])
        api._client = mock_wikipedia_client

        article = api.get_by_source_id("3135", language="fr")
        html = article.get_attribution_html()

        assert "<a href=" in html
        assert "Canis lupus" in html
        assert "CC-BY-SA" in html

    def test_article_url_property(self, mock_wikipedia_client):
        """Test article URL generation."""
        api = WikipediaAPI(languages=["fr"])
        api._client = mock_wikipedia_client

        article = api.get_by_source_id("3135", language="fr")

        assert article.article_url == "https://fr.wikipedia.org/wiki/Canis_lupus"

    def test_license_url_property(self, mock_wikipedia_client):
        """Test license URL."""
        api = WikipediaAPI(languages=["fr"])
        api._client = mock_wikipedia_client

        article = api.get_by_source_id("3135", language="fr")

        assert "creativecommons.org" in article.license_url
        assert "by-sa" in article.license_url
