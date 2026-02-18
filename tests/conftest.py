"""
Pytest configuration and shared fixtures.

This module provides mock HTTP clients and other shared test infrastructure
to enable testing without network access.
"""

import pytest
from unittest.mock import MagicMock
import httpx
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from daynimal.db.models import Base


class MockResponse:
    """Mock httpx.Response for testing."""

    def __init__(self, json_data: dict, status_code: int = 200):
        self._json_data = json_data
        self.status_code = status_code

    @property
    def is_success(self) -> bool:
        return 200 <= self.status_code < 300

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
def mock_gbif_media_client(mock_http_client):
    """Pre-configured mock client for GBIF Media API tests."""
    from tests.fixtures.gbif_media_responses import GBIF_MEDIA_MIXED_LICENSES

    mock_http_client.add_response("api.gbif.org", GBIF_MEDIA_MIXED_LICENSES)

    return mock_http_client


@pytest.fixture
def mock_phylopic_client(mock_http_client):
    """Pre-configured mock client for PhyloPic API tests."""
    from tests.fixtures.phylopic_responses import (
        PHYLOPIC_RESOLVE_SUCCESS,
        PHYLOPIC_NODE_WITH_IMAGE,
    )

    mock_http_client.add_response("resolve/gbif.org", PHYLOPIC_RESOLVE_SUCCESS)
    mock_http_client.add_response("api.phylopic.org/nodes", PHYLOPIC_NODE_WITH_IMAGE)

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
    engine.dispose()


@pytest.fixture
def populated_session(session):
    """
    Provide a session populated with diverse taxa for repository testing.

    Creates 50 taxa with:
    - 30 species (10 enriched, 20 not enriched)
    - 10 genus, 5 family, 5 order
    - Vernacular names in en, fr, es
    - Non-contiguous IDs (gaps)
    - Some synonyms
    """
    from daynimal.db.models import TaxonModel, VernacularNameModel

    taxa = []

    # Species (30 total: IDs 1-30)
    for i in range(1, 31):
        is_enriched = i <= 10  # First 10 are enriched
        taxon = TaxonModel(
            taxon_id=i,
            scientific_name=f"Species {i}",
            canonical_name=f"Species {i}",
            rank="species",
            kingdom="Animalia",
            phylum="Chordata",
            class_="Mammalia",
            order="Carnivora",
            family="Felidae",
            genus="Felis",
            is_enriched=is_enriched,
            is_synonym=False,
        )
        taxa.append(taxon)

        # Add vernacular names
        for lang, name in [
            ("en", f"Species {i} English"),
            ("fr", f"Espèce {i}"),
            ("es", f"Especie {i}"),
        ]:
            vn = VernacularNameModel(taxon_id=i, name=name, language=lang)
            session.add(vn)

    # Genus (10 total: IDs 50-59, gaps from 30-50)
    for i in range(50, 60):
        taxon = TaxonModel(
            taxon_id=i,
            scientific_name=f"Genus{i}",
            canonical_name=f"Genus{i}",
            rank="genus",
            kingdom="Animalia",
            phylum="Chordata",
            class_="Mammalia",
            order="Carnivora",
            family="Felidae",
            is_enriched=False,
            is_synonym=False,
        )
        taxa.append(taxon)

        vn = VernacularNameModel(taxon_id=i, name=f"Genus {i} common", language="en")
        session.add(vn)

    # Family (5 total: IDs 100-104)
    for i in range(100, 105):
        taxon = TaxonModel(
            taxon_id=i,
            scientific_name=f"Family{i}",
            canonical_name=f"Family{i}",
            rank="family",
            kingdom="Animalia",
            phylum="Chordata",
            class_="Mammalia",
            order="Carnivora",
            is_enriched=False,
            is_synonym=False,
        )
        taxa.append(taxon)

    # Order (5 total: IDs 200-204)
    for i in range(200, 205):
        taxon = TaxonModel(
            taxon_id=i,
            scientific_name=f"Order{i}",
            canonical_name=f"Order{i}",
            rank="order",
            kingdom="Animalia",
            phylum="Chordata",
            class_="Mammalia",
            is_enriched=False,
            is_synonym=False,
        )
        taxa.append(taxon)

    # Add a few synonyms (IDs 300-302)
    for i in range(300, 303):
        taxon = TaxonModel(
            taxon_id=i,
            scientific_name=f"Synonym {i}",
            canonical_name=f"Synonym {i}",
            rank="species",
            kingdom="Animalia",
            phylum="Chordata",
            class_="Mammalia",
            order="Carnivora",
            family="Felidae",
            genus="Felis",
            is_enriched=False,
            is_synonym=True,
            accepted_id=1,  # Synonym of taxon 1
        )
        taxa.append(taxon)

    # Add all taxa
    for taxon in taxa:
        session.add(taxon)

    session.commit()

    return session


@pytest.fixture
def session_with_fts(populated_session):
    """
    Provide a session with FTS5 initialized for full-text search testing.

    Note: This fixture may be skipped if SQLite doesn't have FTS5 support.
    """
    from sqlalchemy import text

    try:
        # Test if FTS5 is available
        populated_session.execute(
            text("CREATE VIRTUAL TABLE test_fts USING fts5(content)")
        )
        populated_session.execute(text("DROP TABLE test_fts"))

        # FTS5 available, create taxa_fts table
        # Note: 'rank' is a reserved FTS5 keyword, so we use 'taxonomic_rank'
        populated_session.execute(
            text("""
            CREATE VIRTUAL TABLE taxa_fts USING fts5(
                taxon_id UNINDEXED,
                scientific_name,
                canonical_name,
                vernacular_names,
                taxonomic_rank UNINDEXED
            )
        """)
        )

        # Populate FTS table
        # Match the real init_fts.py implementation
        populated_session.execute(
            text("""
            INSERT INTO taxa_fts(taxon_id, scientific_name, canonical_name, vernacular_names, taxonomic_rank)
            SELECT
                t.taxon_id,
                t.scientific_name,
                COALESCE(t.canonical_name, t.scientific_name),
                COALESCE(GROUP_CONCAT(v.name, ' '), ''),
                t.rank
            FROM taxa t
            LEFT JOIN vernacular_names v ON t.taxon_id = v.taxon_id
            GROUP BY t.taxon_id
        """)
        )

        populated_session.commit()

        return populated_session

    except Exception:
        pytest.skip("FTS5 not available in SQLite")


@pytest.fixture
def session_without_fts(populated_session):
    """
    Provide a session without FTS5 (for testing fallback).

    This is simply the populated_session without FTS5 table created.
    """
    return populated_session


@pytest.fixture
def mock_enrichment_data():
    """
    Provide mock enrichment data (Wikidata, Wikipedia, Commons) for testing.

    Returns a dict with WikidataEntity, WikipediaArticle, and CommonsImage objects.
    """
    from daynimal.schemas import (
        WikidataEntity,
        WikipediaArticle,
        CommonsImage,
        ConservationStatus,
        License,
    )

    wikidata = WikidataEntity(
        qid="Q144",
        labels={"en": "Dog", "fr": "Chien"},
        descriptions={"en": "Domesticated canine", "fr": "Canidé domestique"},
        iucn_status=ConservationStatus.LEAST_CONCERN,
        habitat=["Terrestrial"],
        diet=["Omnivore"],
        lifespan="10-13 years",
        mass="10-30 kg",
        length="60-110 cm",
        image_url="https://commons.wikimedia.org/wiki/File:Dog.jpg",
    )

    wikipedia = WikipediaArticle(
        title="Dog",
        language="en",
        page_id=4269567,
        summary="The dog is a domesticated descendant of the wolf.",
        url="https://en.wikipedia.org/wiki/Dog",
    )

    images = [
        CommonsImage(
            filename="Dog1.jpg",
            url="https://upload.wikimedia.org/wikipedia/commons/Dog1.jpg",
            thumbnail_url="https://upload.wikimedia.org/wikipedia/commons/thumb/Dog1.jpg",
            width=800,
            height=600,
            author="John Photographer",
            license=License.CC_BY_SA,
            description="A dog",
        ),
        CommonsImage(
            filename="Dog2.jpg",
            url="https://upload.wikimedia.org/wikipedia/commons/Dog2.jpg",
            thumbnail_url="https://upload.wikimedia.org/wikipedia/commons/thumb/Dog2.jpg",
            width=1024,
            height=768,
            author="Jane Photographer",
            license=License.CC_BY,
            description="Another dog",
        ),
    ]

    return {"wikidata": wikidata, "wikipedia": wikipedia, "images": images}


@pytest.fixture
def repo_with_cache(populated_session, mock_enrichment_data):
    """
    Provide a repository with pre-populated enrichment cache.

    Taxon ID 1 has cached Wikidata, Wikipedia, and images.
    """
    from daynimal.db.models import EnrichmentCacheModel
    from daynimal.repository import AnimalRepository
    import json

    repo = AnimalRepository(session=populated_session)

    # Add cache entries for taxon 1
    wikidata_cache = EnrichmentCacheModel(
        taxon_id=1,
        source="wikidata",
        data=json.dumps(repo._to_dict(mock_enrichment_data["wikidata"])),
    )
    populated_session.add(wikidata_cache)

    wikipedia_cache = EnrichmentCacheModel(
        taxon_id=1,
        source="wikipedia",
        data=json.dumps(repo._to_dict(mock_enrichment_data["wikipedia"])),
    )
    populated_session.add(wikipedia_cache)

    images_cache = EnrichmentCacheModel(
        taxon_id=1,
        source="commons",  # Fixed: _get_cached_images() searches for "commons"
        data=json.dumps([repo._to_dict(img) for img in mock_enrichment_data["images"]]),
    )
    populated_session.add(images_cache)

    populated_session.commit()

    yield repo

    repo.close()


@pytest.fixture
def repo(populated_session):
    """
    Provide an AnimalRepository backed by the populated in-memory session.

    Properly closes the repository (and its lazy-initialized API clients)
    after the test finishes to avoid ResourceWarning on unclosed connections.
    """
    from daynimal.repository import AnimalRepository

    repo = AnimalRepository(session=populated_session)
    yield repo
    repo.close()


@pytest.fixture
def sync_executor():
    """
    Patch ThreadPoolExecutor to execute tasks synchronously in the same thread.

    This is necessary for tests that use SQLite in-memory databases, which cannot
    be accessed from different threads. The patch makes executor.submit() execute
    the function immediately instead of in a separate thread.
    """
    from unittest.mock import MagicMock, patch
    from concurrent.futures import Future

    def immediate_submit(fn, *args, **kwargs):
        """Execute function immediately and return a completed Future."""
        future = Future()
        try:
            result = fn(*args, **kwargs)
            future.set_result(result)
        except Exception as e:
            future.set_exception(e)
        return future

    mock_executor = MagicMock()
    mock_executor.submit = immediate_submit
    mock_executor.__enter__ = MagicMock(return_value=mock_executor)
    mock_executor.__exit__ = MagicMock(return_value=False)

    with patch("daynimal.repository.ThreadPoolExecutor", return_value=mock_executor):
        yield
