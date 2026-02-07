#!/usr/bin/env python3
"""
FAST import of French vernacular names from TAXREF - OPTIMIZED VERSION.

This version is ~100x faster than the original by using bulk operations:
- Single query to load all GBIF taxa
- Single query to load existing French names
- In-memory matching (Python)
- Bulk insert with executemany()
- Single commit

Expected time: 2-3 minutes (vs 2-3 hours for the old version)
"""

import argparse
import csv
import re
import sys
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from daynimal.db.session import get_session
from daynimal.db.models import TaxonModel, VernacularNameModel
from sqlalchemy import text


def extract_canonical_name(scientific_name: str) -> str:
    """Extract canonical name (genus + species only)."""
    name = re.sub(r'\([^)]*\)', '', scientific_name)
    name = re.sub(r'\b\d{4}\b', '', name)
    name = re.sub(r',\s*\d+', '', name)
    name = ' '.join(name.split())
    parts = name.split()
    if len(parts) >= 2:
        return f"{parts[0]} {parts[1]}"
    return name


def load_taxref_fast(file_path: str, dry_run: bool = False):
    """Fast import with bulk operations."""
    taxref_path = Path(file_path)

    if not taxref_path.exists():
        print(f"[ERROR] File not found: {file_path}")
        sys.exit(1)

    print(f"[INFO] FAST import starting...")
    print(f"[INFO] Loading TAXREF from: {file_path}")

    session = get_session()

    # STEP 1: Parse TAXREF file (in memory)
    print("[1/6] Parsing TAXREF file...")
    taxref_animals = []

    try:
        with open(taxref_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter='\t')
            for row in reader:
                if row.get('REGNE') != 'Animalia':
                    continue
                french_name = row.get('NOM_VERN', '').strip()
                if not french_name:
                    continue
                scientific_name = row.get('LB_NOM', '').strip()
                if not scientific_name:
                    continue

                canonical = extract_canonical_name(scientific_name)
                taxref_animals.append({
                    'canonical_name': canonical,
                    'french_name': french_name,
                })

    except Exception as e:
        print(f"[ERROR] Failed to parse TAXREF: {e}")
        sys.exit(1)

    print(f"[OK] Found {len(taxref_animals):,} animal taxa with French names")

    # STEP 2: Load ALL GBIF species in ONE query
    print("[2/6] Loading GBIF species database (single query)...")

    gbif_species = {}
    result = session.execute(text("""
        SELECT taxon_id, canonical_name, scientific_name
        FROM taxa
        WHERE rank = 'species'
    """))

    for row in result:
        taxon_id, canonical, scientific = row
        if canonical:
            gbif_species[canonical.lower()] = taxon_id
        # Also index by first part of scientific name for LIKE matching
        if scientific:
            canon_from_sci = extract_canonical_name(scientific).lower()
            if canon_from_sci and canon_from_sci not in gbif_species:
                gbif_species[canon_from_sci] = taxon_id

    print(f"[OK] Loaded {len(gbif_species):,} GBIF species")

    # STEP 3: Load ALL existing French names in ONE query
    print("[3/6] Loading existing French names (single query)...")

    existing_names = set()
    result = session.execute(text("""
        SELECT taxon_id, name
        FROM vernacular_names
        WHERE language = 'fr'
    """))

    for taxon_id, name in result:
        existing_names.add((taxon_id, name))

    print(f"[OK] Found {len(existing_names):,} existing French names")

    # STEP 4: Match in Python (in-memory, very fast)
    print("[4/6] Matching TAXREF with GBIF (in-memory)...")

    to_insert = []
    added_count = 0
    skipped_count = 0
    no_match_count = 0

    for idx, entry in enumerate(taxref_animals):
        if idx > 0 and idx % 10000 == 0:
            print(f"      Processed {idx:,}/{len(taxref_animals):,}...")

        canonical = entry['canonical_name'].lower()
        french_name = entry['french_name']

        # Find taxon_id
        taxon_id = gbif_species.get(canonical)
        if not taxon_id:
            no_match_count += 1
            continue

        # Check if already exists
        if (taxon_id, french_name) in existing_names:
            skipped_count += 1
            continue

        # Add to insert list
        to_insert.append({
            'taxon_id': taxon_id,
            'name': french_name,
            'language': 'fr',
        })
        added_count += 1

        # Show first 20 as examples
        if added_count <= 20:
            print(f"[OK] Will add: {canonical} -> {french_name}")

    print(f"[OK] Matching complete: {added_count:,} to add, {skipped_count:,} skipped, {no_match_count:,} no match")

    if not to_insert:
        print("[INFO] Nothing to add!")
        return

    # STEP 5: Bulk insert with executemany (FAST!)
    if not dry_run:
        print(f"[5/6] Bulk inserting {len(to_insert):,} names...")

        # Split into batches of 10000 for safety
        batch_size = 10000
        for i in range(0, len(to_insert), batch_size):
            batch = to_insert[i:i+batch_size]
            session.execute(
                text("""
                    INSERT INTO vernacular_names (taxon_id, name, language)
                    VALUES (:taxon_id, :name, :language)
                """),
                batch
            )
            print(f"      Inserted batch {i//batch_size + 1}/{(len(to_insert)-1)//batch_size + 1}")

        # STEP 6: Single commit (FAST!)
        print("[6/6] Committing changes...")
        session.commit()

        print(f"\n[SUCCESS] Added {added_count:,} French names!")
        print(f"[INFO] Skipped {skipped_count:,} (already existed)")
        print(f"[INFO] No match for {no_match_count:,} TAXREF taxa")

        print("\n[IMPORTANT] Don't forget to rebuild the FTS5 search index:")
        print("    uv run init-fts")

    else:
        print(f"\n[DRY RUN] Would add {added_count:,} French names")
        print(f"[INFO] Would skip {skipped_count:,} (already exist)")
        print(f"[INFO] No match for {no_match_count:,} TAXREF taxa")

    session.close()


def main():
    parser = argparse.ArgumentParser(
        description="FAST import of French names from TAXREF (optimized version)"
    )
    parser.add_argument('--file', type=str, required=True, help='Path to TAXREF file')
    parser.add_argument('--dry-run', action='store_true', help='Preview without changes')

    args = parser.parse_args()
    load_taxref_fast(args.file, dry_run=args.dry_run)


if __name__ == '__main__':
    main()
