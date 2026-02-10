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
    WIKIPEDIA_FULL_ARTICLE,
    WIKIPEDIA_EMPTY_PAGES,
    WIKIPEDIA_SEARCH_EMPTY,
    WIKIPEDIA_SEARCH_MULTIPLE,
    WIKIPEDIA_SEARCH_WOLF,
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

    def test_get_by_source_id_empty_pages(self, mock_http_client):
        """Test handling of empty pages response."""
        mock_http_client.add_response("en.wikipedia.org", WIKIPEDIA_EMPTY_PAGES)

        api = WikipediaAPI(languages=["en"])
        api._client = mock_http_client

        article = api.get_by_source_id("12345", language="en")

        assert article is None

    def test_search(self, mock_http_client):
        """Test search functionality."""
        # The search() method makes one search API call, then calls get_by_source_id for each result
        # We use default_response to handle all subsequent get_by_source_id calls
        mock_http_client.add_response("list=search", WIKIPEDIA_SEARCH_MULTIPLE)
        mock_http_client.set_default_response(WIKIPEDIA_ARTICLE_CANIS_LUPUS_EN)

        api = WikipediaAPI(languages=["en"])
        api._client = mock_http_client

        results = api.search("wolf", limit=10, language="en")

        assert len(results) > 0
        assert all(isinstance(article.page_id, int) for article in results)

    def test_search_empty_results(self, mock_http_client):
        """Test search with no results."""
        mock_http_client.add_response("en.wikipedia.org", WIKIPEDIA_SEARCH_EMPTY)

        api = WikipediaAPI(languages=["en"])
        api._client = mock_http_client

        results = api.search("NonExistentSpecies12345", limit=10, language="en")

        assert results == []

    def test_get_full_article(self, mock_http_client):
        """Test fetching full article content."""
        mock_http_client.add_response("fr.wikipedia.org", WIKIPEDIA_FULL_ARTICLE)

        api = WikipediaAPI(languages=["fr"])
        api._client = mock_http_client

        article = api.get_full_article(3135, language="fr")

        assert article is not None
        assert article.title == "Canis lupus"
        assert article.full_text is not None
        assert len(article.full_text) > 200  # Full text is longer than summary

    def test_get_full_article_not_found(self, mock_http_client):
        """Test get_full_article with non-existent page."""
        mock_http_client.add_response("fr.wikipedia.org", WIKIPEDIA_NOT_FOUND)

        api = WikipediaAPI(languages=["fr"])
        api._client = mock_http_client

        article = api.get_full_article(99999, language="fr")

        assert article is None

    def test_get_by_taxonomy_fallback_search(self, mock_http_client):
        """Test that get_by_taxonomy falls back to search when exact title fails."""
        # First call to get_by_source_id (exact title with titles=) returns None
        mock_http_client.add_response("titles=", WIKIPEDIA_NOT_FOUND)
        # Second call in _search_in_language (search API with list=search)
        mock_http_client.add_response("list=search", WIKIPEDIA_SEARCH_WOLF)
        # Third call to get_by_source_id for the search result (pageids=)
        mock_http_client.add_response("pageids=", WIKIPEDIA_ARTICLE_CANIS_LUPUS_EN)

        api = WikipediaAPI(languages=["en"])
        api._client = mock_http_client

        article = api.get_by_taxonomy("Canis lupus")

        assert article is not None
        assert article.page_id == 39365

    def test_get_by_taxonomy_no_match_any_language(self, mock_http_client):
        """Test that get_by_taxonomy returns None when no language finds an article."""
        # Both exact title and search fail for both languages
        mock_http_client.add_response("titles=", WIKIPEDIA_NOT_FOUND)
        mock_http_client.add_response("list=search", WIKIPEDIA_SEARCH_EMPTY)

        api = WikipediaAPI(languages=["fr", "en"])
        api._client = mock_http_client

        article = api.get_by_taxonomy("NonExistentSpecies")

        assert article is None

    def test_search_in_language_uses_first_result_if_no_exact_match(
        self, mock_http_client
    ):
        """Test _search_in_language returns first result when no title match."""
        # Exact title match fails
        mock_http_client.add_response("titles=", WIKIPEDIA_NOT_FOUND)
        # Search returns results without exact title match
        mock_http_client.add_response(
            "list=search",
            {
                "query": {
                    "search": [{"pageid": 99999, "title": "Some Other Wolf Species"}]
                }
            },
        )
        # get_by_source_id for the search result
        mock_http_client.add_response("pageids=", WIKIPEDIA_ARTICLE_CANIS_LUPUS_EN)

        api = WikipediaAPI(languages=["en"])
        api._client = mock_http_client

        article = api.get_by_taxonomy("Canis lupus")

        assert article is not None
        # Should return first search result even without exact match
        assert article.page_id == 39365


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
