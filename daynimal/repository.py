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
import threading
import unicodedata
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, UTC

import httpx
from sqlalchemy import func, or_, text
from sqlalchemy.orm import Session, joinedload

from daynimal.db.models import (
    TaxonModel,
    VernacularNameModel,
    EnrichmentCacheModel,
    AnimalHistoryModel,
    FavoriteModel,
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
from daynimal.connectivity import ConnectivityService
from daynimal.image_cache import ImageCacheService
from daynimal.sources.wikidata import WikidataAPI
from daynimal.sources.wikipedia import WikipediaAPI
from daynimal.sources.commons import CommonsAPI
from daynimal.sources.gbif_media import GbifMediaAPI
from daynimal.sources.phylopic_local import (
    get_silhouette_for_taxon as get_phylopic_silhouette,
)

# Logger for this module
logger = logging.getLogger(__name__)


def remove_accents(text: str) -> str:
    """
    Remove accents from text for better search matching.

    Examples:
        guépard -> guepard
        café -> cafe
    """
    nfd = unicodedata.normalize("NFD", text)
    return "".join(char for char in nfd if unicodedata.category(char) != "Mn")


class AnimalRepository:
    """
    Repository for accessing animal information.

    Combines local taxonomy data (from GBIF dump) with
    on-demand enrichment from external APIs.
    """

    def __init__(self, session: Session | None = None):
        self.session = session or get_session()
        self._session_lock = threading.Lock()
        self._wikidata: WikidataAPI | None = None
        self._wikipedia: WikipediaAPI | None = None
        self._commons: CommonsAPI | None = None
        self._gbif_media: GbifMediaAPI | None = None
        self.connectivity = ConnectivityService()
        self.image_cache = ImageCacheService(session=self.session)

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

    @property
    def gbif_media(self) -> GbifMediaAPI:
        if self._gbif_media is None:
            self._gbif_media = GbifMediaAPI()
        return self._gbif_media

    def close(self):
        """Close all connections."""
        if self._wikidata:
            self._wikidata.close()
        if self._wikipedia:
            self._wikipedia.close()
        if self._commons:
            self._commons.close()
        if self._gbif_media:
            self._gbif_media.close()
        self.image_cache.close()
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

        Uses SQLite FTS5 for fast full-text search with relevance ranking.
        Results are scored by: exact vernacular name match, BM25 text
        relevance, vernacular name count (popularity proxy), and species
        rank priority. Falls back to LIKE queries if FTS is unavailable.

        Args:
            query: Search query
            limit: Maximum number of results
        """
        # Try FTS5 first (fast full-text search)
        try:
            results = self._search_fts5(query, limit)
            if results is not None:
                return results
        except Exception:
            # FTS table doesn't exist - fall back to old method
            pass

        # Fallback: slower LIKE-based search
        return self._search_like(query, limit)

    def _search_fts5(self, query: str, limit: int) -> list[AnimalInfo] | None:
        """Search using FTS5 with relevance ranking.

        Returns None if no results found (to allow fallback to wildcard
        or normalized queries). Returns empty list if search was
        performed but yielded no matches after filtering.
        """
        # Try with original query first, then with normalized (no accents)
        queries_to_try = [query]
        normalized = remove_accents(query)
        if normalized != query:
            queries_to_try.append(normalized)

        # Fetch a larger candidate set for re-ranking.
        # Must be large enough to capture high-relevance results that BM25
        # ranks low (e.g. "eagle" exact match at FTS5 position 102 of 237).
        fetch_limit = max(limit * 10, 300)

        for search_query in queries_to_try:
            for use_wildcard in [False, True]:
                fts_query = f"{search_query}*" if use_wildcard else search_query

                fts_results = self.session.execute(
                    text("""
                        SELECT taxon_id
                        FROM taxa_fts
                        WHERE taxa_fts MATCH :query
                        ORDER BY rank
                        LIMIT :limit
                    """),
                    {"query": fts_query, "limit": fetch_limit},
                ).fetchall()

                if not fts_results:
                    continue

                taxon_ids = [row[0] for row in fts_results]
                taxon_models = (
                    self.session.query(TaxonModel)
                    .options(joinedload(TaxonModel.vernacular_names))
                    .filter(TaxonModel.taxon_id.in_(taxon_ids))
                    .all()
                )
                id_to_model = {m.taxon_id: m for m in taxon_models}

                # Filter and score results
                scored = []
                search_lower = search_query.lower()

                for taxon_id in taxon_ids:
                    model = id_to_model.get(taxon_id)
                    if not model:
                        continue

                    score = self._relevance_score(model, search_lower)
                    if score is None:
                        continue  # name doesn't match at all

                    scored.append((score, model))

                if not scored:
                    if not use_wildcard:
                        continue  # try wildcard
                    continue  # try next query variant

                # Sort by score descending (higher = more relevant)
                scored.sort(key=lambda x: x[0], reverse=True)

                # For short queries, only return species to avoid
                # genus/family noise (e.g. "lion" → species, not genus)
                if len(query) < 7:
                    scored = [
                        (s, m)
                        for s, m in scored
                        if m.rank == TaxonomicRank.SPECIES.value
                    ]
                    if not scored:
                        return []

                results = []
                for _score, model in scored[:limit]:
                    taxon = self._model_to_taxon(model)
                    results.append(AnimalInfo(taxon=taxon))

                return results

        return None

    @staticmethod
    def _relevance_score(model: "TaxonModel", query_lower: str) -> float | None:
        """Compute a relevance score for a taxon model against a query.

        Returns None if the query doesn't match the taxon at all.
        Higher score = more relevant.

        Scoring factors (fixed weights, additive):
        - Exact vernacular name match: +200 per match
          (name IS the query, e.g. "Tiger" == "tiger")
        - Prefix vernacular name match: +150 per match
          (name starts with query word, e.g. "Aigle royal")
        - Canonical name contains query: +80
        - Species rank: +30
        - Popularity (vernacular name count): +min(vn_count, 250)
        """
        score = 0.0
        matched = False
        exact_vn_count = 0
        prefix_vn_count = 0
        query_prefix = query_lower + " "
        query_prefix_hyphen = query_lower + "-"

        # Check canonical name match (NOT scientific_name which includes
        # author names like "Nielsen & Eagle, 1974" — false positives)
        canonical = (model.canonical_name or "").lower()
        has_canonical_match = query_lower in canonical

        if has_canonical_match:
            matched = True

        # Check vernacular names
        vn_count = 0
        if model.vernacular_names:
            vn_count = len(model.vernacular_names)
            for vn in model.vernacular_names:
                if not vn.name:
                    continue
                vn_lower = vn.name.lower()
                if vn_lower == query_lower:
                    exact_vn_count += 1
                    matched = True
                elif vn_lower.startswith(query_prefix) or vn_lower.startswith(
                    query_prefix_hyphen
                ):
                    prefix_vn_count += 1
                    matched = True
                elif query_lower in vn_lower:
                    matched = True

        if not matched:
            return None

        # Build score with fixed weights (no multiplicative interaction).
        # Prefix matches are capped to prevent species with many
        # translations of a compound name (e.g. "Tiger Moray" in 17
        # languages) from outranking the actual animal (Tiger, 10 exact).
        score += exact_vn_count * 200
        score += min(prefix_vn_count, 8) * 150
        if has_canonical_match:
            score += 80
        if model.rank == TaxonomicRank.SPECIES.value:
            score += 30
        score += min(vn_count, 250)  # popularity proxy (capped)

        return score

    def _search_like(self, query: str, limit: int) -> list[AnimalInfo]:
        """Fallback LIKE-based search when FTS5 is unavailable."""
        query_lower = query.lower()

        taxon_matches = (
            self.session.query(TaxonModel)
            .filter(func.lower(TaxonModel.canonical_name).contains(query_lower))
            .limit(limit)
            .all()
        )

        vernacular_matches = (
            self.session.query(TaxonModel)
            .join(VernacularNameModel)
            .filter(func.lower(VernacularNameModel.name).contains(query_lower))
            .limit(limit)
            .all()
        )

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

        if prefer_unenriched:
            # First try to get an unenriched animal
            taxon_model = self._get_random_by_id_range(rank=rank, is_enriched=False)

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
            func.min(TaxonModel.taxon_id), func.max(TaxonModel.taxon_id)
        ).first()

        min_id, max_id = id_range

        if min_id is None or max_id is None:
            return None

        # Generate random ID in range and find closest match with filters
        # Try up to 20 times to find a valid taxon (handles gaps and filtering)
        for _ in range(20):
            random_id = random.randint(min_id, max_id)

            taxon_model = query.filter(TaxonModel.taxon_id >= random_id).first()

            if taxon_model:
                return taxon_model

        # Fallback: just get the first one matching filters
        return query.first()

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

        # Skip network enrichment if offline
        if not self.connectivity.is_online:
            logger.info(f"Offline: skipping API enrichment for {scientific_name}")
            # Still load cached data
            animal.wikidata = self._get_cached_wikidata(taxon_model.taxon_id)
            animal.wikipedia = self._get_cached_wikipedia(taxon_model.taxon_id)
            animal.images = self._get_cached_images(taxon_model.taxon_id)
            animal.is_enriched = taxon_model.is_enriched
            return

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
                    futures["wikidata"] = executor.submit(
                        self._fetch_and_cache_wikidata,
                        taxon_model.taxon_id,
                        scientific_name,
                    )

                if needs_wikipedia:
                    futures["wikipedia"] = executor.submit(
                        self._fetch_and_cache_wikipedia,
                        taxon_model.taxon_id,
                        scientific_name,
                    )

                # Wait for completion and assign results
                for key, future in futures.items():
                    try:
                        result = future.result()
                        if key == "wikidata":
                            animal.wikidata = result
                        elif key == "wikipedia":
                            animal.wikipedia = result
                    except Exception as e:
                        logger.error(
                            f"Error fetching {key} for taxon {taxon_model.taxon_id}: {e}",
                            exc_info=True,
                        )

        # Fetch images (depends on wikidata, so must be after)
        if needs_images:
            animal.images = self._fetch_and_cache_images(
                taxon_model.taxon_id, scientific_name, animal.wikidata, animal.taxon
            )

        # Mark as enriched
        if not taxon_model.is_enriched:
            with self._session_lock:
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
        except httpx.RequestError:
            self.connectivity.set_offline()
            logger.warning(f"Network error fetching Wikidata for {scientific_name}")
            return None
        except Exception as e:
            logger.warning(f"Error fetching Wikidata for {scientific_name}: {e}")
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
        except httpx.RequestError:
            self.connectivity.set_offline()
            logger.warning(f"Network error fetching Wikipedia for {scientific_name}")
            return None
        except Exception as e:
            logger.warning(f"Error fetching Wikipedia for {scientific_name}: {e}")
            return None

    def _fetch_and_cache_images(
        self,
        taxon_id: int,
        scientific_name: str,
        wikidata: WikidataEntity | None,
        taxon: Taxon | None = None,
    ) -> list[CommonsImage]:
        """Fetch images with cascade: Commons → GBIF Media → PhyloPic (local)."""
        try:
            images = []
            p18_filename = wikidata.image_filename if wikidata else None
            p18_image = None

            # Fetch P18 image details from Commons
            if p18_filename:
                try:
                    p18_image = self.commons.get_by_source_id(p18_filename)
                except Exception as e:
                    logger.warning(
                        f"Error fetching P18 image for {scientific_name}: {e}"
                    )

            # 1. Try Wikidata-linked images first (Wikimedia Commons)
            if wikidata and wikidata.qid:
                images = self.commons.get_images_for_wikidata(wikidata.qid, limit=5)

            # 2. Fall back to Commons category/search
            if not images:
                images = self.commons.get_by_taxonomy(scientific_name, limit=5)

            # 3. Fall back to GBIF Media API
            if not images:
                try:
                    images = self.gbif_media.get_media_for_taxon(taxon_id, limit=5)
                except Exception as e:
                    logger.warning(
                        f"Error fetching GBIF Media for {scientific_name}: {e}"
                    )

            # 4. Last resort: PhyloPic silhouettes (local CSV lookup)
            if not images and taxon:
                try:
                    silhouette = get_phylopic_silhouette(taxon)
                    if silhouette:
                        images = [silhouette]
                except Exception as e:
                    logger.warning(
                        f"Error looking up PhyloPic for {scientific_name}: {e}"
                    )

            # Insert P18 if not already in the list
            if p18_image:
                existing_filenames = {img.filename for img in images}
                if p18_image.filename not in existing_filenames:
                    images.append(p18_image)

            # Rank images
            if images:
                from daynimal.sources.commons import rank_images

                images = rank_images(images, p18_filename=p18_filename)

            if images:
                self._save_cache(taxon_id, "commons", images)
                try:
                    self.image_cache.cache_single_image(images[0])
                except Exception as e:
                    logger.warning(f"Error caching images locally: {e}")

            return images
        except httpx.RequestError:
            self.connectivity.set_offline()
            logger.warning(f"Network error fetching images for {scientific_name}")
            return []
        except Exception as e:
            logger.warning(f"Error fetching images for {scientific_name}: {e}")
            return []

    def _save_cache(self, taxon_id: int, source: str, data) -> None:
        """Save data to enrichment cache.

        Thread-safe: uses a lock to prevent concurrent session access
        from parallel API fetch threads.
        """
        # Serialize data (no session access, safe outside lock)
        if isinstance(data, list):
            json_data = json.dumps([self._to_dict(item) for item in data])
        else:
            json_data = json.dumps(self._to_dict(data))

        with self._session_lock:
            try:
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
            except Exception:
                self.session.rollback()
                raise

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

        # Try to convert rank to enum, fallback to None for invalid ranks
        rank = None
        if model.rank:
            try:
                rank = TaxonomicRank(model.rank)
            except ValueError:
                # Rank not in enum (e.g., "unranked", "variety", "form")
                # Keep as None
                pass

        return Taxon(
            taxon_id=model.taxon_id,
            scientific_name=model.scientific_name,
            canonical_name=model.canonical_name,
            rank=rank,
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

        # Get paginated results with eager loading of taxon
        offset = (page - 1) * per_page
        history_entries = (
            self.session.query(AnimalHistoryModel)
            .options(joinedload(AnimalHistoryModel.taxon))
            .order_by(AnimalHistoryModel.viewed_at.desc())
            .offset(offset)
            .limit(per_page)
            .all()
        )

        # Convert to AnimalInfo objects
        results = []
        for entry in history_entries:
            # Skip entries with missing taxon (deleted from database)
            if not entry.taxon:
                continue

            try:
                taxon = self._model_to_taxon(entry.taxon)
                animal = AnimalInfo(taxon=taxon)
                # Attach history metadata
                animal.viewed_at = entry.viewed_at
                animal.command = entry.command
                animal.history_id = entry.id
                results.append(animal)
            except Exception as e:
                # Log and skip corrupted entries
                logger.warning(f"Skipping corrupted history entry {entry.id}: {e}")
                continue

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

    def remove_from_history(self, history_id: int) -> bool:
        """
        Remove a single entry from the history.

        Args:
            history_id: ID of the history entry to remove

        Returns:
            True if removed, False if not found
        """
        entry = self.session.get(AnimalHistoryModel, history_id)

        if not entry:
            return False

        self.session.delete(entry)
        self.session.commit()
        return True

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

        setting = (
            self.session.query(UserSettingsModel)
            .filter(UserSettingsModel.key == key)
            .first()
        )

        return setting.value if setting else default

    def set_setting(self, key: str, value: str) -> None:
        """
        Set a user setting.

        Args:
            key: Setting key
            value: Setting value (will be converted to string)
        """
        from daynimal.db.models import UserSettingsModel

        setting = (
            self.session.query(UserSettingsModel)
            .filter(UserSettingsModel.key == key)
            .first()
        )

        if setting:
            setting.value = str(value)
        else:
            setting = UserSettingsModel(key=key, value=str(value))
            self.session.add(setting)

        self.session.commit()

    # --- Favorites methods ---

    def add_favorite(self, taxon_id: int) -> bool:
        """
        Add an animal to favorites.

        Args:
            taxon_id: GBIF taxon ID

        Returns:
            True if added, False if already in favorites
        """
        # Check if already in favorites
        existing = (
            self.session.query(FavoriteModel)
            .filter(FavoriteModel.taxon_id == taxon_id)
            .first()
        )

        if existing:
            return False

        # Add to favorites
        favorite = FavoriteModel(taxon_id=taxon_id)
        self.session.add(favorite)
        self.session.commit()
        return True

    def remove_favorite(self, taxon_id: int) -> bool:
        """
        Remove an animal from favorites.

        Args:
            taxon_id: GBIF taxon ID

        Returns:
            True if removed, False if not in favorites
        """
        favorite = (
            self.session.query(FavoriteModel)
            .filter(FavoriteModel.taxon_id == taxon_id)
            .first()
        )

        if not favorite:
            return False

        self.session.delete(favorite)
        self.session.commit()
        return True

    def is_favorite(self, taxon_id: int) -> bool:
        """
        Check if an animal is in favorites.

        Args:
            taxon_id: GBIF taxon ID

        Returns:
            True if in favorites, False otherwise
        """
        return (
            self.session.query(FavoriteModel)
            .filter(FavoriteModel.taxon_id == taxon_id)
            .first()
        ) is not None

    def get_favorites(
        self, page: int = 1, per_page: int = 50
    ) -> tuple[list[AnimalInfo], int]:
        """
        Get paginated list of favorite animals.

        Args:
            page: Page number (1-indexed)
            per_page: Number of results per page

        Returns:
            Tuple of (list of AnimalInfo, total count)
        """
        # Get total count
        total = self.session.query(FavoriteModel).count()

        if total == 0:
            return ([], 0)

        # Get paginated favorites (ordered by most recently added)
        offset = (page - 1) * per_page
        favorites = (
            self.session.query(FavoriteModel)
            .order_by(FavoriteModel.added_at.desc())
            .offset(offset)
            .limit(per_page)
            .all()
        )

        # Convert to AnimalInfo
        animals = []
        for fav in favorites:
            taxon_model = fav.taxon
            taxon = self._model_to_taxon(taxon_model)
            animal = AnimalInfo(taxon=taxon)
            animals.append(animal)

        return (animals, total)

    def get_favorites_count(self) -> int:
        """
        Get total number of favorites.

        Returns:
            Total count of favorites
        """
        return self.session.query(FavoriteModel).count()
