"""Application state management for Daynimal UI.

This module provides centralized state management for the Flet application,
including repository lifecycle, current animal display, and caching.
"""

import threading
from dataclasses import dataclass, field
from typing import Optional

from daynimal.image_cache import ImageCacheService
from daynimal.repository import AnimalRepository
from daynimal.schemas import AnimalInfo


@dataclass
class AppState:
    """Shared application state across all views.

    This class manages:
    - Repository singleton (lazy initialization, thread-safe)
    - Currently displayed animal
    - Image carousel state
    - Statistics cache
    - Current view tracking

    The repository is created on first access and properly closed during cleanup.
    """

    _repository: Optional[AnimalRepository] = field(default=None, init=False)
    _repo_lock: threading.Lock = field(default_factory=threading.Lock, init=False)
    current_animal: Optional[AnimalInfo] = None
    current_image_index: int = 0
    cached_stats: Optional[dict] = None
    current_view_name: str = "today"

    @property
    def image_cache(self) -> ImageCacheService:
        """Get image cache service from repository."""
        return self.repository.image_cache

    @property
    def repository(self) -> AnimalRepository:
        """Get or create repository (lazy initialization, thread-safe).

        Returns:
            AnimalRepository: The singleton repository instance.
        """
        if self._repository is None:
            with self._repo_lock:
                if self._repository is None:
                    self._repository = AnimalRepository()
        return self._repository

    def close_repository(self):
        """Close repository and cleanup resources.

        Should be called during application shutdown (on_disconnect, on_close).
        """
        with self._repo_lock:
            if self._repository:
                self._repository.close()
                self._repository = None

    def reset_animal_display(self):
        """Reset animal display state (used when loading new animal)."""
        self.current_animal = None
        self.current_image_index = 0
