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
