"""
Wikimedia Commons API client.

Wikimedia Commons only accepts free content that allows commercial use.
Each image has its own license (CC-BY, CC-BY-SA, CC0, Public Domain).
https://commons.wikimedia.org/wiki/Commons:Licensing
"""

from daynimal.schemas import CommonsImage, License
from daynimal.sources.base import DataSource

# Commons API endpoint
COMMONS_API = "https://commons.wikimedia.org/w/api.php"

# License mapping from Commons templates to our License enum
LICENSE_MAP = {
    "cc0": License.CC0,
    "cc-zero": License.CC0,
    "public domain": License.PUBLIC_DOMAIN,
    "pd": License.PUBLIC_DOMAIN,
    "cc-by-4.0": License.CC_BY,
    "cc-by-3.0": License.CC_BY,
    "cc-by-2.5": License.CC_BY,
    "cc-by-2.0": License.CC_BY,
    "cc-by": License.CC_BY,
    "cc-by-sa-4.0": License.CC_BY_SA,
    "cc-by-sa-3.0": License.CC_BY_SA,
    "cc-by-sa-2.5": License.CC_BY_SA,
    "cc-by-sa-2.0": License.CC_BY_SA,
    "cc-by-sa": License.CC_BY_SA,
}


class CommonsAPI(DataSource[CommonsImage]):
    """
    Client for Wikimedia Commons API.

    License: Varies per image, but all allow commercial use.
    Only CC0, CC-BY, CC-BY-SA, and Public Domain images are on Commons.
    """

    @property
    def source_name(self) -> str:
        return "commons"

    @property
    def license(self) -> str:
        return "varies (CC0, CC-BY, CC-BY-SA, Public Domain)"

    def get_by_source_id(self, source_id: str) -> CommonsImage | None:
        """
        Fetch image info by filename.

        Args:
            source_id: Commons filename (with or without "File:" prefix)
        """
        filename = source_id
        if not filename.startswith("File:"):
            filename = f"File:{filename}"

        params = {
            "action": "query",
            "titles": filename,
            "format": "json",
            "prop": "imageinfo",
            "iiprop": "url|size|mime|extmetadata|user",
            "iiurlwidth": 800,  # Get thumbnail
        }

        response = self._request_with_retry("get", COMMONS_API, params=params)
        if response is None or not response.is_success:
            return None

        data = response.json()

        pages = data.get("query", {}).get("pages", {})
        if not pages:
            return None

        page_id, page_data = next(iter(pages.items()))

        if page_id == "-1" or "missing" in page_data:
            return None

        imageinfo = page_data.get("imageinfo", [{}])[0]
        return self._parse_image_info(filename.replace("File:", ""), imageinfo)

    def get_by_taxonomy(
        self, scientific_name: str, limit: int = 5
    ) -> list[CommonsImage]:
        """
        Find images on Commons for a species by scientific name.

        Args:
            scientific_name: Scientific name (e.g., "Canis lupus")
            limit: Maximum number of images to return
        """
        # Search in the species category
        images = self._search_category(scientific_name, limit)

        if not images:
            # Fall back to general search
            images = self.search(scientific_name, limit)

        return images

    def search(self, query: str, limit: int = 10) -> list[CommonsImage]:
        """
        Search Commons for images matching query.
        """
        params = {
            "action": "query",
            "generator": "search",
            "gsrsearch": f"filetype:bitmap {query}",
            "gsrnamespace": "6",  # File namespace
            "gsrlimit": limit,
            "format": "json",
            "prop": "imageinfo",
            "iiprop": "url|size|mime|extmetadata|user",
            "iiurlwidth": 800,
        }

        response = self._request_with_retry("get", COMMONS_API, params=params)
        if response is None or not response.is_success:
            return []

        data = response.json()

        pages = data.get("query", {}).get("pages", {})
        if not pages:
            return []

        images = []
        for page_data in pages.values():
            title = page_data.get("title", "").replace("File:", "")
            imageinfo = page_data.get("imageinfo", [{}])[0]
            image = self._parse_image_info(title, imageinfo)
            if image:
                images.append(image)

        return images

    def get_images_for_wikidata(self, qid: str, limit: int = 5) -> list[CommonsImage]:
        """
        Get images associated with a Wikidata entity.
        Uses the Structured Data on Commons feature.

        Args:
            qid: Wikidata QID (e.g., "Q144")
            limit: Maximum number of images
        """
        # Search for files depicting this Wikidata item
        params = {
            "action": "query",
            "generator": "search",
            "gsrsearch": f"haswbstatement:P180={qid}",  # P180 = depicts
            "gsrnamespace": "6",
            "gsrlimit": limit,
            "format": "json",
            "prop": "imageinfo",
            "iiprop": "url|size|mime|extmetadata|user",
            "iiurlwidth": 800,
        }

        response = self._request_with_retry("get", COMMONS_API, params=params)
        if response is None or not response.is_success:
            return []

        data = response.json()

        pages = data.get("query", {}).get("pages", {})
        if not pages:
            return []

        images = []
        for page_data in pages.values():
            title = page_data.get("title", "").replace("File:", "")
            imageinfo = page_data.get("imageinfo", [{}])[0]
            image = self._parse_image_info(title, imageinfo)
            if image:
                images.append(image)

        return images

    def _search_category(self, scientific_name: str, limit: int) -> list[CommonsImage]:
        """
        Search for images in a species category.
        Categories are often named after the scientific name.
        """
        # Try direct category
        category = scientific_name.replace(" ", "_")

        params = {
            "action": "query",
            "generator": "categorymembers",
            "gcmtitle": f"Category:{category}",
            "gcmtype": "file",
            "gcmlimit": limit,
            "format": "json",
            "prop": "imageinfo",
            "iiprop": "url|size|mime|extmetadata|user",
            "iiurlwidth": 800,
        }

        response = self._request_with_retry("get", COMMONS_API, params=params)
        if response is None or not response.is_success:
            return []

        data = response.json()

        pages = data.get("query", {}).get("pages", {})
        if not pages:
            return []

        images = []
        for page_data in pages.values():
            title = page_data.get("title", "").replace("File:", "")
            imageinfo = page_data.get("imageinfo", [{}])[0]
            image = self._parse_image_info(title, imageinfo)
            if image:
                images.append(image)

        return images

    def _parse_image_info(self, filename: str, imageinfo: dict) -> CommonsImage | None:
        """Parse image info from API response."""
        if not imageinfo:
            return None

        url = imageinfo.get("url")
        if not url:
            return None

        # Filter out non-image files (audio, video, etc.)
        if not self._is_valid_image_url(url):
            return None

        extmetadata = imageinfo.get("extmetadata", {})

        # Parse license
        license_text = extmetadata.get("LicenseShortName", {}).get("value", "").lower()
        license_type = self._parse_license(license_text)

        # Parse author
        author = extmetadata.get("Artist", {}).get("value", "")
        # Clean HTML from author
        if author:
            import re

            author = re.sub(r"<[^>]+>", "", author).strip()

        # Parse description
        description = extmetadata.get("ImageDescription", {}).get("value", "")
        if description:
            import re

            description = re.sub(r"<[^>]+>", "", description).strip()

        return CommonsImage(
            filename=filename,
            url=url,
            thumbnail_url=imageinfo.get("thumburl"),
            width=imageinfo.get("width"),
            height=imageinfo.get("height"),
            mime_type=imageinfo.get("mime"),
            author=author or imageinfo.get("user"),
            license=license_type,
            attribution_required=license_type
            not in (License.CC0, License.PUBLIC_DOMAIN),
            description=description or None,
        )

    def _is_valid_image_url(self, url: str) -> bool:
        """
        Check if URL points to a valid image file.

        Filters out audio, video, and other non-image files.

        Args:
            url: File URL to check

        Returns:
            True if URL appears to be an image, False otherwise
        """
        # Valid image extensions
        valid_extensions = (
            ".jpg",
            ".jpeg",
            ".png",
            ".gif",
            ".svg",
            ".webp",
            ".bmp",
            ".tif",
            ".tiff",
            ".ico",
        )

        # Invalid extensions (audio, video, documents)
        invalid_extensions = (
            ".mp3",
            ".mp4",
            ".ogg",
            ".webm",
            ".wav",
            ".avi",
            ".mov",
            ".pdf",
            ".doc",
            ".txt",
            ".ogv",
            ".flac",
            ".m4a",
        )

        url_lower = url.lower()

        # Check for invalid extensions first
        if any(url_lower.endswith(ext) for ext in invalid_extensions):
            return False

        # Check for valid extensions
        if any(url_lower.endswith(ext) for ext in valid_extensions):
            return True

        # If no extension match, check MIME type hint in URL
        # Commons URLs sometimes have format hints
        if "image/" in url_lower:
            return True

        # Default to False for unknown types
        return False

    def _parse_license(self, license_text: str) -> License | None:
        """Parse license text to License enum."""
        license_lower = license_text.lower().strip()

        for key, value in LICENSE_MAP.items():
            if key in license_lower:
                return value

        # Default to CC-BY-SA if unknown (most common on Commons)
        if license_text:
            return License.CC_BY_SA

        return None
