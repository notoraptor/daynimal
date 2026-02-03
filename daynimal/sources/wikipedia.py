"""
Wikipedia API client.

Wikipedia content is licensed under CC-BY-SA 4.0.
https://en.wikipedia.org/wiki/Wikipedia:Reusing_Wikipedia_content

Commercial use is allowed with proper attribution and share-alike.
"""

from daynimal.config import settings
from daynimal.schemas import WikipediaArticle, License
from daynimal.sources.base import DataSource

# Wikipedia API endpoint template
WIKIPEDIA_API = "https://{lang}.wikipedia.org/w/api.php"


class WikipediaAPI(DataSource[WikipediaArticle]):
    """
    Client for Wikipedia API.

    License: CC-BY-SA 4.0 - commercial use allowed with attribution
    and share-alike requirement.
    """

    def __init__(self, languages: list[str] | None = None):
        """
        Initialize Wikipedia API client.

        Args:
            languages: List of language codes in order of preference.
                      Defaults to settings.wikipedia_languages.
        """
        super().__init__()
        self.languages = languages or settings.wikipedia_languages

    @property
    def source_name(self) -> str:
        return "wikipedia"

    @property
    def license(self) -> str:
        return License.CC_BY_SA.value

    def get_by_source_id(
        self, source_id: str, language: str = "en"
    ) -> WikipediaArticle | None:
        """
        Fetch a Wikipedia article by page ID or title.

        Args:
            source_id: Page ID (numeric) or page title
            language: Wikipedia language code
        """
        api_url = WIKIPEDIA_API.format(lang=language)

        # Determine if source_id is a page ID or title
        if source_id.isdigit():
            params = {
                "action": "query",
                "pageids": source_id,
                "format": "json",
                "prop": "extracts|info",
                "exintro": "1",
                "explaintext": "1",
                "inprop": "url",
            }
        else:
            params = {
                "action": "query",
                "titles": source_id,
                "format": "json",
                "prop": "extracts|info",
                "exintro": "1",
                "explaintext": "1",
                "inprop": "url",
                "redirects": "1",
            }

        response = self.client.get(api_url, params=params)
        response.raise_for_status()
        data = response.json()

        pages = data.get("query", {}).get("pages", {})
        if not pages:
            return None

        # Get first (and should be only) page
        page_id, page_data = next(iter(pages.items()))

        if page_id == "-1" or "missing" in page_data:
            return None

        return WikipediaArticle(
            title=page_data.get("title", ""),
            language=language,
            page_id=int(page_id),
            summary=page_data.get("extract"),
            url=page_data.get("fullurl"),
            license=License.CC_BY_SA,
        )

    def get_by_taxonomy(self, scientific_name: str) -> WikipediaArticle | None:
        """
        Find a Wikipedia article by scientific name.
        Tries multiple languages in order of preference.

        Args:
            scientific_name: Scientific name (e.g., "Canis lupus")
        """
        for lang in self.languages:
            article = self._search_in_language(scientific_name, lang)
            if article:
                return article

        return None

    def search(
        self, query: str, limit: int = 10, language: str = "en"
    ) -> list[WikipediaArticle]:
        """
        Search Wikipedia for articles matching query.

        Args:
            query: Search query
            limit: Maximum results
            language: Wikipedia language code
        """
        api_url = WIKIPEDIA_API.format(lang=language)

        params = {
            "action": "query",
            "list": "search",
            "srsearch": query,
            "srlimit": limit,
            "format": "json",
        }

        response = self.client.get(api_url, params=params)
        response.raise_for_status()
        data = response.json()

        results = []
        for item in data.get("query", {}).get("search", []):
            article = self.get_by_source_id(str(item["pageid"]), language)
            if article:
                results.append(article)

        return results

    def get_full_article(
        self, page_id: int, language: str = "en"
    ) -> WikipediaArticle | None:
        """
        Fetch full article content (not just summary).

        Args:
            page_id: Wikipedia page ID
            language: Wikipedia language code
        """
        api_url = WIKIPEDIA_API.format(lang=language)

        params = {
            "action": "query",
            "pageids": page_id,
            "format": "json",
            "prop": "extracts|info",
            "explaintext": "1",
            "inprop": "url",
        }

        response = self.client.get(api_url, params=params)
        response.raise_for_status()
        data = response.json()

        pages = data.get("query", {}).get("pages", {})
        page_data = pages.get(str(page_id))

        if not page_data or "missing" in page_data:
            return None

        return WikipediaArticle(
            title=page_data.get("title", ""),
            language=language,
            page_id=page_id,
            full_text=page_data.get("extract"),
            url=page_data.get("fullurl"),
            license=License.CC_BY_SA,
        )

    def _search_in_language(
        self, scientific_name: str, language: str
    ) -> WikipediaArticle | None:
        """
        Search for an article by scientific name in a specific language.
        First tries exact title match, then falls back to search.
        """
        # Try exact title match first
        article = self.get_by_source_id(scientific_name, language)
        if article:
            return article

        # Fall back to search
        api_url = WIKIPEDIA_API.format(lang=language)

        params = {
            "action": "query",
            "list": "search",
            "srsearch": f'"{scientific_name}"',  # Exact phrase search
            "srlimit": 5,
            "format": "json",
        }

        response = self.client.get(api_url, params=params)
        response.raise_for_status()
        data = response.json()

        search_results = data.get("query", {}).get("search", [])

        for result in search_results:
            # Verify this is actually about the species
            # by checking if the scientific name appears in the title
            title = result.get("title", "").lower()
            name_lower = scientific_name.lower()

            if name_lower in title or title in name_lower:
                return self.get_by_source_id(str(result["pageid"]), language)

        # If no good match, return first result if any
        if search_results:
            return self.get_by_source_id(str(search_results[0]["pageid"]), language)

        return None
