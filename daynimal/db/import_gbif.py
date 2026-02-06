"""
GBIF Backbone Taxonomy importer.

Downloads and imports the GBIF Backbone Taxonomy (Animalia only) into the local database.
The GBIF Backbone Taxonomy is licensed under CC-BY 4.0, compatible with commercial use.

Supports resumable downloads and imports:
- Downloads can resume from partial files using HTTP Range requests
- Imports track progress and skip already-imported records on restart

Usage:
    python -m daynimal.db.import_gbif

Data source:
    https://hosted-datasets.gbif.org/datasets/backbone/current/
"""

import csv
import io
import zipfile
from pathlib import Path

import httpx
from sqlalchemy import Integer, String
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.orm import Mapped, mapped_column

from daynimal.config import settings
from daynimal.db.models import Base, TaxonModel, VernacularNameModel
from daynimal.db.session import get_engine, get_session


class ImportProgressModel(Base):
    """Track import progress for resumable imports."""

    __tablename__ = "import_progress"

    task: Mapped[str] = mapped_column(String(50), primary_key=True)
    last_line: Mapped[int] = mapped_column(Integer, default=0)


# GBIF Backbone download URL
GBIF_BACKBONE_URL = (
    "https://hosted-datasets.gbif.org/datasets/backbone/current/backbone.zip"
)

# Alternatively, use a smaller "simple" version for testing
GBIF_SIMPLE_URL = (
    "https://hosted-datasets.gbif.org/datasets/backbone/current/simple.txt.gz"
)

# Column indices in Taxon.tsv (Darwin Core Archive format)
# Based on GBIF Backbone structure (checked 2026-02-05)
TAXON_COLUMNS = {
    "taxonID": 0,
    "datasetID": 1,
    "parentNameUsageID": 2,
    "acceptedNameUsageID": 3,
    "originalNameUsageID": 4,
    "scientificName": 5,
    "scientificNameAuthorship": 6,
    "canonicalName": 7,
    "genericName": 8,
    "specificEpithet": 9,
    "infraspecificEpithet": 10,
    "taxonRank": 11,
    "nameAccordingTo": 12,
    "namePublishedIn": 13,
    "taxonomicStatus": 14,
    "nomenclaturalStatus": 15,
    "taxonRemarks": 16,
    "kingdom": 17,
    "phylum": 18,
    "class": 19,
    "order": 20,
    "family": 21,
    "genus": 22,
}

VERNACULAR_COLUMNS = {"taxonID": 0, "vernacularName": 1, "language": 2}


def download_backbone(dest_path: Path) -> Path:
    """
    Download the GBIF Backbone ZIP file with resume support.

    If a partial download exists, resumes from where it left off using HTTP Range requests.
    """
    partial_path = dest_path.with_suffix(".zip.partial")
    dest_path.parent.mkdir(parents=True, exist_ok=True)

    # Check for existing partial download
    existing_size = partial_path.stat().st_size if partial_path.exists() else 0

    # First, get the total size with a HEAD request
    head_response = httpx.head(GBIF_BACKBONE_URL, timeout=30, follow_redirects=True)
    head_response.raise_for_status()
    total_size = int(head_response.headers.get("content-length", 0))
    accepts_ranges = head_response.headers.get("accept-ranges") == "bytes"

    if existing_size > 0 and accepts_ranges:
        if existing_size >= total_size:
            print(f"Download already complete ({existing_size:,} bytes)")
            partial_path.rename(dest_path)
            return dest_path
        print(f"Resuming download from {existing_size:,} / {total_size:,} bytes...")
        headers = {"Range": f"bytes={existing_size}-"}
        mode = "ab"
    else:
        if existing_size > 0 and not accepts_ranges:
            print("Server does not support resume, restarting download...")
            partial_path.unlink()
        print(f"Downloading GBIF Backbone from {GBIF_BACKBONE_URL}...")
        print(f"Total size: {total_size / 1024 / 1024:.1f} MB")
        headers = {}
        mode = "wb"
        existing_size = 0

    with httpx.stream(
        "GET", GBIF_BACKBONE_URL, timeout=None, follow_redirects=True, headers=headers
    ) as response:
        # 206 = Partial Content (resume), 200 = OK (full download)
        if response.status_code not in (200, 206):
            response.raise_for_status()

        with open(partial_path, mode) as f:
            downloaded = existing_size
            for chunk in response.iter_bytes(chunk_size=65536):
                f.write(chunk)
                downloaded += len(chunk)
                if total_size:
                    pct = (downloaded / total_size) * 100
                    print(
                        f"\rDownloading: {pct:.1f}% ({downloaded // 1024 // 1024} MB / {total_size // 1024 // 1024} MB)",
                        end="",
                        flush=True,
                    )

    print("\nDownload complete.")
    partial_path.rename(dest_path)
    return dest_path


def parse_int(value: str) -> int | None:
    """Parse integer, returning None for empty strings."""
    if value and value.strip():
        try:
            return int(value)
        except ValueError:
            return None
    return None


def get_progress(session, task: str) -> int:
    """Get the last processed line number for a task."""
    progress = session.get(ImportProgressModel, task)
    return progress.last_line if progress else 0


def save_progress(session, task: str, line: int):
    """Save the current progress for a task."""
    stmt = sqlite_insert(ImportProgressModel).values(task=task, last_line=line)
    stmt = stmt.on_conflict_do_update(index_elements=["task"], set_={"last_line": line})
    session.execute(stmt)
    session.commit()


def import_taxa_from_zip(zip_path: Path, batch_size: int = 2000) -> int:
    """
    Import taxa from the GBIF Backbone ZIP file with resume support.
    Only imports Animalia kingdom.

    Uses INSERT OR IGNORE to handle duplicates on restart, and tracks progress
    to skip already-processed lines efficiently.

    Returns the number of taxa imported in this run.
    """
    task_name = "taxa_import"
    engine = get_engine()
    Base.metadata.create_all(engine)

    session = get_session()

    # Check where we left off
    start_line = get_progress(session, task_name)
    if start_line > 0:
        print(f"Resuming taxa import from line {start_line:,}...")

    imported = 0
    skipped_non_animalia = 0
    skipped_lines = 0
    current_line = 0
    batch = []

    print("Extracting and importing Taxon.tsv (Animalia only)...")

    with zipfile.ZipFile(zip_path, "r") as zf:
        # Find Taxon.tsv in the archive
        taxon_file = None
        for name in zf.namelist():
            if name.endswith("Taxon.tsv") or name == "Taxon.tsv":
                taxon_file = name
                break

        if not taxon_file:
            raise FileNotFoundError("Taxon.tsv not found in archive")

        with zf.open(taxon_file) as f:
            reader = csv.reader(
                io.TextIOWrapper(f, encoding="utf-8"),
                delimiter="\t",
                quoting=csv.QUOTE_NONE,
            )

            # Skip header
            next(reader)
            current_line = 1

            for row in reader:
                current_line += 1

                # Skip lines we've already processed
                if current_line <= start_line:
                    skipped_lines += 1
                    if skipped_lines % 500000 == 0:
                        print(
                            f"\rSkipping to line {current_line:,}...",
                            end="",
                            flush=True,
                        )
                    continue

                if len(row) < 23:
                    continue

                kingdom = row[TAXON_COLUMNS["kingdom"]]

                # Filter: only Animalia
                if kingdom != "Animalia":
                    skipped_non_animalia += 1
                    continue

                taxon_data = {
                    "taxon_id": int(row[TAXON_COLUMNS["taxonID"]]),
                    "scientific_name": row[TAXON_COLUMNS["scientificName"]],
                    "canonical_name": row[TAXON_COLUMNS["canonicalName"]] or None,
                    "rank": row[TAXON_COLUMNS["taxonRank"]].lower() or None,
                    "kingdom": kingdom,
                    "phylum": row[TAXON_COLUMNS["phylum"]] or None,
                    "class_": row[TAXON_COLUMNS["class"]] or None,
                    "order": row[TAXON_COLUMNS["order"]] or None,
                    "family": row[TAXON_COLUMNS["family"]] or None,
                    "genus": row[TAXON_COLUMNS["genus"]] or None,
                    "parent_id": parse_int(row[TAXON_COLUMNS["parentNameUsageID"]]),
                    "accepted_id": parse_int(row[TAXON_COLUMNS["acceptedNameUsageID"]]),
                    "is_synonym": row[TAXON_COLUMNS["taxonomicStatus"]] == "synonym",
                }

                batch.append(taxon_data)

                if len(batch) >= batch_size:
                    # Use INSERT OR IGNORE for idempotent inserts
                    stmt = sqlite_insert(TaxonModel).values(batch)
                    stmt = stmt.on_conflict_do_nothing(index_elements=["taxon_id"])
                    session.execute(stmt)
                    save_progress(session, task_name, current_line)
                    imported += len(batch)
                    print(
                        f"\rImported: {imported:,} taxa (line {current_line:,}, skipped {skipped_non_animalia:,} non-Animalia)",
                        end="",
                        flush=True,
                    )
                    batch = []

            # Final batch
            if batch:
                stmt = sqlite_insert(TaxonModel).values(batch)
                stmt = stmt.on_conflict_do_nothing(index_elements=["taxon_id"])
                session.execute(stmt)
                save_progress(session, task_name, current_line)
                imported += len(batch)

    print(f"\nTaxa import complete: {imported:,} Animalia taxa imported.")
    session.close()
    return imported


def import_vernacular_names(zip_path: Path, batch_size: int = 5000) -> int:
    """
    Import vernacular names from VernacularName.tsv with resume support.
    Only imports names for taxa that exist in the database (Animalia).

    Uses line tracking for resume capability. Since vernacular names have auto-generated
    IDs, we track progress by line number and use INSERT with conflict detection.

    Returns the number of vernacular names imported in this run.
    """
    task_name = "vernacular_import"
    session = get_session()

    # Check where we left off
    start_line = get_progress(session, task_name)
    if start_line > 0:
        print(f"Resuming vernacular import from line {start_line:,}...")

    # Get set of valid taxon IDs (Animalia)
    print("Loading existing taxon IDs...")
    valid_ids = set(row[0] for row in session.query(TaxonModel.taxon_id).all())
    print(f"Found {len(valid_ids):,} valid taxon IDs")

    imported = 0
    skipped_invalid = 0
    skipped_lines = 0
    current_line = 0
    batch = []

    print("Extracting and importing VernacularName.tsv...")

    with zipfile.ZipFile(zip_path, "r") as zf:
        # Find VernacularName.tsv
        vernacular_file = None
        for name in zf.namelist():
            if "VernacularName" in name and name.endswith(".tsv"):
                vernacular_file = name
                break

        if not vernacular_file:
            print("VernacularName.tsv not found, skipping vernacular names.")
            return 0

        with zf.open(vernacular_file) as f:
            reader = csv.reader(
                io.TextIOWrapper(f, encoding="utf-8"),
                delimiter="\t",
                quoting=csv.QUOTE_NONE,
            )

            # Skip header
            next(reader)
            current_line = 1

            for row in reader:
                current_line += 1

                # Skip lines we've already processed
                if current_line <= start_line:
                    skipped_lines += 1
                    if skipped_lines % 500000 == 0:
                        print(
                            f"\rSkipping to line {current_line:,}...",
                            end="",
                            flush=True,
                        )
                    continue

                if len(row) < 3:
                    continue

                taxon_id = parse_int(row[VERNACULAR_COLUMNS["taxonID"]])
                if taxon_id is None or taxon_id not in valid_ids:
                    skipped_invalid += 1
                    continue

                vernacular_data = {
                    "taxon_id": taxon_id,
                    "name": row[VERNACULAR_COLUMNS["vernacularName"]],
                    "language": row[VERNACULAR_COLUMNS["language"]] or None,
                }

                batch.append(vernacular_data)

                if len(batch) >= batch_size:
                    # Use regular insert - duplicates are unlikely since we track lines
                    session.execute(sqlite_insert(VernacularNameModel).values(batch))
                    save_progress(session, task_name, current_line)
                    imported += len(batch)
                    print(
                        f"\rImported: {imported:,} vernacular names (line {current_line:,})",
                        end="",
                        flush=True,
                    )
                    batch = []

            # Final batch
            if batch:
                session.execute(sqlite_insert(VernacularNameModel).values(batch))
                save_progress(session, task_name, current_line)
                imported += len(batch)

    print(f"\nVernacular names import complete: {imported:,} names imported.")
    session.close()
    return imported


def print_stats():
    """Print database statistics."""
    session = get_session()

    total_taxa = session.query(TaxonModel).count()
    species_count = (
        session.query(TaxonModel).filter(TaxonModel.rank == "species").count()
    )
    vernacular_count = session.query(VernacularNameModel).count()

    print("\n--- Database Statistics ---")
    print(f"Total taxa: {total_taxa:,}")
    print(f"Species: {species_count:,}")
    print(f"Vernacular names: {vernacular_count:,}")

    # Sample some taxa
    print("\nSample taxa:")
    samples = (
        session.query(TaxonModel).filter(TaxonModel.rank == "species").limit(5).all()
    )
    for t in samples:
        names = [v.name for v in t.vernacular_names[:3]]
        print(
            f"  - {t.scientific_name} ({', '.join(names) if names else 'no common name'})"
        )

    session.close()


def main():
    """Main entry point for GBIF import."""
    print("=" * 60)
    print("GBIF Backbone Taxonomy Importer")
    print("License: CC-BY 4.0 (commercial use allowed with attribution)")
    print("=" * 60)

    data_dir = settings.data_dir
    data_dir.mkdir(parents=True, exist_ok=True)

    zip_path = data_dir / "backbone.zip"
    partial_path = zip_path.with_suffix(".zip.partial")

    # Download if not exists (or resume partial download)
    if not zip_path.exists():
        if partial_path.exists():
            print(f"Found partial download: {partial_path}")
        download_backbone(zip_path)
    else:
        print(f"Using existing download: {zip_path}")

    # Create tables
    engine = get_engine()
    Base.metadata.create_all(engine)

    # Import (with automatic resume)
    import_taxa_from_zip(zip_path)
    import_vernacular_names(zip_path)

    # Stats
    print_stats()

    print("\nImport complete!")
    print("Attribution: GBIF Backbone Taxonomy. GBIF Secretariat (2024).")
    print("License: https://creativecommons.org/licenses/by/4.0/")


if __name__ == "__main__":
    main()
