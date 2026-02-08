#!/usr/bin/env python3
"""
Export TAXREF French names to TSV format (for distribution).

This script reads the raw TAXREF file and generates a pre-processed TSV file
containing French vernacular names indexed by canonical_name (genus + species).
This TSV can be distributed to mobile apps and imported into any database
(full or minimal) without depending on specific taxon_id values.

Usage:
    # Export from TAXREF file
    uv run export-taxref-tsv --taxref data/TAXREFv18.txt

    # Custom output file
    uv run export-taxref-tsv --taxref data/TAXREFv18.txt --output data/taxref_french.tsv

Output format:
    TSV file with 3 columns (no header):
    canonical_name    name    language

    Example:
    Panthera leo      Lion           fr
    Panthera leo      Lion d'Afrique fr

This format is database-agnostic: the import script will match canonical_name
to taxon_id at import time, making it work with any GBIF-based database.
"""

import argparse
import csv
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


def extract_canonical_name(scientific_name: str) -> str:
    """Extract canonical name (genus + species only)."""
    name = re.sub(r"\([^)]*\)", "", scientific_name)
    name = re.sub(r"\b\d{4}\b", "", name)
    name = re.sub(r",\s*\d+", "", name)
    name = " ".join(name.split())
    parts = name.split()
    if len(parts) >= 2:
        return f"{parts[0]} {parts[1]}"
    return name


def export_taxref_to_tsv(taxref_path: Path, output_path: Path):
    """
    Export TAXREF French names to TSV format.

    Args:
        taxref_path: Path to TAXREF raw file (TAXREFv18.txt)
        output_path: Path to output TSV file
    """
    print("=" * 60)
    print("TAXREF TSV EXPORT (database-agnostic format)")
    print("=" * 60)

    if not taxref_path.exists():
        print(f"[ERROR] TAXREF file not found: {taxref_path}")
        sys.exit(1)

    # STEP 1: Parse TAXREF file
    print(f"\n[1/3] Parsing TAXREF file: {taxref_path}")
    taxref_entries = []
    seen_combinations = set()  # To avoid duplicates

    try:
        with open(taxref_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f, delimiter="\t")
            for row in reader:
                # Filter: Animalia only
                if row.get("REGNE") != "Animalia":
                    continue

                # Extract French name
                french_name = row.get("NOM_VERN", "").strip()
                if not french_name:
                    continue

                # Extract scientific name and convert to canonical
                scientific_name = row.get("LB_NOM", "").strip()
                if not scientific_name:
                    continue

                canonical = extract_canonical_name(scientific_name)

                # Avoid duplicates (same canonical + french name)
                key = (canonical.lower(), french_name.lower())
                if key in seen_combinations:
                    continue

                seen_combinations.add(key)
                taxref_entries.append(
                    {"canonical_name": canonical, "french_name": french_name}
                )

    except Exception as e:
        print(f"[ERROR] Failed to parse TAXREF: {e}")
        sys.exit(1)

    print(f"[OK] Found {len(taxref_entries):,} unique (canonical_name, french_name) pairs")

    if not taxref_entries:
        print("[ERROR] No entries to export!")
        sys.exit(1)

    # STEP 2: Export to TSV
    print(f"\n[2/3] Exporting to {output_path}...")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, delimiter="\t", quoting=csv.QUOTE_NONE, escapechar="\\")

        # Sort by canonical_name for better compression and readability
        taxref_entries.sort(key=lambda x: (x["canonical_name"].lower(), x["french_name"]))

        count = 0
        for entry in taxref_entries:
            writer.writerow([entry["canonical_name"], entry["french_name"], "fr"])
            count += 1

            # Show first 20 as examples
            if count <= 20:
                print(f"[OK] {entry['canonical_name']} -> {entry['french_name']}")

            if count % 10000 == 0:
                print(f"      Exported {count:,}/{len(taxref_entries):,}...", end="\r")

        print(f"      Exported {count:,}/{len(taxref_entries):,}    ")

    # STEP 3: Verify output
    file_size_mb = output_path.stat().st_size / (1024 * 1024)

    print("\n[3/3] Verifying output...")
    print(f"[OK] Export complete!")
    print(f"      File: {output_path}")
    print(f"      Size: {file_size_mb:.2f} MB")
    print(f"      Entries: {count:,}")

    print("\n" + "=" * 60)
    print("EXPORT COMPLETE")
    print("=" * 60)
    print("Next steps:")
    print(f"  - Compress for distribution: gzip {output_path}")
    print(f"  - Import into any DB: uv run import-taxref-tsv --file {output_path}")
    print("\nAttribution:")
    print("  TAXREF v18 - MNHN & UMS PatriNat")
    print("  License: Etalab Open License 2.0")
    print("\nNote:")
    print("  This TSV uses canonical_name as key, making it compatible with")
    print("  any GBIF-based database (full or minimal).")


def main():
    parser = argparse.ArgumentParser(
        description="Export TAXREF French names to database-agnostic TSV"
    )
    parser.add_argument(
        "--taxref",
        type=str,
        required=True,
        help="Path to TAXREF raw file (TAXREFv18.txt)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/taxref_french_names.tsv",
        help="Output TSV file path (default: data/taxref_french_names.tsv)",
    )

    args = parser.parse_args()

    taxref_path = Path(args.taxref)
    output_path = Path(args.output)

    export_taxref_to_tsv(taxref_path, output_path)


if __name__ == "__main__":
    main()
