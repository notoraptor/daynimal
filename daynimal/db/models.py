from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def _utcnow():
    return datetime.now(UTC)


class Base(DeclarativeBase):
    pass


class TaxonModel(Base):
    """
    Core taxonomy table imported from GBIF Backbone.
    Only contains Animalia kingdom, filtered for commercial-use licenses.
    """

    __tablename__ = "taxa"

    # Primary key (GBIF taxon key)
    taxon_id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # Names
    scientific_name: Mapped[str] = mapped_column(String(255), nullable=False)
    canonical_name: Mapped[str | None] = mapped_column(String(255))

    # Taxonomic rank
    rank: Mapped[str | None] = mapped_column(String(50))

    # Classification hierarchy
    kingdom: Mapped[str | None] = mapped_column(String(100))
    phylum: Mapped[str | None] = mapped_column(String(100))
    class_: Mapped[str | None] = mapped_column("class", String(100))
    order: Mapped[str | None] = mapped_column(String(100))
    family: Mapped[str | None] = mapped_column(String(100))
    genus: Mapped[str | None] = mapped_column(String(100))

    # Hierarchy relationships
    parent_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("taxa.taxon_id"), index=True
    )
    accepted_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("taxa.taxon_id"), index=True
    )

    # Status
    is_synonym: Mapped[bool] = mapped_column(Boolean, default=False)

    # Enrichment tracking
    is_enriched: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    enriched_at: Mapped[datetime | None] = mapped_column(DateTime)

    # Relationships
    vernacular_names: Mapped[list["VernacularNameModel"]] = relationship(
        back_populates="taxon", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_taxa_canonical_name", "canonical_name"),
        Index("ix_taxa_rank", "rank"),
        Index("ix_taxa_family", "family"),
    )


class VernacularNameModel(Base):
    """Vernacular (common) names for taxa in different languages."""

    __tablename__ = "vernacular_names"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    taxon_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("taxa.taxon_id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    language: Mapped[str | None] = mapped_column(String(10))

    # Relationship
    taxon: Mapped["TaxonModel"] = relationship(back_populates="vernacular_names")

    __table_args__ = (
        Index("ix_vernacular_taxon_lang", "taxon_id", "language"),
        Index("ix_vernacular_name", "name"),
    )


class EnrichmentCacheModel(Base):
    """
    Cache for enrichment data from external APIs.
    Stores JSON responses to avoid repeated API calls.
    """

    __tablename__ = "enrichment_cache"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    taxon_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("taxa.taxon_id", ondelete="CASCADE"), nullable=False
    )

    # Source identification
    source: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # 'wikidata', 'wikipedia', 'commons'

    # Cached data (JSON)
    data: Mapped[str] = mapped_column(Text, nullable=False)

    # Metadata
    fetched_at: Mapped[datetime] = mapped_column(
        DateTime, default=_utcnow, nullable=False
    )
    license: Mapped[str | None] = mapped_column(String(50))

    __table_args__ = (
        Index("ix_cache_taxon_source", "taxon_id", "source", unique=True),
    )


class AnimalHistoryModel(Base):
    """
    History of viewed animals.

    Tracks each time an animal is displayed, with metadata about
    how it was viewed (command used).
    """

    __tablename__ = "animal_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    taxon_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("taxa.taxon_id", ondelete="CASCADE"), nullable=False
    )

    # When the animal was viewed
    viewed_at: Mapped[datetime] = mapped_column(
        DateTime, default=_utcnow, nullable=False
    )

    # Which command was used to view it
    command: Mapped[str | None] = mapped_column(
        String(50)
    )  # 'today', 'random', 'info', 'search'

    # Relationship to taxon
    taxon: Mapped["TaxonModel"] = relationship()

    __table_args__ = (
        Index("ix_history_viewed_at", "viewed_at"),
        Index("ix_history_taxon_id", "taxon_id"),
    )


class UserSettingsModel(Base):
    """
    User preferences and settings.
    Stores key-value pairs for app configuration.
    """

    __tablename__ = "user_settings"

    # Primary key
    key: Mapped[str] = mapped_column(String(100), primary_key=True)

    # Setting value (stored as string, parsed by app)
    value: Mapped[str] = mapped_column(Text, nullable=False)


class FavoriteModel(Base):
    """
    User's favorite animals.
    Stores references to taxa that the user has marked as favorites.
    """

    __tablename__ = "favorites"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    taxon_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("taxa.taxon_id", ondelete="CASCADE"), nullable=False
    )

    # When the favorite was added
    added_at: Mapped[datetime] = mapped_column(
        DateTime, default=_utcnow, nullable=False
    )

    # Relationship to taxon
    taxon: Mapped["TaxonModel"] = relationship()

    __table_args__ = (
        Index(
            "ix_favorites_taxon_id", "taxon_id", unique=True
        ),  # One favorite per taxon
        Index("ix_favorites_added_at", "added_at"),
    )
