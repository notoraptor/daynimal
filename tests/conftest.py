"""
Pytest configuration and shared fixtures.

This module provides mock HTTP clients and other shared test infrastructure
to enable testing without network access.
"""

import pytest
from unittest.mock import MagicMock
import httpx
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from daynimal.db.models import Base


class MockResponse:
    """Mock httpx.Response for testing."""

    def __init__(self, json_data: dict, status_code: int = 200):
        self._json_data = json_data
        self.status_code = status_code

    def json(self):
        return self._json_data

    def raise_for_status(self):
        if self.status_code >= 400:
            raise httpx.HTTPStatusError(
                f"HTTP {self.status_code}", request=MagicMock(), response=self
            )


class MockHttpClient:
    """
    Mock HTTP client that returns predefined responses.

    Usage:
        client = MockHttpClient()
        client.add_response("https://api.example.com/endpoint", {"data": "value"})

        # In test:
        response = client.get("https://api.example.com/endpoint")
        assert response.json() == {"data": "value"}
    """

    def __init__(self):
        self._responses: dict[str, MockResponse] = {}
        self._default_response: MockResponse | None = None

    def add_response(self, url_pattern: str, json_data: dict, status_code: int = 200):
        """Add a mock response for a URL pattern."""
        self._responses[url_pattern] = MockResponse(json_data, status_code)

    def set_default_response(self, json_data: dict, status_code: int = 200):
        """Set a default response for unmatched URLs."""
        self._default_response = MockResponse(json_data, status_code)

    def get(self, url: str, **kwargs) -> MockResponse:
        """Mock GET request."""
        # Check for exact match first
        if url in self._responses:
            return self._responses[url]

        # Build full URL representation including params for matching
        params = kwargs.get("params", {})
        full_url = url + "?" + "&".join(f"{k}={v}" for k, v in params.items())

        # Check for partial match (pattern in URL or params)
        for pattern, response in self._responses.items():
            if pattern in url or pattern in full_url:
                return response

        # Return default or raise
        if self._default_response:
            return self._default_response

        raise ValueError(f"No mock response configured for URL: {url}")

    def close(self):
        """Mock close method."""
        pass

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass


@pytest.fixture
def mock_http_client():
    """Provide a fresh MockHttpClient for each test."""
    return MockHttpClient()


@pytest.fixture
def mock_wikidata_client(mock_http_client):
    """Pre-configured mock client for Wikidata API tests."""
    from tests.fixtures.wikidata_responses import (
        WIKIDATA_ENTITY_Q18498,
        WIKIDATA_SPARQL_CANIS_LUPUS,
        WIKIDATA_SEARCH_WOLF,
    )

    mock_http_client.add_response("wbgetentities", WIKIDATA_ENTITY_Q18498)
    mock_http_client.add_response(
        "query.wikidata.org/sparql", WIKIDATA_SPARQL_CANIS_LUPUS
    )
    mock_http_client.add_response("wbsearchentities", WIKIDATA_SEARCH_WOLF)

    return mock_http_client


@pytest.fixture
def mock_wikipedia_client(mock_http_client):
    """Pre-configured mock client for Wikipedia API tests."""
    from tests.fixtures.wikipedia_responses import WIKIPEDIA_ARTICLE_CANIS_LUPUS_FR

    mock_http_client.add_response("fr.wikipedia.org", WIKIPEDIA_ARTICLE_CANIS_LUPUS_FR)

    return mock_http_client


@pytest.fixture
def mock_commons_client(mock_http_client):
    """Pre-configured mock client for Wikimedia Commons API tests."""
    from tests.fixtures.commons_responses import COMMONS_CATEGORY_CANIS_LUPUS

    mock_http_client.add_response("commons.wikimedia.org", COMMONS_CATEGORY_CANIS_LUPUS)

    return mock_http_client


@pytest.fixture
def session():
    """
    Provide a clean in-memory SQLite database session for each test.

    Creates all tables, yields the session for testing, then tears down.
    """
    # Create in-memory SQLite database
    engine = create_engine("sqlite:///:memory:", echo=False)

    # Create all tables
    Base.metadata.create_all(engine)

    # Create session
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()

    yield session

    # Cleanup
    session.close()
    Base.metadata.drop_all(engine)
