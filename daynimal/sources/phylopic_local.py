"""
Local PhyloPic lookup service.

Replaces the PhyloPic API client with a local CSV-based lookup.
The CSV contains ~11,950 silhouette metadata entries downloaded from PhyloPic.
Taxonomy traversal is done locally using the Taxon hierarchy fields.
"""

import csv
import logging
from pathlib import Path

from daynimal.schemas import CommonsImage, ImageSource, License, Taxon

# Mapping of PhyloPic license URLs to License enum
_PHYLOPIC_LICENSE_MAP = {
    "publicdomain/zero": License.CC0,
    "publicdomain/mark": License.PUBLIC_DOMAIN,
    "/by/": License.CC_BY,
    "/by-sa/": License.CC_BY_SA,
}

# Patterns indicating non-commercial licenses
_REJECTED_PATTERNS = ("-nc", "-nd")


def _parse_phylopic_license(license_url: str | None) -> License | None:
    """Parse a PhyloPic license URL to a License enum."""
    if not license_url:
        return None
    url_lower = license_url.lower()
    for pattern in _REJECTED_PATTERNS:
        if pattern in url_lower:
            return None
    for key, license_value in _PHYLOPIC_LICENSE_MAP.items():
        if key in url_lower:
            return license_value
    return None

logger = logging.getLogger(__name__)

# Taxonomy fields to try, in order (species → genus → family → order → class → phylum)
_TAXON_HIERARCHY = ["genus", "family", "order", "class_", "phylum"]


def _load_csv() -> tuple[dict[str, dict], dict[str, dict]]:
    """
    Load PhyloPic metadata CSV into two dicts.

    Returns:
        Tuple of (specific_lookup, general_lookup):
        - specific_lookup: keyed by specific_node name (most precise match)
        - general_lookup: keyed by general_node name (broader match, fallback)
        If multiple images match the same name, the first one wins.
    """
    csv_path = Path(__file__).resolve().parent.parent / "resources" / "phylopic_metadata.csv"

    specific: dict[str, dict] = {}
    general: dict[str, dict] = {}
    with open(csv_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            sn = row.get("specific_node", "").strip()
            if sn:
                key = sn.lower()
                if key not in specific:
                    specific[key] = row

            gn = row.get("general_node", "").strip()
            if gn:
                key = gn.lower()
                if key not in general:
                    general[key] = row

    logger.info(
        f"PhyloPic local: loaded {len(specific)} specific + {len(general)} general entries"
    )
    return specific, general


# Module-level singletons (loaded once on first access)
_specific_lookup: dict[str, dict] | None = None
_general_lookup: dict[str, dict] | None = None


def _get_lookups() -> tuple[dict[str, dict], dict[str, dict]]:
    """Get or initialize the lookup dicts (lazy singleton)."""
    global _specific_lookup, _general_lookup
    if _specific_lookup is None:
        _specific_lookup, _general_lookup = _load_csv()
    return _specific_lookup, _general_lookup


def _row_to_image(row: dict) -> CommonsImage | None:
    """Convert a CSV row to a CommonsImage, or None if license is rejected."""
    license_url = row.get("license_url", "")
    parsed_license = _parse_phylopic_license(license_url)
    if parsed_license is None:
        return None

    uuid = row.get("uuid", "")
    svg_url = row.get("svg_vector_url") or row.get("svg_source_url", "")
    if not svg_url:
        return None

    attribution = row.get("attribution") or None
    source_page_url = f"https://www.phylopic.org/images/{uuid}"

    return CommonsImage(
        filename=f"phylopic_{uuid[:8]}.svg",
        url=svg_url,
        thumbnail_url=svg_url,
        author=attribution,
        license=parsed_license,
        attribution_required=parsed_license not in (License.CC0, License.PUBLIC_DOMAIN),
        description="Silhouette via PhyloPic",
        image_source=ImageSource.PHYLOPIC,
        source_page_url=source_page_url,
        mime_type="image/svg+xml",
    )


def _find_in_lookups(key: str, specific: dict, general: dict) -> CommonsImage | None:
    """Try to find a valid image for a key, preferring specific over general."""
    if key in specific:
        img = _row_to_image(specific[key])
        if img:
            return img
    if key in general:
        img = _row_to_image(general[key])
        if img:
            return img
    return None


def get_silhouette_for_taxon(taxon: Taxon) -> CommonsImage | None:
    """
    Look up a PhyloPic silhouette for the given taxon.

    Tries exact species match first (in specific_node, then general_node),
    then traverses up the taxonomy: genus → family → order → class → phylum.

    Args:
        taxon: Taxon with canonical_name and hierarchy fields.

    Returns:
        CommonsImage with SVG URL, or None if not found.
    """
    specific, general = _get_lookups()

    # 1. Try exact species name
    name = (taxon.canonical_name or taxon.scientific_name).strip().lower()
    img = _find_in_lookups(name, specific, general)
    if img:
        return img

    # 2. Traverse up taxonomy
    for field in _TAXON_HIERARCHY:
        value = getattr(taxon, field, None)
        if value:
            key = value.strip().lower()
            img = _find_in_lookups(key, specific, general)
            if img:
                return img

    return None
