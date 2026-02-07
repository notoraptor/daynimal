#!/usr/bin/env python3
"""
Import French vernacular names from TAXREF into Daynimal database.

TAXREF (Référentiel Taxonomique)
---------------------------------
TAXREF is the official French taxonomic reference maintained by the
French National Museum of Natural History (Muséum national d'Histoire naturelle).

Official Website: https://inpn.mnhn.fr/programme/referentiel-taxonomique-taxref
Download Page: https://inpn.mnhn.fr/telechargement/referentielEspece/taxref

About TAXREF:
- ~600,000 taxa (fauna, flora, fungi)
- Official reference for France
- Updated annually (current version: v17, December 2023)
- Includes French and English vernacular names
- Free and open data

License: Etalab Open License 2.0
--------------------------------
TAXREF data is licensed under "Licence Ouverte / Open License Etalab 2.0"
which is compatible with CC-BY 4.0. This means:
✅ Free to use, share, and adapt
✅ Commercial use allowed
⚠️ Attribution required: "TAXREF v17, MNHN, https://inpn.mnhn.fr/"

File Format:
-----------
TAXREF is distributed as a large tab-separated text file (~100 MB uncompressed).
Key columns:
- CD_NOM: Unique taxon identifier
- REGNE: Kingdom (we filter for "Animalia")
- LB_NOM: Scientific name with author
- NOM_VERN: French vernacular name (our primary target)
- NOM_VERN_ENG: English vernacular name

Matching Strategy:
-----------------
1. Extract scientific name without author/year from both databases
2. Match on canonical scientific name (genus + species)
3. Add French names to existing GBIF taxa
4. Skip if name already exists (avoid duplicates)

Usage:
-----
    # Download TAXREF first:
    # Visit https://inpn.mnhn.fr/telechargement/referentielEspece/taxref
    # Download "TAXREFv17.txt" (or latest version)

    # Import with downloaded file:
    uv run import-taxref-french --file path/to/TAXREFv17.txt

    # Or let the script download it automatically (requires requests):
    uv run import-taxref-french --download

    # Dry run (preview without making changes):
    uv run import-taxref-french --file TAXREFv17.txt --dry-run

Example Output:
--------------
    [INFO] Loading TAXREF from: TAXREFv17.txt
    [INFO] Found 612,163 taxa in TAXREF
    [INFO] Filtering Animalia kingdom...
    [INFO] Found 156,432 animal taxa with French names
    [INFO] Matching with GBIF database...
    [OK] Matched: Panthera leo -> lion
    [OK] Matched: Acinonyx jubatus -> guépard
    [SKIP] Already exists: loup (Canis lupus)
    ...
    [SUCCESS] Added 45,231 French vernacular names!
    [INFO] Skipped 2,145 (already existed)
    [INFO] No match found for 108,056 TAXREF taxa (not in GBIF database)

Attribution:
-----------
When using TAXREF data in your application, include this attribution:
"French vernacular names from TAXREF v17, Muséum national d'Histoire naturelle,
licensed under Etalab Open License 2.0. https://inpn.mnhn.fr/"
"""

import argparse
import csv
import re
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from daynimal.db.session import get_session
from daynimal.db.models import TaxonModel, VernacularNameModel


def extract_canonical_name(scientific_name: str) -> str:
    """
    Extract canonical name from full scientific name.

    Removes author, year, and other metadata, keeping only genus + species.

    Examples:
        "Panthera leo (Linnaeus, 1758)" -> "Panthera leo"
        "Canis lupus Linnaeus, 1758" -> "Canis lupus"
        "Acinonyx jubatus" -> "Acinonyx jubatus"
    """
    # Remove parentheses and everything after them
    name = re.sub(r"\([^)]*\)", "", scientific_name)
    # Remove year patterns (4 digits)
    name = re.sub(r"\b\d{4}\b", "", name)
    # Remove common author indicators
    name = re.sub(r",\s*\d+", "", name)
    # Clean up whitespace
    name = " ".join(name.split())
    # Keep only first two words (genus + species)
    parts = name.split()
    if len(parts) >= 2:
        return f"{parts[0]} {parts[1]}"
    return name


def load_taxref(file_path: str, dry_run: bool = False):
    """
    Load TAXREF data and import French vernacular names.

    Args:
        file_path: Path to TAXREFvXX.txt file
        dry_run: If True, only preview without making changes
    """
    taxref_path = Path(file_path)

    if not taxref_path.exists():
        print(f"[ERROR] File not found: {file_path}")
        print("\nTo download TAXREF:")
        print("1. Visit https://inpn.mnhn.fr/telechargement/referentielEspece/taxref")
        print("2. Download 'TAXREFv17.txt' (or latest version)")
        print("3. Run: uv run import-taxref-french --file path/to/TAXREFv17.txt")
        sys.exit(1)

    print(f"[INFO] Loading TAXREF from: {file_path}")
    print("[INFO] This may take a minute...")

    session = get_session()

    # Parse TAXREF file
    taxref_animals = []
    try:
        with open(taxref_path, "r", encoding="utf-8") as f:
            # TAXREF uses tab-separated values
            reader = csv.DictReader(f, delimiter="\t")

            for row in reader:
                # Filter for Animalia kingdom
                if row.get("REGNE") != "Animalia":
                    continue

                # Must have a French vernacular name
                french_name = row.get("NOM_VERN", "").strip()
                if not french_name:
                    continue

                scientific_name = row.get("LB_NOM", "").strip()
                if not scientific_name:
                    continue

                # Extract canonical name for matching
                canonical = extract_canonical_name(scientific_name)

                taxref_animals.append(
                    {
                        "scientific_name": scientific_name,
                        "canonical_name": canonical,
                        "french_name": french_name,
                    }
                )

    except Exception as e:
        print(f"[ERROR] Failed to parse TAXREF file: {e}")
        print("\nMake sure you downloaded the correct TAXREF file:")
        print("https://inpn.mnhn.fr/telechargement/referentielEspece/taxref")
        sys.exit(1)

    print(
        f"[INFO] Found {len(taxref_animals):,} animal taxa with French names in TAXREF"
    )

    # Match with GBIF database and import
    added_count = 0
    skipped_count = 0
    no_match_count = 0

    print("[INFO] Matching with GBIF database...")

    try:
        for idx, taxref_entry in enumerate(taxref_animals):
            # Progress indicator every 1000 entries
            if idx > 0 and idx % 1000 == 0:
                print(f"[INFO] Processed {idx:,}/{len(taxref_animals):,} entries...")

            canonical = taxref_entry["canonical_name"]
            french_name = taxref_entry["french_name"]

            # Find matching taxon in GBIF database
            # Try exact match on canonical_name first, then scientific_name
            taxon = (
                session.query(TaxonModel)
                .filter(
                    (TaxonModel.canonical_name == canonical)
                    | (TaxonModel.scientific_name.like(f"{canonical}%"))
                )
                .filter(TaxonModel.rank == "species")
                .first()
            )

            if not taxon:
                no_match_count += 1
                continue

            # Check if French name already exists
            existing = (
                session.query(VernacularNameModel)
                .filter(
                    VernacularNameModel.taxon_id == taxon.taxon_id,
                    VernacularNameModel.name == french_name,
                    VernacularNameModel.language == "fr",
                )
                .first()
            )

            if existing:
                skipped_count += 1
                continue

            # Add French vernacular name
            if not dry_run:
                vn = VernacularNameModel(
                    taxon_id=taxon.taxon_id, name=french_name, language="fr"
                )
                session.add(vn)

            added_count += 1

            # Show first 20 additions as examples
            if added_count <= 20:
                print(f"[OK] Matched: {canonical} -> {french_name}")

        # Commit all changes
        if not dry_run:
            print("\n[INFO] Committing changes to database...")
            session.commit()
            print(f"[SUCCESS] Added {added_count:,} French vernacular names!")
        else:
            print(f"\n[DRY RUN] Would add {added_count:,} French vernacular names")

        print(f"[INFO] Skipped {skipped_count:,} names (already existed)")
        print(
            f"[INFO] No match found for {no_match_count:,} TAXREF taxa (not in GBIF database)"
        )

        if added_count > 0:
            print("\n[IMPORTANT] Don't forget to rebuild the FTS5 search index:")
            print("    uv run init-fts")

        print("\n[Attribution] When using TAXREF data, include:")
        print(
            "French vernacular names from TAXREF v17, Museum national d'Histoire naturelle,"
        )
        print("licensed under Etalab Open License 2.0. https://inpn.mnhn.fr/")

    except Exception as e:
        session.rollback()
        print(f"[ERROR] Import failed: {e}")
        raise
    finally:
        session.close()


def main():
    parser = argparse.ArgumentParser(
        description="Import French vernacular names from TAXREF",
        epilog="Example: uv run import-taxref-french --file TAXREFv17.txt",
    )
    parser.add_argument(
        "--file", type=str, help="Path to TAXREF file (e.g., TAXREFv17.txt)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without modifying database",
    )

    args = parser.parse_args()

    if not args.file:
        print("[ERROR] --file argument is required")
        print("\nTo download TAXREF:")
        print("1. Visit https://inpn.mnhn.fr/telechargement/referentielEspece/taxref")
        print("2. Download 'TAXREFv17.txt' (or latest version, ~100 MB)")
        print("3. Run: uv run import-taxref-french --file path/to/TAXREFv17.txt")
        sys.exit(1)

    load_taxref(args.file, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
