"""
Generate distribution TSV files from raw sources (GBIF + TAXREF).

This script produces ready-to-import TSV files that can be used by build_db.py
to construct a SQLite database. It supports two modes:

  - full: All Animalia kingdom taxa (all ranks)
  - minimal: Species with vernacular names only

When --taxref is provided, French names from TAXREF are merged into the
vernacular TSV, enriching the distribution with ~49K additional French names.

Usage:
    # Minimal distribution with TAXREF French names
    uv run generate-distribution --mode minimal --taxref data/TAXREFv18.txt

    # Full distribution without TAXREF
    uv run generate-distribution --mode full

    # With pre-downloaded backbone
    uv run generate-distribution --mode minimal --backbone data/backbone.zip
"""

import csv
import io
import zipfile
from pathlib import Path

from daynimal.db.import_gbif_utils import (
    TAXON_COLUMNS,
    VERNACULAR_COLUMNS,
    download_backbone,
    extract_canonical_name,
    parse_int,
)


def extract_and_filter_taxa(
    zip_path: Path, output_path: Path, mode: str = "full"
) -> tuple[int, set[int]]:
    """
    Extract taxa from GBIF ZIP and create a filtered TSV file.

    Args:
        zip_path: Path to GBIF backbone ZIP file
        output_path: Path for output TSV file
        mode: 'full' (all Animalia) or 'minimal' (species only)

    Returns:
        Tuple of (count of taxa extracted, set of taxon IDs).
    """
    print(f"Extracting and filtering taxa to {output_path} (mode: {mode})...")

    count = 0
    taxon_ids = set()

    with zipfile.ZipFile(zip_path, "r") as zf:
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
                if kingdom != "Animalia":
                    continue

                rank = row[TAXON_COLUMNS["taxonRank"]].lower() or ""

                if mode == "minimal" and rank != "species":
                    continue

                taxon_id = row[TAXON_COLUMNS["taxonID"]]
                scientific_name = row[TAXON_COLUMNS["scientificName"]]
                canonical_name = row[TAXON_COLUMNS["canonicalName"]] or ""
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

                writer.writerow(
                    [
                        taxon_id,
                        scientific_name,
                        canonical_name,
                        rank,
                        kingdom,
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

                taxon_ids.add(int(taxon_id))
                count += 1
                if count % 100000 == 0:
                    print(f"\rExtracted: {count:,} taxa...", end="", flush=True)

    print(f"\nExtraction complete: {count:,} Animalia taxa extracted.")
    return count, taxon_ids


def extract_and_filter_vernacular(
    zip_path: Path, output_path: Path, valid_taxon_ids: set[int]
) -> int:
    """
    Extract vernacular names from GBIF ZIP and create a filtered TSV file.
    Only includes names for taxa in valid_taxon_ids.

    Returns the number of names extracted.
    """
    print(f"Extracting and filtering vernacular names to {output_path}...")

    count = 0

    with zipfile.ZipFile(zip_path, "r") as zf:
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


def build_canonical_to_taxon_ids(taxa_tsv: Path) -> dict[str, int]:
    """Build a mapping from lowercase canonical_name to taxon_id from the taxa TSV."""
    print("Building canonical_name -> taxon_id mapping from taxa TSV...")
    mapping = {}
    with open(taxa_tsv, "r", encoding="utf-8") as f:
        reader = csv.reader(f, delimiter="\t", quoting=csv.QUOTE_NONE)
        for row in reader:
            if len(row) != 13:
                continue
            taxon_id = int(row[0])
            canonical_name = row[2]
            if canonical_name:
                mapping[canonical_name.lower()] = taxon_id
    print(f"Mapped {len(mapping):,} canonical names to taxon IDs.")
    return mapping


def _split_vernacular_names(text: str) -> list[str]:
    """Split a comma-separated list of vernacular names, respecting parentheses.

    TAXREF stores multiple vernacular names in a single NOM_VERN field separated
    by commas.  Commas inside parentheses are part of the name and must NOT be
    used as separators (e.g. "Rapaces nocturnes (Chouettes, Hiboux)").

    Args:
        text: Raw NOM_VERN value from TAXREF.

    Returns:
        List of individual vernacular names, stripped and non-empty.
    """
    names: list[str] = []
    current: list[str] = []
    depth = 0
    for ch in text:
        if ch == "(":
            depth += 1
            current.append(ch)
        elif ch == ")":
            depth = max(depth - 1, 0)
            current.append(ch)
        elif ch == "," and depth == 0:
            name = "".join(current).strip()
            if name:
                names.append(name)
            current = []
        else:
            current.append(ch)
    # Last segment
    name = "".join(current).strip()
    if name:
        names.append(name)
    return names


def parse_taxref_french_names(taxref_path: Path) -> list[dict]:
    """
    Parse TAXREF file and extract unique French vernacular names for Animalia.

    Returns list of dicts with keys: canonical_name, french_name.
    """
    print(f"Parsing TAXREF file: {taxref_path}...")
    entries = []
    seen = set()

    with open(taxref_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            if row.get("REGNE") != "Animalia":
                continue

            raw_names = row.get("NOM_VERN", "").strip()
            if not raw_names:
                continue

            scientific_name = row.get("LB_NOM", "").strip()
            if not scientific_name:
                continue

            canonical = extract_canonical_name(scientific_name)

            for french_name in _split_vernacular_names(raw_names):
                key = (canonical.lower(), french_name.lower())
                if key in seen:
                    continue

                seen.add(key)
                entries.append(
                    {"canonical_name": canonical, "french_name": french_name}
                )

    print(f"Found {len(entries):,} unique TAXREF French name entries.")
    return entries


def merge_taxref_into_vernacular(
    vernacular_tsv: Path, taxref_entries: list[dict], canonical_to_id: dict[str, int]
) -> tuple[int, int]:
    """
    Append TAXREF French names to the vernacular TSV, avoiding duplicates.

    Args:
        vernacular_tsv: Path to the existing vernacular TSV to append to
        taxref_entries: Parsed TAXREF entries
        canonical_to_id: Mapping from canonical_name to taxon_id

    Returns:
        Tuple of (added_count, no_match_count).
    """
    print("Merging TAXREF French names into vernacular TSV...")

    # Load existing entries for dedup
    existing = set()
    with open(vernacular_tsv, "r", encoding="utf-8") as f:
        reader = csv.reader(f, delimiter="\t", quoting=csv.QUOTE_NONE)
        for row in reader:
            if len(row) == 3:
                existing.add((row[0], row[1].lower()))

    added = 0
    no_match = 0

    with open(vernacular_tsv, "a", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, delimiter="\t", quoting=csv.QUOTE_NONE, escapechar="\\")

        for entry in taxref_entries:
            canonical = entry["canonical_name"]
            french_name = entry["french_name"]

            taxon_id = canonical_to_id.get(canonical.lower())
            if not taxon_id:
                no_match += 1
                continue

            # Dedup: check (taxon_id_str, lowercase name)
            if (str(taxon_id), french_name.lower()) in existing:
                continue

            writer.writerow([taxon_id, french_name, "fr"])
            existing.add((str(taxon_id), french_name.lower()))
            added += 1

    print(f"TAXREF merge: {added:,} names added, {no_match:,} unmatched.")
    return added, no_match


def cleanup_taxa_without_vernacular(
    taxa_tsv: Path, vernacular_tsv: Path, output_taxa_tsv: Path
) -> tuple[int, int]:
    """
    Filter taxa TSV to keep only taxa that have at least one vernacular name.
    Used in minimal mode.

    Args:
        taxa_tsv: Input taxa TSV
        vernacular_tsv: Vernacular TSV (to read taxon IDs with names)
        output_taxa_tsv: Output filtered taxa TSV

    Returns:
        Tuple of (kept_count, removed_count).
    """
    print("Filtering taxa to keep only those with vernacular names...")

    # Collect taxon IDs that have vernacular names
    ids_with_names = set()
    with open(vernacular_tsv, "r", encoding="utf-8") as f:
        reader = csv.reader(f, delimiter="\t", quoting=csv.QUOTE_NONE)
        for row in reader:
            if len(row) >= 1:
                tid = parse_int(row[0])
                if tid is not None:
                    ids_with_names.add(tid)

    print(f"Found {len(ids_with_names):,} taxon IDs with vernacular names.")

    kept = 0
    removed = 0
    with (
        open(taxa_tsv, "r", encoding="utf-8") as f_in,
        open(output_taxa_tsv, "w", encoding="utf-8", newline="") as f_out,
    ):
        reader = csv.reader(f_in, delimiter="\t", quoting=csv.QUOTE_NONE)
        writer = csv.writer(
            f_out, delimiter="\t", quoting=csv.QUOTE_NONE, escapechar="\\"
        )

        for row in reader:
            if len(row) != 13:
                continue
            taxon_id = int(row[0])
            if taxon_id in ids_with_names:
                writer.writerow(row)
                kept += 1
            else:
                removed += 1

    print(f"Cleanup: kept {kept:,} taxa, removed {removed:,} without names.")
    return kept, removed


def generate_distribution(
    mode: str, backbone_path: Path | None, taxref_path: Path | None, output_dir: Path
):
    """Main logic for generating distribution TSV files."""
    print("=" * 60)
    print("GENERATE DISTRIBUTION TSV FILES")
    print(f"Mode: {mode.upper()}")
    if taxref_path:
        print(f"TAXREF: {taxref_path}")
    else:
        print("TAXREF: not provided")
    print(f"Output: {output_dir}")
    print("=" * 60)

    output_dir.mkdir(parents=True, exist_ok=True)

    # Step 1: Locate backbone.zip
    if backbone_path:
        zip_path = backbone_path
        if not zip_path.exists():
            raise FileNotFoundError(f"Backbone file not found: {zip_path}")
        print(f"Using backbone: {zip_path}")
    else:
        zip_path = output_dir / "backbone.zip"
        if not zip_path.exists():
            download_backbone(zip_path)
        else:
            print(f"Using existing backbone: {zip_path}")

    # Determine output filenames
    if mode == "minimal":
        taxa_tsv = output_dir / "animalia_taxa_minimal.tsv"
        vernacular_tsv = output_dir / "animalia_vernacular_minimal.tsv"
    else:
        taxa_tsv = output_dir / "animalia_taxa.tsv"
        vernacular_tsv = output_dir / "animalia_vernacular.tsv"

    # Step 2: Extract taxa from GBIF
    print(f"\n--- Step 1: Extract taxa (mode={mode}) ---")
    taxa_count, taxon_ids = extract_and_filter_taxa(zip_path, taxa_tsv, mode=mode)

    # Step 3: Extract vernacular names from GBIF
    print("\n--- Step 2: Extract vernacular names ---")
    extract_and_filter_vernacular(zip_path, vernacular_tsv, taxon_ids)

    # Step 4: TAXREF integration
    taxref_added = 0
    taxref_no_match = 0
    if taxref_path:
        print("\n--- Step 3: Merge TAXREF French names ---")
        if not taxref_path.exists():
            print(f"[ERROR] TAXREF file not found: {taxref_path}")
            raise FileNotFoundError(f"TAXREF file not found: {taxref_path}")

        taxref_entries = parse_taxref_french_names(taxref_path)
        canonical_to_id = build_canonical_to_taxon_ids(taxa_tsv)
        taxref_added, taxref_no_match = merge_taxref_into_vernacular(
            vernacular_tsv, taxref_entries, canonical_to_id
        )
    else:
        print("\n--- Step 3: TAXREF not provided (skipped) ---")
        print(
            "WARNING: TAXREF non fourni. Les noms francais seront limites aux donnees GBIF."
        )
        print("Pour enrichir avec ~49K noms francais supplementaires :")
        print(
            "  1. Telecharger TAXREF depuis https://inpn.mnhn.fr/telechargement/referentielEspece/taxref"
        )
        print("  2. Decompresser et relancer avec --taxref data/TAXREFv18.txt")

    # Step 5: Cleanup (minimal mode only)
    if mode == "minimal":
        print("\n--- Step 4: Cleanup taxa without vernacular names ---")
        # Write to a temp file, then replace
        temp_taxa = taxa_tsv.with_suffix(".tsv.tmp")
        kept, removed = cleanup_taxa_without_vernacular(
            taxa_tsv, vernacular_tsv, temp_taxa
        )
        # Replace original with filtered version
        taxa_tsv.unlink()
        temp_taxa.rename(taxa_tsv)
        taxa_count = kept
    else:
        print("\n--- Step 4: Cleanup skipped (full mode) ---")

    # Step 6: Statistics
    # Count final vernacular names
    final_vernacular_count = 0
    fr_count = 0
    with open(vernacular_tsv, "r", encoding="utf-8") as f:
        reader = csv.reader(f, delimiter="\t", quoting=csv.QUOTE_NONE)
        for row in reader:
            if len(row) == 3:
                final_vernacular_count += 1
                if row[2] == "fr":
                    fr_count += 1

    print("\n" + "=" * 60)
    print("DISTRIBUTION STATISTICS")
    print("=" * 60)
    print(f"Mode:               {mode.upper()}")
    print(f"Taxa:               {taxa_count:,}")
    print(f"Vernacular names:   {final_vernacular_count:,}")
    print(f"  French names:     {fr_count:,}")
    if taxref_path:
        print(f"  (from TAXREF):    {taxref_added:,}")
        print(f"  (TAXREF no match):{taxref_no_match:,}")
    print("\nOutput files:")
    print(f"  Taxa:       {taxa_tsv}")
    print(f"  Vernacular: {vernacular_tsv}")

    taxa_size = taxa_tsv.stat().st_size / (1024 * 1024)
    vern_size = vernacular_tsv.stat().st_size / (1024 * 1024)
    print(f"  Taxa size:       {taxa_size:.1f} MB")
    print(f"  Vernacular size: {vern_size:.1f} MB")

    print("\n" + "=" * 60)
    print("GENERATION COMPLETE!")
    print("=" * 60)
    print("Next steps:")
    print(f"  uv run build-db --taxa {taxa_tsv} --vernacular {vernacular_tsv}")
    print("  uv run init-fts")
    print("\nFor mobile distribution:")
    print(f"  gzip {taxa_tsv}")
    print(f"  gzip {vernacular_tsv}")
    print("\nAttribution:")
    print("  GBIF Backbone Taxonomy. GBIF Secretariat (2024). CC-BY 4.0")
    if taxref_path:
        print("  TAXREF v18 - MNHN & UMS PatriNat. Etalab Open License 2.0")


def main():
    """Main entry point for generate-distribution."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate distribution TSV files from GBIF (+ optional TAXREF)"
    )
    parser.add_argument(
        "--mode",
        choices=["full", "minimal"],
        required=True,
        help="Generation mode: 'full' (all Animalia) or 'minimal' (species with vernacular names)",
    )
    parser.add_argument(
        "--backbone",
        type=str,
        default=None,
        help="Path to backbone.zip (downloaded automatically if not provided)",
    )
    parser.add_argument(
        "--taxref",
        type=str,
        default=None,
        help="Path to TAXREF file (TAXREFv18.txt) for French names enrichment",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/",
        help="Output directory for TSV files (default: data/)",
    )

    args = parser.parse_args()

    generate_distribution(
        mode=args.mode,
        backbone_path=Path(args.backbone) if args.backbone else None,
        taxref_path=Path(args.taxref) if args.taxref else None,
        output_dir=Path(args.output_dir),
    )


if __name__ == "__main__":
    main()
