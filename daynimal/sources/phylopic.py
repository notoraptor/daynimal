"""
PhyloPic API client.

Fetches silhouette images from PhyloPic (https://www.phylopic.org/)
as a last-resort fallback when no photos are available.

PhyloPic provides free silhouette images of organisms, organized by
phylogenetic taxonomy. When no image exists for the exact species,
we traverse up the GBIF taxonomy (genus → family → order → class)
to find the closest available silhouette.

Only images with commercial-use-compatible licenses are returned.
"""

import logging

import httpx

from daynimal.config import settings
from daynimal.schemas import CommonsImage, ImageSource, License
from daynimal.sources.base import DataSource

logger = logging.getLogger(__name__)

# PhyloPic API endpoint
PHYLOPIC_API = "https://api.phylopic.org"

# GBIF API for fetching parent taxon keys
GBIF_SPECIES_API = "https://api.gbif.org/v1/species"

# Mapping of PhyloPic license URLs to License enum
_PHYLOPIC_LICENSE_MAP = {
    "publicdomain/zero": License.CC0,
    "publicdomain/mark": License.PUBLIC_DOMAIN,
    "/by/": License.CC_BY,
    "/by-sa/": License.CC_BY_SA,
}

# Patterns indicating non-commercial licenses
_REJECTED_PATTERNS = ("-nc", "-nd")

# Parent key fields to try, in order (genus → family → order → class → phylum)
_PARENT_KEY_FIELDS = ["genusKey", "familyKey", "orderKey", "classKey", "phylumKey"]


def _parse_phylopic_license(license_url: str | None) -> License | None:
    """
    Parse a PhyloPic license URL to a License enum.

    Args:
        license_url: License URL (e.g. "https://creativecommons.org/licenses/by/4.0/")

    Returns:
        License enum value, or None if not commercial-use-compatible
    """
    if not license_url:
        return None

    url_lower = license_url.lower()

    # Reject non-commercial / non-derivative
    for pattern in _REJECTED_PATTERNS:
        if pattern in url_lower:
            return None

    # Match known licenses
    for key, license_value in _PHYLOPIC_LICENSE_MAP.items():
        if key in url_lower:
            return license_value

    return None


class PhyloPicAPI(DataSource[CommonsImage]):
    """
    Client for PhyloPic API.

    Fetches silhouette images via GBIF key resolution.
    Traverses GBIF taxonomy upward (species → genus → family → ...)
    to find the closest available silhouette.
    """

    @property
    def client(self) -> httpx.Client:
        """Lazy-initialized HTTP client with redirect support."""
        if self._client is None:
            self._client = httpx.Client(
                timeout=settings.httpx_timeout,
                follow_redirects=True,
                headers={
                    "User-Agent": "Daynimal/1.0 (https://github.com/notoraptor/daynimal)"
                },
            )
        return self._client

    @property
    def source_name(self) -> str:
        return "phylopic"

    @property
    def license(self) -> str:
        return "varies (CC0, CC-BY, CC-BY-SA)"

    def get_by_source_id(self, source_id: str) -> CommonsImage | None:
        """Not applicable — use get_silhouettes_for_taxon instead."""
        return None

    def get_by_taxonomy(self, scientific_name: str) -> CommonsImage | None:
        """Not applicable — use get_silhouettes_for_taxon with a GBIF key."""
        return None

    def search(self, query: str, limit: int = 10) -> list[CommonsImage]:
        """Not applicable — use get_silhouettes_for_taxon with a GBIF key."""
        return []

    def get_silhouettes_for_taxon(
        self, gbif_key: int, limit: int = 1
    ) -> list[CommonsImage]:
        """
        Fetch silhouette images for a GBIF taxon key.

        Tries the exact species key first. If PhyloPic doesn't have it,
        fetches parent taxon keys from GBIF and tries each level
        (genus → family → order → class → phylum) until a silhouette is found.

        Args:
            gbif_key: GBIF taxon key
            limit: Maximum number of silhouettes (usually 1)

        Returns:
            List of CommonsImage with image_source=PHYLOPIC
        """
        # Try exact species key first
        image = self._try_resolve_and_get_image(gbif_key)
        if image:
            return [image]

        # Fetch parent keys from GBIF and traverse upward
        parent_keys = self._get_parent_keys(gbif_key)
        for key in parent_keys:
            if key and key != gbif_key:
                image = self._try_resolve_and_get_image(key)
                if image:
                    return [image]

        return []

    def _try_resolve_and_get_image(self, gbif_key: int) -> CommonsImage | None:
        """Try to resolve a GBIF key and get its PhyloPic image."""
        node_uuid = self._resolve_gbif_key(gbif_key)
        if not node_uuid:
            return None
        return self._get_node_image(node_uuid)

    def _get_parent_keys(self, gbif_key: int) -> list[int]:
        """
        Fetch parent taxon keys from GBIF API.

        Returns list of parent keys in order: genus, family, order, class, phylum.
        """
        url = f"{GBIF_SPECIES_API}/{gbif_key}"
        response = self._request_with_retry("get", url)
        if response is None or not response.is_success:
            return []

        data = response.json()
        keys = []
        for field in _PARENT_KEY_FIELDS:
            key = data.get(field)
            if key:
                keys.append(key)

        return keys

    def _resolve_gbif_key(self, gbif_key: int) -> str | None:
        """
        Resolve a GBIF species key to a PhyloPic node UUID.

        Args:
            gbif_key: GBIF taxon key

        Returns:
            PhyloPic node UUID, or None if not found
        """
        url = f"{PHYLOPIC_API}/resolve/gbif.org/species"
        params = {"objectIDs": str(gbif_key)}

        response = self._request_with_retry("get", url, params=params)
        if response is None or not response.is_success:
            return None

        data = response.json()

        # The resolve endpoint returns a node link
        # Response format: {"_links": {"self": {"href": "/nodes/<uuid>?build=NNN"}}}
        node_href = data.get("_links", {}).get("self", {}).get("href")
        if not node_href:
            return None

        # Extract UUID from href "/nodes/<uuid>" or "/nodes/<uuid>?build=NNN"
        # Remove query string first
        path = node_href.split("?")[0]
        parts = path.strip("/").split("/")
        if len(parts) >= 2 and parts[-2] == "nodes":
            return parts[-1]

        return None

    def _get_node_image(self, node_uuid: str) -> CommonsImage | None:
        """
        Fetch the primary image for a PhyloPic node.

        Args:
            node_uuid: PhyloPic node UUID

        Returns:
            CommonsImage or None
        """
        url = f"{PHYLOPIC_API}/nodes/{node_uuid}"
        params = {"embed_primaryImage": "true"}

        response = self._request_with_retry("get", url, params=params)
        if response is None or not response.is_success:
            return None

        data = response.json()

        # Get the embedded primary image
        embedded = data.get("_embedded", {})
        primary_image = embedded.get("primaryImage")
        if not primary_image:
            return None

        return self._parse_image(primary_image)

    def _parse_image(self, image_data: dict) -> CommonsImage | None:
        """
        Parse a PhyloPic image object to a CommonsImage.

        Args:
            image_data: PhyloPic image data dict

        Returns:
            CommonsImage or None if license is incompatible
        """
        # Get image UUID from _links.self.href
        image_href = image_data.get("_links", {}).get("self", {}).get("href", "")
        image_uuid = image_href.strip("/").split("/")[-1] if image_href else None
        if not image_uuid:
            return None

        # Remove query string from UUID if present
        image_uuid = image_uuid.split("?")[0]

        # Parse license
        license_url = image_data.get("_links", {}).get("license", {}).get("href")
        parsed_license = _parse_phylopic_license(license_url)
        if parsed_license is None:
            return None

        # Get real image URLs from rasterFiles and thumbnailFiles
        links = image_data.get("_links", {})
        raster_files = links.get("rasterFiles", [])
        thumbnail_files = links.get("thumbnailFiles", [])

        # Pick the largest raster as main image
        image_url = raster_files[0]["href"] if raster_files else None
        if not image_url:
            return None

        # Pick the largest thumbnail
        thumbnail_url = thumbnail_files[0]["href"] if thumbnail_files else None

        # Parse dimensions from the chosen raster
        width, height = None, None
        if raster_files:
            sizes = raster_files[0].get("sizes", "")
            if "x" in sizes:
                parts = sizes.split("x")
                try:
                    width, height = int(float(parts[0])), int(float(parts[1]))
                except (ValueError, IndexError):
                    pass

        # Attribution
        attribution = image_data.get("attribution") or None

        # Source page URL
        source_page_url = f"https://www.phylopic.org/images/{image_uuid}"

        filename = f"phylopic_{image_uuid[:8]}.png"

        return CommonsImage(
            filename=filename,
            url=image_url,
            thumbnail_url=thumbnail_url,
            width=width,
            height=height,
            mime_type="image/png",
            author=attribution,
            license=parsed_license,
            attribution_required=parsed_license
            not in (License.CC0, License.PUBLIC_DOMAIN),
            description="Silhouette via PhyloPic",
            image_source=ImageSource.PHYLOPIC,
            source_page_url=source_page_url,
        )
