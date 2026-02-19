"""
Tests for DataSource base class.

Tests context manager, client lifecycle, and abstract methods.
"""

from daynimal.sources.wikipedia import WikipediaAPI


class TestDataSourceBase:
    """Tests for DataSource base class functionality."""

    def test_close_with_no_client(self):
        """Test that close() works when client was never initialized."""
        api = WikipediaAPI()
        # Never access api.client, so _client stays None
        api.close()  # Should not raise

        assert api._client is None

    def test_context_manager_without_client_access(self):
        """Test context manager when client is never accessed."""
        with WikipediaAPI() as api:
            # Don't access api.client
            assert api._client is None

        # After exit, _client should still be None
        assert api._client is None

    def test_context_manager_with_client_access(self, mock_http_client):
        """Test context manager properly closes client."""
        with WikipediaAPI() as api:
            # Replace with mock before accessing
            api._client = mock_http_client
            # Access client to initialize
            _ = api._client

        # After exit, close() should have been called
        # Since we use a mock, we just verify the API doesn't crash

    def test_multiple_close_calls(self, mock_http_client):
        """Test that calling close() multiple times is safe."""
        api = WikipediaAPI()
        api._client = mock_http_client

        api.close()
        assert api._client is None

        # Second close should not raise
        api.close()
        assert api._client is None

    def test_client_lazy_initialization(self):
        """Test that client is only created when accessed."""
        api = WikipediaAPI()
        assert api._client is None

        # Access client property
        client = api.client
        assert client is not None
        assert api._client is not None

        # Second access returns same client
        client2 = api.client
        assert client is client2


# =============================================================================
# SECTION 2 : _request_with_retry — branches manquantes (lignes 134-137)
# =============================================================================


class TestRequestWithRetry:
    """Tests pour DataSource._request_with_retry(method, url, **kwargs)."""

    def test_post_request(self):
        """Vérifie que _request_with_retry('POST', url, data=...) appelle
        self.client.post(url, data=...) au lieu de self.client.get.
        On crée une WikidataAPI avec un mock client et on vérifie
        que client.post est appelé."""
        # todo
        pass

    def test_unsupported_method_raises_value_error(self):
        """Vérifie que _request_with_retry('DELETE', url) lève
        ValueError('Unsupported method: DELETE').
        Seuls GET et POST sont supportés."""
        # todo
        pass

    def test_get_request_passes_kwargs(self):
        """Vérifie que _request_with_retry('GET', url, params={'q': 'test'})
        passe les kwargs à self.client.get."""
        # todo
        pass
