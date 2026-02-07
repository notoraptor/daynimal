"""
GBIF Backbone Taxonomy Fast Importer.

This is a high-performance version of the GBIF importer that uses:
1. Pre-filtering to create clean TSV files
2. Mode-based filtering (full or minimal)
3. Optimized PRAGMA settings
4. Single large transaction

This approach is 10-100x faster than the incremental import.

Modes:
  - full: All Animalia kingdom taxa (~4.4M taxa, ~1.7 GB database)
  - minimal: Species with vernacular names only (~500k taxa, ~150 MB database)

Usage:
    # Full database (for development/desktop)
    uv run import-gbif-fast --mode full

    # Minimal database (for mobile apps)
    uv run import-gbif-fast --mode minimal

    # Save TSV files for distribution
    uv run import-gbif-fast --mode minimal --save-tsv
"""

import csv
import io
import zipfile
from pathlib import Path

from sqlalchemy import text

from daynimal.config import settings
from daynimal.db.import_gbif import (
    TAXON_COLUMNS,
    VERNACULAR_COLUMNS,
    download_backbone,
    parse_int,
)
from daynimal.db.models import Base
from daynimal.db.session import get_engine


def optimize_database_for_import(engine):
    """Configure SQLite for maximum import speed."""
    print("Optimizing database for bulk import...")
    with engine.begin() as conn:  # Use begin() for auto-commit
        # Disable safety checks for speed (but keep journal_mode default)
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


def extract_and_filter_taxa(
    zip_path: Path, output_path: Path, mode: str = "full"
) -> int:
    """
    Extract taxa from GBIF ZIP and create a filtered TSV file.

    Filtering strategy:
    - full: All Animalia kingdom taxa
    - minimal: Only species (rank='species')

    Args:
        zip_path: Path to GBIF backbone ZIP file
        output_path: Path for output TSV file
        mode: Extraction mode ('full' or 'minimal')

    Returns the number of taxa extracted.
    """
    print(f"Extracting and filtering taxa to {output_path} (mode: {mode})...")

    count = 0

    with zipfile.ZipFile(zip_path, "r") as zf:
        # Find Taxon.tsv in the archive
        taxon_file = None
        for name in zf.namelist():
            if name.endswith("Taxon.tsv") or name == "Taxon.tsv":
                taxon_file = name
                break

        if not taxon_file:
            raise FileNotFoundError("Taxon.tsv not found in archive")

        with (
            zf.open(taxon_file) as f_in,
            open(output_path, "w", encoding="utf-8", newline="") as f_out,
        ):
            reader = csv.reader(
                io.TextIOWrapper(f_in, encoding="utf-8"),
                delimiter="\t",
                quoting=csv.QUOTE_NONE,
            )
            writer = csv.writer(
                f_out, delimiter="\t", quoting=csv.QUOTE_NONE, escapechar="\\"
            )

            # Skip header
            next(reader)

            for row in reader:
                if len(row) < 23:
                    continue

                kingdom = row[TAXON_COLUMNS["kingdom"]]

                # Filter: only Animalia
                if kingdom != "Animalia":
                    continue

                # Extract columns needed for filtering
                rank = row[TAXON_COLUMNS["taxonRank"]].lower() or ""

                # Mode-specific filtering
                if mode == "minimal":
                    # Minimal mode: only species
                    if rank != "species":
                        continue

                # Extract only the columns we need, in the right order
                taxon_id = row[TAXON_COLUMNS["taxonID"]]
                scientific_name = row[TAXON_COLUMNS["scientificName"]]
                canonical_name = row[TAXON_COLUMNS["canonicalName"]] or ""
                kingdom_val = kingdom
                phylum = row[TAXON_COLUMNS["phylum"]] or ""
                class_ = row[TAXON_COLUMNS["class"]] or ""
                order = row[TAXON_COLUMNS["order"]] or ""
                family = row[TAXON_COLUMNS["family"]] or ""
                genus = row[TAXON_COLUMNS["genus"]] or ""
                parent_id = row[TAXON_COLUMNS["parentNameUsageID"]] or ""
                accepted_id = row[TAXON_COLUMNS["acceptedNameUsageID"]] or ""
                is_synonym = (
                    "1" if row[TAXON_COLUMNS["taxonomicStatus"]] == "synonym" else "0"
                )

                # Write row
                writer.writerow(
                    [
                        taxon_id,
                        scientific_name,
                        canonical_name,
                        rank,
                        kingdom_val,
                        phylum,
                        class_,
                        order,
                        family,
                        genus,
                        parent_id,
                        accepted_id,
                        is_synonym,
                    ]
                )

                count += 1
                if count % 100000 == 0:
                    print(f"\rExtracted: {count:,} taxa...", end="", flush=True)

    print(f"\nExtraction complete: {count:,} Animalia taxa extracted.")
    return count


def extract_and_filter_vernacular(
    zip_path: Path, output_path: Path, valid_taxon_ids: set
) -> int:
    """
    Extract vernacular names from GBIF ZIP and create a filtered TSV file.
    Only includes names for taxa in valid_taxon_ids.

    Returns the number of names extracted.
    """
    print(f"Extracting and filtering vernacular names to {output_path}...")

    count = 0

    with zipfile.ZipFile(zip_path, "r") as zf:
        # Find VernacularName.tsv
        vernacular_file = None
        for name in zf.namelist():
            if "VernacularName" in name and name.endswith(".tsv"):
                vernacular_file = name
                break

        if not vernacular_file:
            print("VernacularName.tsv not found, skipping.")
            return 0

        with (
            zf.open(vernacular_file) as f_in,
            open(output_path, "w", encoding="utf-8", newline="") as f_out,
        ):
            reader = csv.reader(
                io.TextIOWrapper(f_in, encoding="utf-8"),
                delimiter="\t",
                quoting=csv.QUOTE_NONE,
            )
            writer = csv.writer(
                f_out, delimiter="\t", quoting=csv.QUOTE_NONE, escapechar="\\"
            )

            # Skip header
            next(reader)

            for row in reader:
                if len(row) < 3:
                    continue

                taxon_id_str = row[VERNACULAR_COLUMNS["taxonID"]]
                taxon_id = parse_int(taxon_id_str)

                if taxon_id is None or taxon_id not in valid_taxon_ids:
                    continue

                name = row[VERNACULAR_COLUMNS["vernacularName"]]
                language = row[VERNACULAR_COLUMNS["language"]] or ""

                writer.writerow([taxon_id, name, language])

                count += 1
                if count % 100000 == 0:
                    print(f"\rExtracted: {count:,} names...", end="", flush=True)

    print(f"\nExtraction complete: {count:,} vernacular names extracted.")
    return count


def bulk_import_taxa(engine, tsv_path: Path) -> int:
    """
    Import taxa from TSV file using optimized bulk insert.
    """
    print(f"Importing taxa from {tsv_path}...")

    count = 0
    batch = []
    batch_size = 5000

    with engine.begin() as conn:  # Single transaction for entire import
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

            # Import remaining batch
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
    """
    Import vernacular names from TSV file using optimized bulk insert.
    """
    print(f"Importing vernacular names from {tsv_path}...")

    count = 0
    batch = []
    batch_size = 10000

    with engine.begin() as conn:  # Single transaction for entire import
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

            # Import remaining batch
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


def cleanup_taxa_without_vernacular(engine) -> int:
    """
    Remove taxa that don't have any vernacular names.
    Used in minimal mode (Option D) to keep only species with common names.

    Returns the number of taxa removed.
    """
    print("Removing taxa without vernacular names...")

    with engine.begin() as conn:
        # Count before
        before_count = conn.execute(text("SELECT COUNT(*) FROM taxa")).scalar()

        # Delete taxa without vernacular names
        conn.execute(
            text("""
                DELETE FROM taxa
                WHERE taxon_id NOT IN (
                    SELECT DISTINCT taxon_id FROM vernacular_names
                )
            """)
        )

        # Count after
        after_count = conn.execute(text("SELECT COUNT(*) FROM taxa")).scalar()

    removed = before_count - after_count
    print(f"Removed {removed:,} taxa without vernacular names")
    print(f"Remaining: {after_count:,} taxa")

    return removed


def main():
    """Main entry point for fast GBIF import."""
    import argparse

    parser = argparse.ArgumentParser(description="Fast GBIF Backbone Taxonomy importer")
    parser.add_argument(
        "--mode",
        choices=["full", "minimal"],
        default="full",
        help="Import mode: 'full' (all Animalia) or 'minimal' (species with vernacular names only)",
    )
    parser.add_argument(
        "--save-tsv",
        action="store_true",
        help="Save filtered TSV files (useful for distribution)",
    )

    args = parser.parse_args()

    print("=" * 60)
    print("GBIF Backbone Taxonomy Fast Importer")
    print(f"Mode: {args.mode.upper()}")
    if args.mode == "minimal":
        print("(Species with vernacular names only)")
    print("License: CC-BY 4.0 (commercial use allowed with attribution)")
    print("=" * 60)

    data_dir = settings.data_dir
    data_dir.mkdir(parents=True, exist_ok=True)

    zip_path = data_dir / "backbone.zip"

    # Use different filenames for minimal mode
    if args.mode == "minimal":
        taxa_tsv = data_dir / "animalia_taxa_minimal.tsv"
        vernacular_tsv = data_dir / "animalia_vernacular_minimal.tsv"
        db_filename = "daynimal_minimal.db"
    else:
        taxa_tsv = data_dir / "animalia_taxa.tsv"
        vernacular_tsv = data_dir / "animalia_vernacular.tsv"
        db_filename = "daynimal.db"

    # Temporarily override database URL for this import
    original_db_url = settings.database_url
    settings.database_url = f"sqlite:///{db_filename}"

    # Download if not exists
    if not zip_path.exists():
        download_backbone(zip_path)
    else:
        print(f"Using existing download: {zip_path}")

    print(f"Target database: {db_filename}")

    # Create database and tables
    engine = get_engine()
    print("Creating database tables...")
    Base.metadata.create_all(engine)

    # Verify tables were created
    with engine.connect() as conn:
        result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
        tables = [row[0] for row in result]
        print(f"Tables created: {tables}")
        if "taxa" not in tables:
            raise RuntimeError("Failed to create taxa table!")

    # Optimize database for import AFTER creating tables
    optimize_database_for_import(engine)

    try:
        # Step 1: Extract and filter taxa
        if not taxa_tsv.exists():
            extract_and_filter_taxa(zip_path, taxa_tsv, mode=args.mode)
        else:
            print(f"Using existing filtered taxa file: {taxa_tsv}")

        # Step 2: Import taxa
        bulk_import_taxa(engine, taxa_tsv)

        # Step 3: Get valid taxon IDs for vernacular filtering
        print("Loading taxon IDs for vernacular filtering...")
        with engine.connect() as conn:
            result = conn.execute(text("SELECT taxon_id FROM taxa"))
            valid_ids = {row[0] for row in result}
        print(f"Found {len(valid_ids):,} valid taxon IDs")

        # Step 4: Extract and filter vernacular names
        if not vernacular_tsv.exists():
            extract_and_filter_vernacular(zip_path, vernacular_tsv, valid_ids)
        else:
            print(f"Using existing filtered vernacular file: {vernacular_tsv}")

        # Step 5: Import vernacular names
        bulk_import_vernacular(engine, vernacular_tsv)

        # Step 6: Cleanup (minimal mode only)
        if args.mode == "minimal":
            cleanup_taxa_without_vernacular(engine)

        # Step 7: Optional - save TSV files for distribution
        if args.save_tsv:
            print("\nTSV files saved for distribution:")
            print(f"  Taxa:        {taxa_tsv}")
            print(f"  Vernacular:  {vernacular_tsv}")
            print("\nThese files can be compressed and distributed for mobile apps.")

    finally:
        # Restore normal database settings
        restore_database_settings(engine)
        # Restore original database URL
        settings.database_url = original_db_url

    # Show stats
    with engine.connect() as conn:
        total_taxa = conn.execute(text("SELECT COUNT(*) FROM taxa")).scalar()
        species_count = conn.execute(
            text("SELECT COUNT(*) FROM taxa WHERE rank = 'species'")
        ).scalar()
        vernacular_count = conn.execute(
            text("SELECT COUNT(*) FROM vernacular_names")
        ).scalar()

    print("\n" + "=" * 60)
    print("DATABASE STATISTICS")
    print("=" * 60)
    print(f"Mode:             {args.mode.upper()}")
    print(f"Total taxa:       {total_taxa:,}")
    print(f"Species:          {species_count:,}")
    print(f"Vernacular names: {vernacular_count:,}")

    if args.mode == "minimal":
        print("\nNote: Minimal mode includes only species with common names.")
        print(f"This is optimized for mobile apps (~{total_taxa:,} taxa).")

    # Compact database to reclaim unused space
    print("\n" + "=" * 60)
    print("COMPACTING DATABASE...")
    print("=" * 60)
    print("Running VACUUM to reclaim unused space...")
    with engine.connect() as conn:
        conn.execute(text("VACUUM"))
        conn.commit()
    print("[OK] Database compacted")

    print("\n" + "=" * 60)
    print("IMPORT COMPLETE!")
    print("=" * 60)
    print("Attribution: GBIF Backbone Taxonomy. GBIF Secretariat (2024).")
    print("License: https://creativecommons.org/licenses/by/4.0/")
    print("\nNext steps:")
    if args.mode == "full":
        print("  - Run 'uv run init-fts' to create search index")
        print("  - Or create minimal DB: 'uv run import-gbif-fast --mode minimal'")
    else:
        print("  - Run 'uv run init-fts' to create search index")
        print("  - Database is ready for mobile deployment!")
        if args.save_tsv:
            print("  - Compress TSV files for distribution:")
            print(f"    gzip {taxa_tsv}")
            print(f"    gzip {vernacular_tsv}")


if __name__ == "__main__":
    main()
