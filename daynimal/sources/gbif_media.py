"""
GBIF Media API client.

Fetches images from GBIF's species media endpoint as a fallback
when Wikimedia Commons has no images for a species.

Only images with commercial-use-compatible licenses are returned:
CC0, CC-BY, CC-BY-SA, Public Domain. Images with NC or ND clauses
are rejected.
"""

import logging
import re

from daynimal.schemas import CommonsImage, ImageSource, License
from daynimal.sources.base import DataSource

logger = logging.getLogger(__name__)

# GBIF API endpoint
GBIF_API = "https://api.gbif.org/v1"

# Mapping of GBIF license URLs to License enum
# GBIF returns licenses as full URLs like "http://creativecommons.org/licenses/by/4.0/"
_GBIF_LICENSE_MAP = {
    "publicdomain/zero": License.CC0,
    "publicdomain/mark": License.PUBLIC_DOMAIN,
    "/cc0": License.CC0,
    "by-sa/": License.CC_BY_SA,
    "by/": License.CC_BY,
}

# Patterns that indicate non-commercial licenses (must be rejected)
_REJECTED_LICENSE_PATTERNS = ("by-nc", "by-nd", "by-nc-sa", "by-nc-nd")


def _parse_gbif_license(license_url: str | None) -> License | None:
    """
    Parse a GBIF license URL to a License enum.

    Args:
        license_url: License URL from GBIF API (e.g. "http://creativecommons.org/licenses/by/4.0/")

    Returns:
        License enum value, or None if not commercial-use-compatible
    """
    if not license_url:
        return None

    url_lower = license_url.lower()

    # Reject non-commercial / non-derivative licenses
    for pattern in _REJECTED_LICENSE_PATTERNS:
        if pattern in url_lower:
            return None

    # Match known commercial licenses
    for key, license_value in _GBIF_LICENSE_MAP.items():
        if key in url_lower:
            return license_value

    # Unknown license — reject to be safe
    return None


class GbifMediaAPI(DataSource[CommonsImage]):
    """
    Client for GBIF Media API.

    Fetches species images from GBIF's occurrence media.
    Only returns images with commercial-use-compatible licenses.
    """

    @property
    def source_name(self) -> str:
        return "gbif_media"

    @property
    def license(self) -> str:
        return "varies (CC0, CC-BY, CC-BY-SA)"

    def get_by_source_id(self, source_id: str) -> CommonsImage | None:
        """Not applicable for GBIF Media — use get_media_for_taxon instead."""
        return None

    def get_by_taxonomy(self, scientific_name: str) -> CommonsImage | None:
        """Not applicable — use get_media_for_taxon with a taxon key."""
        return None

    def search(self, query: str, limit: int = 10) -> list[CommonsImage]:
        """Not applicable — use get_media_for_taxon with a taxon key."""
        return []

    def get_media_for_taxon(self, taxon_key: int, limit: int = 5) -> list[CommonsImage]:
        """
        Fetch images for a GBIF taxon, filtering for commercial-use licenses.

        Over-fetches (20 items) to compensate for license filtering.

        Args:
            taxon_key: GBIF taxon key (species ID)
            limit: Maximum number of images to return

        Returns:
            List of CommonsImage with image_source=GBIF
        """
        # Over-fetch to compensate for filtering
        fetch_limit = max(limit * 4, 20)

        url = f"{GBIF_API}/species/{taxon_key}/media"
        params = {"limit": fetch_limit}

        response = self._request_with_retry("get", url, params=params)
        if response is None or not response.is_success:
            return []

        data = response.json()
        results = data.get("results", [])

        images = []
        for item in results:
            image = self._parse_media_item(item)
            if image:
                images.append(image)
                if len(images) >= limit:
                    break

        return images

    def _parse_media_item(self, item: dict) -> CommonsImage | None:
        """
        Parse a GBIF media item to a CommonsImage.

        Filters for StillImage type and commercial-use licenses only.
        """
        # Only accept still images
        media_type = item.get("type", "")
        if media_type != "StillImage":
            return None

        # Get image URL
        url = item.get("identifier", "")
        if not url:
            return None

        # Parse and filter license
        license_url = item.get("license", "")
        parsed_license = _parse_gbif_license(license_url)
        if parsed_license is None:
            return None

        # Extract metadata
        author = item.get("rightsHolder") or item.get("creator") or None
        # Clean HTML tags from author if present
        if author:
            author = re.sub(r"<[^>]+>", "", author).strip()

        description = item.get("description") or item.get("title") or None

        # Build source page URL (link to GBIF occurrence if available)
        source_url = item.get("references") or None

        # Extract filename from URL
        filename = url.rsplit("/", 1)[-1] if "/" in url else url
        # Truncate very long filenames
        if len(filename) > 100:
            filename = filename[:97] + "..."

        return CommonsImage(
            filename=filename,
            url=url,
            thumbnail_url=None,  # GBIF doesn't provide thumbnails
            author=author,
            license=parsed_license,
            attribution_required=parsed_license
            not in (License.CC0, License.PUBLIC_DOMAIN),
            description=description,
            image_source=ImageSource.GBIF,
            source_page_url=source_url,
        )
