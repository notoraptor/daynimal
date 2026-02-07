"""
Animal Repository - aggregates data from local DB and external APIs.

This is the main interface for retrieving enriched animal information.
It handles:
- Querying the local GBIF-based taxonomy database
- Fetching additional data from Wikidata, Wikipedia, Commons
- Caching enrichment data locally
"""

import json
import logging
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, UTC

from sqlalchemy import func, or_, text
from sqlalchemy.orm import Session

from daynimal.db.models import (
    TaxonModel,
    VernacularNameModel,
    EnrichmentCacheModel,
    AnimalHistoryModel,
)
from daynimal.db.session import get_session
from daynimal.schemas import (
    AnimalInfo,
    Taxon,
    TaxonomicRank,
    WikidataEntity,
    WikipediaArticle,
    CommonsImage,
)
from daynimal.sources.wikidata import WikidataAPI
from daynimal.sources.wikipedia import WikipediaAPI

# Logger for this module
logger = logging.getLogger(__name__)
from daynimal.sources.commons import CommonsAPI


class AnimalRepository:
    """
    Repository for accessing animal information.

    Combines local taxonomy data (from GBIF dump) with
    on-demand enrichment from external APIs.
    """

    def __init__(self, session: Session | None = None):
        self.session = session or get_session()
        self._wikidata: WikidataAPI | None = None
        self._wikipedia: WikipediaAPI | None = None
        self._commons: CommonsAPI | None = None

    @property
    def wikidata(self) -> WikidataAPI:
        if self._wikidata is None:
            self._wikidata = WikidataAPI()
        return self._wikidata

    @property
    def wikipedia(self) -> WikipediaAPI:
        if self._wikipedia is None:
            self._wikipedia = WikipediaAPI()
        return self._wikipedia

    @property
    def commons(self) -> CommonsAPI:
        if self._commons is None:
            self._commons = CommonsAPI()
        return self._commons

    def close(self):
        """Close all connections."""
        if self._wikidata:
            self._wikidata.close()
        if self._wikipedia:
            self._wikipedia.close()
        if self._commons:
            self._commons.close()
        self.session.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    # --- Query methods ---

    def get_by_id(self, taxon_id: int, enrich: bool = True) -> AnimalInfo | None:
        """
        Get animal by GBIF taxon ID.

        Args:
            taxon_id: GBIF taxon key
            enrich: Whether to fetch additional data from external APIs
        """
        taxon_model = self.session.get(TaxonModel, taxon_id)
        if not taxon_model:
            return None

        taxon = self._model_to_taxon(taxon_model)
        animal = AnimalInfo(taxon=taxon, is_enriched=taxon_model.is_enriched)

        if enrich:
            self._enrich(animal, taxon_model)

        return animal

    def get_by_name(
        self, scientific_name: str, enrich: bool = True
    ) -> AnimalInfo | None:
        """
        Get animal by scientific name.

        Args:
            scientific_name: Scientific name (e.g., "Canis lupus")
            enrich: Whether to fetch additional data from external APIs
        """
        taxon_model = (
            self.session.query(TaxonModel)
            .filter(
                or_(
                    TaxonModel.scientific_name == scientific_name,
                    TaxonModel.canonical_name == scientific_name,
                )
            )
            .first()
        )

        if not taxon_model:
            return None

        taxon = self._model_to_taxon(taxon_model)
        animal = AnimalInfo(taxon=taxon, is_enriched=taxon_model.is_enriched)

        if enrich:
            self._enrich(animal, taxon_model)

        return animal

    def search(self, query: str, limit: int = 20) -> list[AnimalInfo]:
        """
        Search for animals by name (scientific or vernacular) using FTS5.

        Uses SQLite FTS5 for fast full-text search. Falls back to LIKE queries
        if the FTS table hasn't been initialized yet.

        Args:
            query: Search query
            limit: Maximum number of results
        """
        # Try FTS5 first (fast full-text search)
        try:
            # FTS5 MATCH query - supports prefixes and relevance ranking
            fts_results = self.session.execute(
                text("""
                    SELECT taxon_id
                    FROM taxa_fts
                    WHERE taxa_fts MATCH :query
                    ORDER BY rank
                    LIMIT :limit
                """),
                {"query": query, "limit": limit},
            ).fetchall()

            if fts_results:
                # Get taxa by IDs preserving FTS5 ranking order
                taxon_ids = [row[0] for row in fts_results]
                taxon_models = (
                    self.session.query(TaxonModel)
                    .filter(TaxonModel.taxon_id.in_(taxon_ids))
                    .all()
                )

                # Preserve FTS5 ranking order
                id_to_model = {m.taxon_id: m for m in taxon_models}
                results = []
                for taxon_id in taxon_ids:
                    if taxon_id in id_to_model:
                        taxon = self._model_to_taxon(id_to_model[taxon_id])
                        results.append(AnimalInfo(taxon=taxon))

                return results

        except Exception:
            # FTS table doesn't exist - fall back to old method
            # Silently fallback (avoid spamming user on every search)
            pass

        # Fallback: slower LIKE-based search
        query_lower = query.lower()

        # Search in canonical names
        taxon_matches = (
            self.session.query(TaxonModel)
            .filter(func.lower(TaxonModel.canonical_name).contains(query_lower))
            .limit(limit)
            .all()
        )

        # Search in vernacular names
        vernacular_matches = (
            self.session.query(TaxonModel)
            .join(VernacularNameModel)
            .filter(func.lower(VernacularNameModel.name).contains(query_lower))
            .limit(limit)
            .all()
        )

        # Combine and deduplicate
        seen_ids = set()
        results = []

        for taxon_model in taxon_matches + vernacular_matches:
            if taxon_model.taxon_id not in seen_ids:
                seen_ids.add(taxon_model.taxon_id)
                taxon = self._model_to_taxon(taxon_model)
                results.append(AnimalInfo(taxon=taxon))

            if len(results) >= limit:
                break

        return results

    def get_random(
        self, rank: str = "species", prefer_unenriched: bool = True, enrich: bool = True
    ) -> AnimalInfo | None:
        """
        Get a random animal using fast ID-based selection.

        This method is optimized for large datasets by selecting a random ID
        in the valid range instead of using ORDER BY RANDOM(), which is slow.

        Args:
            rank: Taxonomic rank to filter by (default: species)
            prefer_unenriched: Prefer animals not yet enriched (for "animal of the day")
            enrich: Whether to fetch additional data
        """
        import random

        if prefer_unenriched:
            # First try to get an unenriched animal
            taxon_model = self._get_random_by_id_range(
                rank=rank, is_enriched=False
            )

            if not taxon_model:
                # Fall back to any animal
                taxon_model = self._get_random_by_id_range(rank=rank)
        else:
            taxon_model = self._get_random_by_id_range(rank=rank)

        if not taxon_model:
            return None

        taxon = self._model_to_taxon(taxon_model)
        animal = AnimalInfo(taxon=taxon)

        if enrich:
            self._enrich(animal, taxon_model)

        return animal

    def _get_random_by_id_range(
        self, rank: str, is_enriched: bool | None = None
    ) -> TaxonModel | None:
        """
        Fast random selection by ID range.

        Instead of ORDER BY RANDOM() (which is O(n)), this method:
        1. Gets min/max taxon_id from entire table (fast - uses PK index)
        2. Generates random ID in that range
        3. Finds first taxon matching filters with id >= random_id

        This avoids slow MIN/MAX on filtered columns without index.

        Args:
            rank: Taxonomic rank to filter
            is_enriched: Optional filter by enrichment status
        """
        import random

        # Build base query with filters
        query = self.session.query(TaxonModel).filter(TaxonModel.rank == rank)

        if is_enriched is not None:
            query = query.filter(TaxonModel.is_enriched.is_(is_enriched))

        # Get ID range from entire table (fast - uses primary key index)
        # Don't filter by rank/is_enriched here to avoid full table scan
        id_range = self.session.query(
            func.min(TaxonModel.taxon_id),
            func.max(TaxonModel.taxon_id)
        ).first()

        min_id, max_id = id_range

        if min_id is None or max_id is None:
            return None

        # Generate random ID in range and find closest match with filters
        # Try up to 20 times to find a valid taxon (handles gaps and filtering)
        for _ in range(20):
            random_id = random.randint(min_id, max_id)

            taxon_model = query.filter(
                TaxonModel.taxon_id >= random_id
            ).first()

            if taxon_model:
                return taxon_model

        # Fallback: just get the first one matching filters
        return query.first()

    def get_animal_of_the_day(self, date: datetime | None = None) -> AnimalInfo | None:
        """
        Get a consistent "animal of the day" based on the date.

        Uses the date as a seed for deterministic selection using ID-based approach,
        so the same date always returns the same animal. This is optimized for
        large datasets by avoiding COUNT(), OFFSET, and filtered MIN/MAX operations.

        Args:
            date: Date to use for selection (default: today)
        """
        import random

        if date is None:
            date = datetime.now()

        # Use date as seed for consistent selection
        day_seed = date.year * 10000 + date.month * 100 + date.day

        # Get ID range from entire table (fast - uses primary key index)
        # Don't filter by rank/is_synonym here to avoid slow full table scan
        id_range = self.session.query(
            func.min(TaxonModel.taxon_id),
            func.max(TaxonModel.taxon_id)
        ).first()

        min_id, max_id = id_range

        if min_id is None or max_id is None:
            return None

        # Use date seed to generate deterministic random ID
        rng = random.Random(day_seed)
        target_id = rng.randint(min_id, max_id)

        # Find closest taxon with id >= target_id matching filters
        taxon_model = (
            self.session.query(TaxonModel)
            .filter(TaxonModel.rank == "species")
            .filter(TaxonModel.is_synonym.is_(False))
            .filter(TaxonModel.taxon_id >= target_id)
            .first()
        )

        # If no taxon found (target_id was beyond last valid ID), wrap around
        if not taxon_model:
            taxon_model = (
                self.session.query(TaxonModel)
                .filter(TaxonModel.rank == "species")
                .filter(TaxonModel.is_synonym.is_(False))
                .order_by(TaxonModel.taxon_id)
                .first()
            )

        if not taxon_model:
            return None

        taxon = self._model_to_taxon(taxon_model)
        animal = AnimalInfo(taxon=taxon)
        self._enrich(animal, taxon_model)

        return animal

    # --- Enrichment methods ---

    def _enrich(self, animal: AnimalInfo, taxon_model: TaxonModel) -> None:
        """
        Enrich animal with data from external APIs (parallelized).

        This method fetches missing data from Wikidata, Wikipedia, and Wikimedia Commons.
        To optimize performance:
        - Wikidata and Wikipedia are fetched in parallel (independent calls)
        - Images are fetched after (may depend on Wikidata results)
        - All results are cached in the database for future use

        Args:
            animal: AnimalInfo object to enrich (modified in place)
            taxon_model: Database model with taxon information
        """
        scientific_name = animal.taxon.canonical_name or animal.taxon.scientific_name

        # Try to load from cache first
        animal.wikidata = self._get_cached_wikidata(taxon_model.taxon_id)
        animal.wikipedia = self._get_cached_wikipedia(taxon_model.taxon_id)
        animal.images = self._get_cached_images(taxon_model.taxon_id)

        # Determine what needs to be fetched
        needs_wikidata = animal.wikidata is None
        needs_wikipedia = animal.wikipedia is None
        needs_images = not animal.images

        # Fetch missing data in parallel
        if needs_wikidata or needs_wikipedia:
            with ThreadPoolExecutor(max_workers=2) as executor:
                futures = {}

                # Submit Wikidata and Wikipedia in parallel (they're independent)
                if needs_wikidata:
                    futures['wikidata'] = executor.submit(
                        self._fetch_and_cache_wikidata,
                        taxon_model.taxon_id,
                        scientific_name
                    )

                if needs_wikipedia:
                    futures['wikipedia'] = executor.submit(
                        self._fetch_and_cache_wikipedia,
                        taxon_model.taxon_id,
                        scientific_name
                    )

                # Wait for completion and assign results
                for key, future in futures.items():
                    try:
                        result = future.result()
                        if key == 'wikidata':
                            animal.wikidata = result
                        elif key == 'wikipedia':
                            animal.wikipedia = result
                    except Exception as e:
                        logger.error(f"Error fetching {key} for taxon {taxon_model.taxon_id}: {e}", exc_info=True)

        # Fetch images (depends on wikidata, so must be after)
        if needs_images:
            animal.images = self._fetch_and_cache_images(
                taxon_model.taxon_id, scientific_name, animal.wikidata
            )

        # Mark as enriched
        if not taxon_model.is_enriched:
            taxon_model.is_enriched = True
            taxon_model.enriched_at = datetime.now(UTC)
            self.session.commit()

        animal.is_enriched = True

    def _get_cached_wikidata(self, taxon_id: int) -> WikidataEntity | None:
        """Load cached Wikidata from database."""
        cache = (
            self.session.query(EnrichmentCacheModel)
            .filter(
                EnrichmentCacheModel.taxon_id == taxon_id,
                EnrichmentCacheModel.source == "wikidata",
            )
            .first()
        )

        if cache:
            data = json.loads(cache.data)
            return WikidataEntity(**data)

        return None

    def _get_cached_wikipedia(self, taxon_id: int) -> WikipediaArticle | None:
        """Load cached Wikipedia from database."""
        cache = (
            self.session.query(EnrichmentCacheModel)
            .filter(
                EnrichmentCacheModel.taxon_id == taxon_id,
                EnrichmentCacheModel.source == "wikipedia",
            )
            .first()
        )

        if cache:
            data = json.loads(cache.data)
            return WikipediaArticle(**data)

        return None

    def _get_cached_images(self, taxon_id: int) -> list[CommonsImage]:
        """Load cached images from database."""
        cache = (
            self.session.query(EnrichmentCacheModel)
            .filter(
                EnrichmentCacheModel.taxon_id == taxon_id,
                EnrichmentCacheModel.source == "commons",
            )
            .first()
        )

        if cache:
            data = json.loads(cache.data)
            return [CommonsImage(**img) for img in data]

        return []

    def _fetch_and_cache_wikidata(
        self, taxon_id: int, scientific_name: str
    ) -> WikidataEntity | None:
        """Fetch Wikidata and cache it."""
        try:
            entity = self.wikidata.get_by_taxonomy(scientific_name)
            if entity:
                self._save_cache(taxon_id, "wikidata", entity)
            return entity
        except Exception as e:
            print(f"Error fetching Wikidata for {scientific_name}: {e}")
            return None

    def _fetch_and_cache_wikipedia(
        self, taxon_id: int, scientific_name: str
    ) -> WikipediaArticle | None:
        """Fetch Wikipedia and cache it."""
        try:
            article = self.wikipedia.get_by_taxonomy(scientific_name)
            if article:
                self._save_cache(taxon_id, "wikipedia", article)
            return article
        except Exception as e:
            print(f"Error fetching Wikipedia for {scientific_name}: {e}")
            return None

    def _fetch_and_cache_images(
        self, taxon_id: int, scientific_name: str, wikidata: WikidataEntity | None
    ) -> list[CommonsImage]:
        """Fetch Commons images and cache them."""
        try:
            images = []

            # Try Wikidata-linked images first
            if wikidata and wikidata.qid:
                images = self.commons.get_images_for_wikidata(wikidata.qid, limit=5)

            # Fall back to category/search
            if not images:
                images = self.commons.get_by_taxonomy(scientific_name, limit=5)

            if images:
                self._save_cache(taxon_id, "commons", images)

            return images
        except Exception as e:
            print(f"Error fetching Commons images for {scientific_name}: {e}")
            return []

    def _save_cache(self, taxon_id: int, source: str, data) -> None:
        """Save data to enrichment cache."""
        # Serialize data
        if isinstance(data, list):
            json_data = json.dumps([self._to_dict(item) for item in data])
        else:
            json_data = json.dumps(self._to_dict(data))

        # Check for existing cache
        existing = (
            self.session.query(EnrichmentCacheModel)
            .filter(
                EnrichmentCacheModel.taxon_id == taxon_id,
                EnrichmentCacheModel.source == source,
            )
            .first()
        )

        if existing:
            existing.data = json_data
            existing.fetched_at = datetime.now(UTC)
        else:
            cache = EnrichmentCacheModel(
                taxon_id=taxon_id,
                source=source,
                data=json_data,
                fetched_at=datetime.now(UTC),
            )
            self.session.add(cache)

        self.session.commit()

    def _to_dict(self, obj) -> dict:
        """Convert dataclass to dict, handling enums."""
        from dataclasses import asdict, is_dataclass

        if is_dataclass(obj):
            result = {}
            for key, value in asdict(obj).items():
                if hasattr(value, "value"):  # Enum
                    result[key] = value.value
                else:
                    result[key] = value
            return result
        return obj

    def _model_to_taxon(self, model: TaxonModel) -> Taxon:
        """Convert TaxonModel to Taxon schema."""
        # Get vernacular names grouped by language
        vernacular_names: dict[str, list[str]] = {}
        for vn in model.vernacular_names:
            lang = vn.language or "unknown"
            if lang not in vernacular_names:
                vernacular_names[lang] = []
            vernacular_names[lang].append(vn.name)

        return Taxon(
            taxon_id=model.taxon_id,
            scientific_name=model.scientific_name,
            canonical_name=model.canonical_name,
            rank=TaxonomicRank(model.rank) if model.rank else None,
            kingdom=model.kingdom,
            phylum=model.phylum,
            class_=model.class_,
            order=model.order,
            family=model.family,
            genus=model.genus,
            parent_id=model.parent_id,
            accepted_id=model.accepted_id,
            vernacular_names=vernacular_names,
        )

    # --- Statistics ---

    def get_stats(self) -> dict:
        """Get database statistics."""
        total = self.session.query(TaxonModel).count()
        species = (
            self.session.query(TaxonModel).filter(TaxonModel.rank == "species").count()
        )
        enriched = (
            self.session.query(TaxonModel)
            .filter(TaxonModel.is_enriched.is_(True))
            .count()
        )
        vernacular = self.session.query(VernacularNameModel).count()

        return {
            "total_taxa": total,
            "species_count": species,
            "enriched_count": enriched,
            "vernacular_names": vernacular,
            "enrichment_progress": f"{enriched}/{species} ({100 * enriched / species:.1f}%)"
            if species
            else "N/A",
        }

    # --- History ---

    def add_to_history(
        self, taxon_id: int, command: str | None = None
    ) -> AnimalHistoryModel:
        """
        Add an animal view to the history.

        Args:
            taxon_id: GBIF taxon key
            command: Command used to view the animal ('today', 'random', 'info', 'search')

        Returns:
            The created history entry
        """
        entry = AnimalHistoryModel(
            taxon_id=taxon_id, viewed_at=datetime.now(UTC), command=command
        )
        self.session.add(entry)
        self.session.commit()
        return entry

    def get_history(
        self, page: int = 1, per_page: int = 10
    ) -> tuple[list[AnimalInfo], int]:
        """
        Get history of viewed animals with pagination.

        Args:
            page: Page number (1-indexed)
            per_page: Number of entries per page

        Returns:
            Tuple of (list of AnimalInfo objects, total count)
        """
        # Get total count
        total = self.session.query(AnimalHistoryModel).count()

        # Get paginated results
        offset = (page - 1) * per_page
        history_entries = (
            self.session.query(AnimalHistoryModel)
            .order_by(AnimalHistoryModel.viewed_at.desc())
            .offset(offset)
            .limit(per_page)
            .all()
        )

        # Convert to AnimalInfo objects
        results = []
        for entry in history_entries:
            taxon = self._model_to_taxon(entry.taxon)
            animal = AnimalInfo(taxon=taxon)
            # Attach history metadata
            animal.viewed_at = entry.viewed_at
            animal.command = entry.command
            results.append(animal)

        return results, total

    def get_history_count(self) -> int:
        """Get total number of history entries."""
        return self.session.query(AnimalHistoryModel).count()

    def clear_history(self) -> int:
        """
        Clear all history entries.

        Returns:
            Number of entries deleted
        """
        count = self.session.query(AnimalHistoryModel).count()
        self.session.query(AnimalHistoryModel).delete()
        self.session.commit()
        return count

    # --- Settings ---

    def get_setting(self, key: str, default: str | None = None) -> str | None:
        """
        Get a user setting by key.

        Args:
            key: Setting key
            default: Default value if setting doesn't exist

        Returns:
            Setting value or default
        """
        from daynimal.db.models import UserSettingsModel

        setting = self.session.query(UserSettingsModel).filter(
            UserSettingsModel.key == key
        ).first()

        return setting.value if setting else default

    def set_setting(self, key: str, value: str) -> None:
        """
        Set a user setting.

        Args:
            key: Setting key
            value: Setting value (will be converted to string)
        """
        from daynimal.db.models import UserSettingsModel

        setting = self.session.query(UserSettingsModel).filter(
            UserSettingsModel.key == key
        ).first()

        if setting:
            setting.value = str(value)
        else:
            setting = UserSettingsModel(key=key, value=str(value))
            self.session.add(setting)

        self.session.commit()
