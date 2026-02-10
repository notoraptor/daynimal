"""Network connectivity detection for offline mode.

Provides a lightweight connectivity check to avoid long API timeouts
when the device is offline. Uses a HEAD request to wikidata.org with
a short timeout and caches the result for 60 seconds.
"""

import logging
import threading
import time

import httpx

logger = logging.getLogger(__name__)


class ConnectivityService:
    """Detects network connectivity via a lightweight HEAD request."""

    CHECK_URL = "https://www.wikidata.org"
    TIMEOUT = 5.0
    CACHE_TTL = 60.0

    def __init__(self):
        self._is_online: bool | None = None
        self._last_check: float = 0
        self._lock = threading.Lock()
        self._force_offline: bool = False

    @property
    def is_online(self) -> bool:
        """Return cached connectivity state, refreshing if TTL expired."""
        if self._force_offline:
            return False
        now = time.monotonic()
        if self._is_online is None or (now - self._last_check) > self.CACHE_TTL:
            self.check()
        return self._is_online

    def check(self) -> bool:
        """Force an immediate connectivity check."""
        if self._force_offline:
            return False
        with self._lock:
            try:
                resp = httpx.head(
                    self.CHECK_URL, timeout=self.TIMEOUT, follow_redirects=True
                )
                self._is_online = resp.status_code < 500
            except (httpx.RequestError, httpx.TimeoutException):
                self._is_online = False
            self._last_check = time.monotonic()
            logger.debug(
                f"Connectivity check: {'online' if self._is_online else 'offline'}"
            )
            return self._is_online

    def set_offline(self):
        """Mark as offline (e.g. after API failure)."""
        self._is_online = False
        self._last_check = time.monotonic()

    def set_online(self):
        """Mark as online."""
        self._is_online = True
        self._last_check = time.monotonic()

    @property
    def force_offline(self) -> bool:
        """Whether offline mode is forced by user."""
        return self._force_offline

    @force_offline.setter
    def force_offline(self, value: bool):
        """Set forced offline mode."""
        self._force_offline = value
