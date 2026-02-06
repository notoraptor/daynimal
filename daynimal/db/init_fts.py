"""
Initialize FTS5 (Full-Text Search) table for fast animal search.

FTS5 is a SQLite virtual table that provides efficient full-text search
capabilities. This module creates and populates the taxa_fts table.
"""

from sqlalchemy import text

from daynimal.db.session import get_session


def create_fts_table(session):
    """
    Create the FTS5 virtual table for taxa search.

    The table indexes:
    - scientific_name: Full scientific name
    - canonical_name: Canonical (simplified) name
    - vernacular_names: All common names concatenated with spaces
    - taxonomic_rank: Taxonomic rank (UNINDEXED, for reference only)
    - taxon_id: ID to link back to taxa table (UNINDEXED)
    """
    # Drop existing FTS table if it exists
    session.execute(text("DROP TABLE IF EXISTS taxa_fts"))

    # Create FTS5 virtual table
    session.execute(text("""
        CREATE VIRTUAL TABLE taxa_fts USING fts5(
            scientific_name,
            canonical_name,
            vernacular_names,
            taxonomic_rank UNINDEXED,
            taxon_id UNINDEXED
        )
    """))

    session.commit()
    print("[OK] Created FTS5 table: taxa_fts")


def populate_fts_table(session):
    """
    Populate the FTS5 table with data from taxa and vernacular_names tables.

    This aggregates all vernacular names for each taxon into a single
    space-separated string for efficient full-text search.
    """
    print("Populating FTS5 table...")

    # Insert data into FTS5 table
    # We concatenate all vernacular names into a single field for searching
    session.execute(text("""
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
    """))

    session.commit()

    # Get count
    result = session.execute(text("SELECT COUNT(*) FROM taxa_fts")).fetchone()
    count = result[0] if result else 0

    print(f"[OK] Populated FTS5 table with {count:,} taxa")


def init_fts():
    """Initialize FTS5 search: create and populate the table."""
    print("\n[Initializing FTS5 Full-Text Search]")
    print("-" * 50)

    with get_session() as session:
        create_fts_table(session)
        populate_fts_table(session)

    print("-" * 50)
    print("[OK] FTS5 initialization complete!")
    print("\nYou can now use fast full-text search with 'daynimal search'")


def rebuild_fts():
    """Rebuild the FTS5 table (useful after importing new taxa)."""
    print("\n[Rebuilding FTS5 Index]")
    print("-" * 50)

    with get_session() as session:
        # FTS5 rebuild command optimizes the index
        print("Optimizing FTS5 index...")
        session.execute(text("INSERT INTO taxa_fts(taxa_fts) VALUES('rebuild')"))
        session.commit()
        print("[OK] FTS5 index optimized")

    print("-" * 50)
    print("[OK] FTS5 rebuild complete!")


if __name__ == "__main__":
    init_fts()
