"""
Animal Repository - aggregates data from local DB and external APIs.

This is the main interface for retrieving enriched animal information.
It handles:
- Querying the local GBIF-based taxonomy database
- Fetching additional data from Wikidata, Wikipedia, Commons
- Caching enrichment data locally
"""

import json
from datetime import datetime

from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from daynimal.db.models import TaxonModel, VernacularNameModel, EnrichmentCacheModel
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
        Search for animals by name (scientific or vernacular).

        Args:
            query: Search query
            limit: Maximum number of results
        """
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
        Get a random animal.

        Args:
            rank: Taxonomic rank to filter by (default: species)
            prefer_unenriched: Prefer animals not yet enriched (for "animal of the day")
            enrich: Whether to fetch additional data
        """
        query = self.session.query(TaxonModel).filter(TaxonModel.rank == rank)

        if prefer_unenriched:
            # First try to get an unenriched animal
            unenriched = query.filter(TaxonModel.is_enriched.is_(False))
            taxon_model = unenriched.order_by(func.random()).first()

            if not taxon_model:
                # Fall back to any animal
                taxon_model = query.order_by(func.random()).first()
        else:
            taxon_model = query.order_by(func.random()).first()

        if not taxon_model:
            return None

        taxon = self._model_to_taxon(taxon_model)
        animal = AnimalInfo(taxon=taxon)

        if enrich:
            self._enrich(animal, taxon_model)

        return animal

    def get_animal_of_the_day(self, date: datetime | None = None) -> AnimalInfo | None:
        """
        Get a consistent "animal of the day" based on the date.

        Uses the date as a seed for deterministic random selection,
        so the same date always returns the same animal.

        Args:
            date: Date to use for selection (default: today)
        """
        if date is None:
            date = datetime.now()

        # Use date as seed for consistent selection
        day_seed = date.year * 10000 + date.month * 100 + date.day

        # Count species
        species_count = (
            self.session.query(TaxonModel)
            .filter(TaxonModel.rank == "species")
            .filter(TaxonModel.is_synonym.is_(False))
            .count()
        )

        if species_count == 0:
            return None

        # Select based on seed
        offset = day_seed % species_count

        taxon_model = (
            self.session.query(TaxonModel)
            .filter(TaxonModel.rank == "species")
            .filter(TaxonModel.is_synonym.is_(False))
            .offset(offset)
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
        """Enrich animal with data from external APIs."""
        scientific_name = animal.taxon.canonical_name or animal.taxon.scientific_name

        # Try to load from cache first
        animal.wikidata = self._get_cached_wikidata(taxon_model.taxon_id)
        animal.wikipedia = self._get_cached_wikipedia(taxon_model.taxon_id)
        animal.images = self._get_cached_images(taxon_model.taxon_id)

        # Fetch missing data from APIs
        if animal.wikidata is None:
            animal.wikidata = self._fetch_and_cache_wikidata(
                taxon_model.taxon_id, scientific_name
            )

        if animal.wikipedia is None:
            animal.wikipedia = self._fetch_and_cache_wikipedia(
                taxon_model.taxon_id, scientific_name
            )

        if not animal.images:
            animal.images = self._fetch_and_cache_images(
                taxon_model.taxon_id, scientific_name, animal.wikidata
            )

        # Mark as enriched
        if not taxon_model.is_enriched:
            taxon_model.is_enriched = True
            taxon_model.enriched_at = datetime.utcnow()
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
            existing.fetched_at = datetime.utcnow()
        else:
            cache = EnrichmentCacheModel(
                taxon_id=taxon_id,
                source=source,
                data=json_data,
                fetched_at=datetime.utcnow(),
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
