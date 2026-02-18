"""
Download all PhyloPic SVG silhouettes with metadata into a zip file.

Usage:
    uv run python scripts/download_phylopic.py

Output:
    data/phylopic_dump.zip containing:
    - svgs/<uuid>.svg          (all SVG silhouettes)
    - phylopic_metadata.csv    (metadata: uuid, taxon, license, attribution, etc.)
"""

import csv
import io
import logging
import time
import zipfile
from pathlib import Path

import httpx

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

API = "https://api.phylopic.org"
IMAGES_URL = f"{API}/images"
OUTPUT_ZIP = Path("data/phylopic_dump.zip")

# Rate limiting: be polite to the API
REQUEST_DELAY = 0.05  # 50ms between requests


def fetch_json(
    client: httpx.Client, url: str, params: dict | None = None
) -> dict | None:
    """Fetch JSON from URL with retry on 429/503."""
    for attempt in range(3):
        try:
            resp = client.get(url, params=params)
            if resp.status_code == 429:
                wait = float(resp.headers.get("Retry-After", 5))
                logger.warning(f"Rate limited, waiting {wait}s...")
                time.sleep(wait)
                continue
            if resp.status_code == 503:
                time.sleep(2**attempt)
                continue
            if not resp.is_success:
                logger.warning(f"HTTP {resp.status_code} for {url}")
                return None
            return resp.json()
        except httpx.HTTPError as e:
            logger.warning(f"HTTP error: {e}")
            time.sleep(2**attempt)
    return None


def fetch_svg(client: httpx.Client, url: str) -> bytes | None:
    """Download SVG content."""
    for attempt in range(3):
        try:
            resp = client.get(url)
            if resp.status_code == 429:
                wait = float(resp.headers.get("Retry-After", 5))
                time.sleep(wait)
                continue
            if not resp.is_success:
                return None
            return resp.content
        except httpx.HTTPError:
            time.sleep(2**attempt)
    return None


def get_build_number(client: httpx.Client) -> int:
    """Get current PhyloPic build number."""
    data = fetch_json(client, API)
    if data:
        return data.get("build", 0)
    return 0


def iter_all_images(client: httpx.Client, build: int):
    """Iterate over all images, page by page, yielding each image item."""
    # Get total from list endpoint (without embed)
    list_data = fetch_json(client, IMAGES_URL, {"build": build})
    total_items = list_data.get("totalItems", 0) if list_data else 0
    total_pages = list_data.get("totalPages", 0) if list_data else 0
    logger.info(f"Total images: {total_items}, pages: {total_pages}")

    # First page with embedded items
    params = {"build": build, "embed_items": "true", "page": "0"}
    data = fetch_json(client, IMAGES_URL, params)
    if not data:
        logger.error("Failed to fetch first page")
        return

    # Yield items from first page
    for item in data.get("_embedded", {}).get("items", []):
        yield item

    # Remaining pages
    for page in range(1, total_pages):
        if page % 25 == 0:
            logger.info(f"Page {page}/{total_pages}")
        time.sleep(REQUEST_DELAY)
        params["page"] = str(page)
        data = fetch_json(client, IMAGES_URL, params)
        if not data:
            logger.warning(f"Failed page {page}, skipping")
            continue
        for item in data.get("_embedded", {}).get("items", []):
            yield item


def extract_metadata(item: dict) -> dict:
    """Extract metadata from an image item."""
    links = item.get("_links", {})

    uuid = item.get("uuid", "")
    attribution = item.get("attribution") or ""
    license_url = links.get("license", {}).get("href", "")

    # Taxon names from specificNode and generalNode
    specific = links.get("specificNode") or {}
    general = links.get("generalNode") or {}
    specific_name = specific.get("title", "")
    general_name = general.get("title", "")

    # SVG source URL
    source_file = links.get("sourceFile", {})
    svg_url = source_file.get("href", "")
    svg_sizes = source_file.get("sizes", "")

    # Vector file (usually smaller/optimized)
    vector_file = links.get("vectorFile", {})
    vector_url = vector_file.get("href", "")

    return {
        "uuid": uuid,
        "specific_node": specific_name,
        "general_node": general_name,
        "license_url": license_url,
        "attribution": attribution,
        "svg_source_url": svg_url,
        "svg_source_sizes": svg_sizes,
        "svg_vector_url": vector_url,
        "created": item.get("created", ""),
    }


def main():
    OUTPUT_ZIP.parent.mkdir(parents=True, exist_ok=True)

    client = httpx.Client(
        timeout=30,
        follow_redirects=True,
        headers={"User-Agent": "Daynimal/1.0 (https://github.com/notoraptor/daynimal)"},
    )

    try:
        build = get_build_number(client)
        logger.info(f"PhyloPic build: {build}")

        all_metadata = []
        svg_data = {}  # uuid -> bytes
        errors = 0

        for i, item in enumerate(iter_all_images(client, build)):
            meta = extract_metadata(item)
            all_metadata.append(meta)

            # Download SVG (prefer vector, fallback to source)
            svg_url = meta["svg_vector_url"] or meta["svg_source_url"]
            if svg_url:
                time.sleep(REQUEST_DELAY)
                svg_bytes = fetch_svg(client, svg_url)
                if svg_bytes:
                    svg_data[meta["uuid"]] = svg_bytes
                else:
                    errors += 1
                    logger.warning(f"Failed to download SVG for {meta['uuid']}")
            else:
                errors += 1

            if (i + 1) % 100 == 0:
                total_svg_mb = sum(len(b) for b in svg_data.values()) / (1024 * 1024)
                logger.info(
                    f"Progress: {i + 1} images processed, "
                    f"{len(svg_data)} SVGs downloaded ({total_svg_mb:.1f} MB), "
                    f"{errors} errors"
                )

        # Write zip
        logger.info(f"Writing zip with {len(svg_data)} SVGs and metadata...")
        with zipfile.ZipFile(OUTPUT_ZIP, "w", zipfile.ZIP_DEFLATED) as zf:
            # Write CSV metadata
            csv_buffer = io.StringIO()
            writer = csv.DictWriter(
                csv_buffer,
                fieldnames=[
                    "uuid",
                    "specific_node",
                    "general_node",
                    "license_url",
                    "attribution",
                    "svg_source_url",
                    "svg_source_sizes",
                    "svg_vector_url",
                    "created",
                ],
            )
            writer.writeheader()
            writer.writerows(all_metadata)
            zf.writestr("phylopic_metadata.csv", csv_buffer.getvalue())

            # Write SVGs
            for uuid, data in svg_data.items():
                zf.writestr(f"svgs/{uuid}.svg", data)

        final_size = OUTPUT_ZIP.stat().st_size / (1024 * 1024)
        logger.info(f"Done! {OUTPUT_ZIP} — {final_size:.1f} MB")
        logger.info(
            f"  {len(all_metadata)} images total, {len(svg_data)} SVGs, {errors} errors"
        )

    finally:
        client.close()


if __name__ == "__main__":
    main()
