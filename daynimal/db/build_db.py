"""
Build a SQLite database from distribution TSV files.

This script takes pre-generated TSV files (from generate_distribution.py) and
imports them into a new SQLite database with optimized settings.

Usage:
    # Build from minimal distribution
    uv run build-db --taxa data/animalia_taxa_minimal.tsv \\
                     --vernacular data/animalia_vernacular_minimal.tsv

    # Build with custom database name
    uv run build-db --taxa data/animalia_taxa.tsv \\
                     --vernacular data/animalia_vernacular.tsv \\
                     --db daynimal_full.db
"""

import csv
from pathlib import Path

from sqlalchemy import text

from daynimal.config import settings
from daynimal.db.models import Base
from daynimal.db.session import get_engine


def optimize_database_for_import(engine):
    """Configure SQLite for maximum import speed."""
    print("Optimizing database for bulk import...")
    with engine.begin() as conn:
        conn.execute(text("PRAGMA synchronous = OFF"))
        conn.execute(text("PRAGMA temp_store = MEMORY"))
        conn.execute(text("PRAGMA cache_size = -256000"))  # 256 MB cache
    print("Database optimized.")


def restore_database_settings(engine):
    """Restore normal database settings after import."""
    print("Restoring normal database settings...")
    with engine.begin() as conn:
        conn.execute(text("PRAGMA synchronous = FULL"))
    print("Settings restored.")


def bulk_import_taxa(engine, tsv_path: Path) -> int:
    """Import taxa from TSV file using optimized bulk insert."""
    print(f"Importing taxa from {tsv_path}...")

    count = 0
    batch = []
    batch_size = 5000

    with engine.begin() as conn:
        with open(tsv_path, "r", encoding="utf-8") as f:
            reader = csv.reader(f, delimiter="\t", quoting=csv.QUOTE_NONE)

            for row in reader:
                if len(row) != 13:
                    continue

                batch.append(
                    {
                        "taxon_id": int(row[0]),
                        "scientific_name": row[1],
                        "canonical_name": row[2] or None,
                        "rank": row[3] or None,
                        "kingdom": row[4],
                        "phylum": row[5] or None,
                        "class_": row[6] or None,
                        "order": row[7] or None,
                        "family": row[8] or None,
                        "genus": row[9] or None,
                        "parent_id": int(row[10]) if row[10] else None,
                        "accepted_id": int(row[11]) if row[11] else None,
                        "is_synonym": bool(int(row[12])),
                        "is_enriched": False,
                    }
                )

                if len(batch) >= batch_size:
                    conn.execute(
                        text("""
                            INSERT INTO taxa (taxon_id, scientific_name, canonical_name, rank,
                                             kingdom, phylum, class, "order", family, genus,
                                             parent_id, accepted_id, is_synonym, is_enriched)
                            VALUES (:taxon_id, :scientific_name, :canonical_name, :rank,
                                   :kingdom, :phylum, :class_, :order, :family, :genus,
                                   :parent_id, :accepted_id, :is_synonym, :is_enriched)
                        """),
                        batch,
                    )
                    count += len(batch)
                    print(f"\rImported: {count:,} taxa...", end="", flush=True)
                    batch = []

            if batch:
                conn.execute(
                    text("""
                        INSERT INTO taxa (taxon_id, scientific_name, canonical_name, rank,
                                         kingdom, phylum, class, "order", family, genus,
                                         parent_id, accepted_id, is_synonym, is_enriched)
                        VALUES (:taxon_id, :scientific_name, :canonical_name, :rank,
                               :kingdom, :phylum, :class_, :order, :family, :genus,
                               :parent_id, :accepted_id, :is_synonym, :is_enriched)
                    """),
                    batch,
                )
                count += len(batch)

    print(f"\nImport complete: {count:,} taxa imported.")
    return count


def bulk_import_vernacular(engine, tsv_path: Path) -> int:
    """Import vernacular names from TSV file using optimized bulk insert."""
    print(f"Importing vernacular names from {tsv_path}...")

    count = 0
    batch = []
    batch_size = 10000

    with engine.begin() as conn:
        with open(tsv_path, "r", encoding="utf-8") as f:
            reader = csv.reader(f, delimiter="\t", quoting=csv.QUOTE_NONE)

            for row in reader:
                if len(row) != 3:
                    continue

                batch.append(
                    {
                        "taxon_id": int(row[0]),
                        "name": row[1],
                        "language": row[2] or None,
                    }
                )

                if len(batch) >= batch_size:
                    conn.execute(
                        text("""
                            INSERT INTO vernacular_names (taxon_id, name, language)
                            VALUES (:taxon_id, :name, :language)
                        """),
                        batch,
                    )
                    count += len(batch)
                    print(f"\rImported: {count:,} names...", end="", flush=True)
                    batch = []

            if batch:
                conn.execute(
                    text("""
                        INSERT INTO vernacular_names (taxon_id, name, language)
                        VALUES (:taxon_id, :name, :language)
                    """),
                    batch,
                )
                count += len(batch)

    print(f"\nImport complete: {count:,} vernacular names imported.")
    return count


def build_database(taxa_tsv: Path, vernacular_tsv: Path, db_filename: str):
    """Build a SQLite database from distribution TSV files."""
    print("=" * 60)
    print("BUILD DATABASE FROM DISTRIBUTION TSV FILES")
    print("=" * 60)
    print(f"Taxa:       {taxa_tsv}")
    print(f"Vernacular: {vernacular_tsv}")
    print(f"Database:   {db_filename}")
    print("=" * 60)

    if not taxa_tsv.exists():
        raise FileNotFoundError(f"Taxa TSV not found: {taxa_tsv}")
    if not vernacular_tsv.exists():
        raise FileNotFoundError(f"Vernacular TSV not found: {vernacular_tsv}")

    # Override database URL
    original_db_url = settings.database_url
    settings.database_url = f"sqlite:///{db_filename}"

    try:
        # Step 1: Create DB + schema
        engine = get_engine()
        print("\nCreating database tables...")
        Base.metadata.create_all(engine)

        with engine.connect() as conn:
            result = conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='table'")
            )
            tables = [row[0] for row in result]
            print(f"Tables created: {tables}")
            if "taxa" not in tables:
                raise RuntimeError("Failed to create taxa table!")

        # Step 2: Optimize PRAGMA
        optimize_database_for_import(engine)

        # Step 3: Import taxa
        print("\n--- Import taxa ---")
        bulk_import_taxa(engine, taxa_tsv)

        # Step 4: Import vernacular
        print("\n--- Import vernacular names ---")
        bulk_import_vernacular(engine, vernacular_tsv)

        # Step 5: Restore PRAGMA
        restore_database_settings(engine)

        # Step 6: VACUUM
        print("\nCompacting database (VACUUM)...")
        with engine.connect() as conn:
            conn.execute(text("VACUUM"))
            conn.commit()
        print("Database compacted.")

        # Step 7: Statistics
        with engine.connect() as conn:
            total_taxa = conn.execute(text("SELECT COUNT(*) FROM taxa")).scalar()
            species_count = conn.execute(
                text("SELECT COUNT(*) FROM taxa WHERE rank = 'species'")
            ).scalar()
            vern_count = conn.execute(
                text("SELECT COUNT(*) FROM vernacular_names")
            ).scalar()
            fr_count = conn.execute(
                text("SELECT COUNT(*) FROM vernacular_names WHERE language = 'fr'")
            ).scalar()

        print("\n" + "=" * 60)
        print("DATABASE STATISTICS")
        print("=" * 60)
        print(f"Total taxa:       {total_taxa:,}")
        print(f"Species:          {species_count:,}")
        print(f"Vernacular names: {vern_count:,}")
        print(f"French names:     {fr_count:,}")

        db_path = Path(db_filename)
        if db_path.exists():
            db_size = db_path.stat().st_size / (1024 * 1024)
            print(f"Database size:    {db_size:.1f} MB")

        # Step 8: Remind about FTS
        print("\n" + "=" * 60)
        print("BUILD COMPLETE!")
        print("=" * 60)
        print("Next step: build the FTS5 search index:")
        print("  uv run init-fts")
        print("\nAttribution:")
        print("  GBIF Backbone Taxonomy. GBIF Secretariat (2024). CC-BY 4.0")
        print("  TAXREF v18 - MNHN & UMS PatriNat. Etalab Open License 2.0")

    finally:
        settings.database_url = original_db_url


def main():
    """Main entry point for build-db."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Build SQLite database from distribution TSV files"
    )
    parser.add_argument("--taxa", type=str, required=True, help="Path to taxa TSV file")
    parser.add_argument(
        "--vernacular",
        type=str,
        required=True,
        help="Path to vernacular names TSV file",
    )
    parser.add_argument(
        "--db",
        type=str,
        default="daynimal.db",
        help="Output database filename (default: daynimal.db)",
    )

    args = parser.parse_args()

    build_database(
        taxa_tsv=Path(args.taxa),
        vernacular_tsv=Path(args.vernacular),
        db_filename=args.db,
    )


if __name__ == "__main__":
    main()
