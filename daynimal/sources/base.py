"""Base class for external data sources."""

from abc import ABC, abstractmethod
from typing import TypeVar, Generic

import httpx

from daynimal.config import settings

T = TypeVar("T")


class DataSource(ABC, Generic[T]):
    """
    Abstract base class for external data sources.

    All data sources must implement methods to fetch data by source ID
    and by scientific name (taxonomy).
    """

    def __init__(self):
        self._client: httpx.Client | None = None

    @property
    def client(self) -> httpx.Client:
        """Lazy-initialized HTTP client."""
        if self._client is None:
            self._client = httpx.Client(
                timeout=settings.httpx_timeout,
                headers={
                    "User-Agent": "Daynimal/1.0 (https://github.com/daynimal; contact@example.com)"
                },
            )
        return self._client

    def close(self):
        """Close the HTTP client."""
        if self._client is not None:
            self._client.close()
            self._client = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    @property
    @abstractmethod
    def source_name(self) -> str:
        """Name of the data source (e.g., 'wikidata', 'wikipedia')."""
        ...

    @property
    @abstractmethod
    def license(self) -> str:
        """License of the data from this source."""
        ...

    @abstractmethod
    def get_by_source_id(self, source_id: str) -> T | None:
        """
        Fetch data using the source's native identifier.

        Args:
            source_id: The identifier used by this source (e.g., QID for Wikidata)

        Returns:
            The data object, or None if not found.
        """
        ...

    @abstractmethod
    def get_by_taxonomy(self, scientific_name: str) -> T | None:
        """
        Fetch data using a scientific (taxonomic) name.

        Args:
            scientific_name: The scientific name of the taxon (e.g., "Canis lupus")

        Returns:
            The data object, or None if not found.
        """
        ...

    @abstractmethod
    def search(self, query: str, limit: int = 10) -> list[T]:
        """
        Search for entities matching a query.

        Args:
            query: Search query string
            limit: Maximum number of results to return

        Returns:
            List of matching data objects.
        """
        ...
