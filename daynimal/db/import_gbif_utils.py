"""
GBIF Backbone Taxonomy - Shared utilities for import scripts.

This module contains common functions and constants used by both
the standard and fast GBIF importers.
"""

import re
from pathlib import Path

import httpx

# GBIF Backbone download URL
GBIF_BACKBONE_URL = (
    "https://hosted-datasets.gbif.org/datasets/backbone/current/backbone.zip"
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


def extract_canonical_name(scientific_name: str) -> str:
    """Extract canonical name (genus + species only) from a scientific name.

    Removes parenthetical authorities, year citations, and extra parts,
    keeping only the first two words (genus + specific epithet).
    """
    name = re.sub(r"\([^)]*\)", "", scientific_name)
    name = re.sub(r"\b\d{4}\b", "", name)
    name = re.sub(r",\s*\d+", "", name)
    name = " ".join(name.split())
    parts = name.split()
    if len(parts) >= 2:
        return f"{parts[0]} {parts[1]}"
    return name


def parse_int(value: str) -> int | None:
    """Parse integer, returning None for empty strings."""
    if value and value.strip():
        try:
            return int(value)
        except ValueError:
            return None
    return None
