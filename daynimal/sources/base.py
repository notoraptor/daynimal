"""Base class for external data sources."""

import logging
import time
from abc import ABC, abstractmethod
from typing import TypeVar, Generic, Callable, Any

import httpx

from daynimal.config import settings

logger = logging.getLogger(__name__)

T = TypeVar("T")


def retry_with_backoff(
    func: Callable[[], httpx.Response], max_retries: int = 3, backoff_base: float = 1.0
) -> httpx.Response | None:
    """
    Execute HTTP request with exponential backoff retry.

    Retries on:
    - 429 (rate limit)
    - 503 (service unavailable)
    - Network errors (httpx.RequestError)

    Args:
        func: Callable that returns httpx.Response
        max_retries: Maximum number of retry attempts (default: 3)
        backoff_base: Base delay in seconds for exponential backoff (default: 1.0)

    Returns:
        Response object on success, None on failure after all retries
    """
    for attempt in range(max_retries):
        try:
            response = func()

            # Check if we should retry based on status code
            if response.status_code in (429, 503):
                if attempt < max_retries - 1:
                    # TODO: Respecter le header Retry-After si présent (429)
                    #   retry_after = response.headers.get("Retry-After")
                    delay = backoff_base * (2**attempt)
                    logger.warning(
                        f"HTTP {response.status_code} error, retrying in {delay}s "
                        f"(attempt {attempt + 1}/{max_retries})"
                    )
                    time.sleep(delay)
                    continue
                else:
                    logger.error(
                        f"HTTP {response.status_code} error, max retries exceeded"
                    )
                    return None

            # Success or non-retryable error
            return response

        except httpx.RequestError as e:
            if attempt < max_retries - 1:
                delay = backoff_base * (2**attempt)
                logger.warning(
                    f"Network error: {e}, retrying in {delay}s "
                    f"(attempt {attempt + 1}/{max_retries})"
                )
                time.sleep(delay)
            else:
                logger.error(f"Network error after {max_retries} attempts: {e}")

    return None


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
                    "User-Agent": "Daynimal/1.0 (https://github.com/notoraptor/daynimal)"
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

    def _request_with_retry(
        self, method: str, url: str, **kwargs: Any
    ) -> httpx.Response | None:
        """
        Make HTTP request with automatic retry on rate limit and service errors.

        Args:
            method: HTTP method ('get', 'post', etc.)
            url: URL to request
            **kwargs: Additional arguments for httpx (params, headers, etc.)

        Returns:
            Response object on success, None on failure
        """

        def _make_request() -> httpx.Response:
            if method.lower() == "get":
                return self.client.get(url, **kwargs)
            elif method.lower() == "post":
                return self.client.post(url, **kwargs)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

        return retry_with_backoff(_make_request)

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
