"""
Tests for HTTP resilience: retry with exponential backoff.

Tests the retry_with_backoff function and API behavior with
rate limits (429), service unavailable (503), and network errors.
"""

from unittest.mock import MagicMock, patch

import httpx

from daynimal.sources.base import retry_with_backoff
from daynimal.sources.wikidata import WikidataAPI
from daynimal.sources.wikipedia import WikipediaAPI
from daynimal.sources.commons import CommonsAPI


class TestRetryWithBackoff:
    """Tests for retry_with_backoff function."""

    def test_success_on_first_attempt(self):
        """Test that successful response is returned immediately."""
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 200

        func = MagicMock(return_value=mock_response)
        result = retry_with_backoff(func)

        assert result == mock_response
        assert func.call_count == 1

    def test_retry_on_429(self):
        """Test retry on 429 rate limit error."""
        # First two calls return 429, third succeeds
        response_429 = MagicMock(spec=httpx.Response)
        response_429.status_code = 429
        response_200 = MagicMock(spec=httpx.Response)
        response_200.status_code = 200

        func = MagicMock(side_effect=[response_429, response_429, response_200])

        with patch("time.sleep") as mock_sleep:
            result = retry_with_backoff(func, max_retries=3, backoff_base=0.1)

        assert result == response_200
        assert func.call_count == 3
        # Verify exponential backoff: 0.1s, 0.2s
        assert mock_sleep.call_count == 2
        mock_sleep.assert_any_call(0.1)
        mock_sleep.assert_any_call(0.2)

    def test_retry_on_503(self):
        """Test retry on 503 service unavailable."""
        response_503 = MagicMock(spec=httpx.Response)
        response_503.status_code = 503
        response_200 = MagicMock(spec=httpx.Response)
        response_200.status_code = 200

        func = MagicMock(side_effect=[response_503, response_200])

        with patch("time.sleep") as mock_sleep:
            result = retry_with_backoff(func, max_retries=2, backoff_base=0.1)

        assert result == response_200
        assert func.call_count == 2
        assert mock_sleep.call_count == 1

    def test_returns_none_after_max_retries(self):
        """Test that None is returned after exhausting retries."""
        response_429 = MagicMock(spec=httpx.Response)
        response_429.status_code = 429

        func = MagicMock(return_value=response_429)

        with patch("time.sleep"):
            result = retry_with_backoff(func, max_retries=3, backoff_base=0.01)

        assert result is None
        assert func.call_count == 3

    def test_no_retry_on_404(self):
        """Test that 404 and other 4xx errors don't trigger retry."""
        response_404 = MagicMock(spec=httpx.Response)
        response_404.status_code = 404

        func = MagicMock(return_value=response_404)
        result = retry_with_backoff(func)

        assert result == response_404
        assert func.call_count == 1

    def test_retry_on_network_error(self):
        """Test retry on network errors (httpx.RequestError)."""
        error = httpx.RequestError("Connection failed")
        response_200 = MagicMock(spec=httpx.Response)
        response_200.status_code = 200

        func = MagicMock(side_effect=[error, response_200])

        with patch("time.sleep") as mock_sleep:
            result = retry_with_backoff(func, max_retries=2, backoff_base=0.1)

        assert result == response_200
        assert func.call_count == 2
        assert mock_sleep.call_count == 1

    def test_returns_none_after_network_errors(self):
        """Test that None is returned after persistent network errors."""
        error = httpx.RequestError("Connection timeout")
        func = MagicMock(side_effect=error)

        with patch("time.sleep"):
            result = retry_with_backoff(func, max_retries=3, backoff_base=0.01)

        assert result is None
        assert func.call_count == 3


# Note: Les tests API ci-dessous ne vérifient que le cas "échec final après
# tous les retries" car MockHttpClient retourne toujours la même réponse pour
# un pattern donné (pas de side_effect). Le scénario "429 puis 200" (récupération
# après retry) est couvert dans TestRetryWithBackoff ci-dessus.


class TestWikidataAPIResilience:
    """Tests for WikidataAPI error handling."""

    def test_get_by_source_id_returns_none_on_429(self, mock_http_client):
        """Test that get_by_source_id returns None after 429 retries."""
        mock_http_client.add_response("wbgetentities", {}, status_code=429)

        api = WikidataAPI()
        api._client = mock_http_client

        with patch("time.sleep"):
            result = api.get_by_source_id("Q18498")

        assert result is None

    def test_get_by_source_id_returns_none_on_503(self, mock_http_client):
        """Test that get_by_source_id returns None after 503 retries."""
        mock_http_client.add_response("wbgetentities", {}, status_code=503)

        api = WikidataAPI()
        api._client = mock_http_client

        with patch("time.sleep"):
            result = api.get_by_source_id("Q18498")

        assert result is None

    def test_search_returns_empty_list_on_error(self, mock_http_client):
        """Test that search returns [] instead of crashing on error."""
        mock_http_client.add_response("wbsearchentities", {}, status_code=503)

        api = WikidataAPI()
        api._client = mock_http_client

        with patch("time.sleep"):
            result = api.search("wolf")

        assert result == []


class TestWikipediaAPIResilience:
    """Tests for WikipediaAPI error handling."""

    def test_get_by_source_id_returns_none_on_429(self, mock_http_client):
        """Test that get_by_source_id returns None after 429 retries."""
        mock_http_client.add_response("en.wikipedia.org", {}, status_code=429)

        api = WikipediaAPI()
        api._client = mock_http_client

        with patch("time.sleep"):
            result = api.get_by_source_id("12345")

        assert result is None

    def test_get_by_source_id_returns_none_on_503(self, mock_http_client):
        """Test that get_by_source_id returns None after 503 retries."""
        mock_http_client.add_response("en.wikipedia.org", {}, status_code=503)

        api = WikipediaAPI()
        api._client = mock_http_client

        with patch("time.sleep"):
            result = api.get_by_source_id("12345")

        assert result is None

    def test_search_returns_empty_list_on_error(self, mock_http_client):
        """Test that search returns [] instead of crashing on error."""
        mock_http_client.add_response("en.wikipedia.org", {}, status_code=503)

        api = WikipediaAPI()
        api._client = mock_http_client

        with patch("time.sleep"):
            result = api.search("wolf")

        assert result == []


class TestCommonsAPIResilience:
    """Tests for CommonsAPI error handling."""

    def test_get_by_source_id_returns_none_on_429(self, mock_http_client):
        """Test that get_by_source_id returns None after 429 retries."""
        mock_http_client.add_response("commons.wikimedia.org", {}, status_code=429)

        api = CommonsAPI()
        api._client = mock_http_client

        with patch("time.sleep"):
            result = api.get_by_source_id("Wolf.jpg")

        assert result is None

    def test_get_by_source_id_returns_none_on_503(self, mock_http_client):
        """Test that get_by_source_id returns None after 503 retries."""
        mock_http_client.add_response("commons.wikimedia.org", {}, status_code=503)

        api = CommonsAPI()
        api._client = mock_http_client

        with patch("time.sleep"):
            result = api.get_by_source_id("Wolf.jpg")

        assert result is None

    def test_search_returns_empty_list_on_error(self, mock_http_client):
        """Test that search returns [] instead of crashing on error."""
        mock_http_client.add_response("commons.wikimedia.org", {}, status_code=503)

        api = CommonsAPI()
        api._client = mock_http_client

        with patch("time.sleep"):
            result = api.search("wolf")

        assert result == []

    def test_get_images_for_wikidata_returns_empty_on_error(self, mock_http_client):
        """Test that get_images_for_wikidata returns [] on error."""
        mock_http_client.add_response("commons.wikimedia.org", {}, status_code=503)

        api = CommonsAPI()
        api._client = mock_http_client

        with patch("time.sleep"):
            result = api.get_images_for_wikidata("Q18498")

        assert result == []
