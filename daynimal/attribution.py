"""
Attribution management for legal compliance.

This module ensures proper attribution for all data sources
as required by their respective licenses:

- GBIF Backbone: CC-BY 4.0 (attribution required)
- TAXREF: Etalab Open License 2.0 (attribution required, compatible with CC-BY)
- Wikidata: CC0 (no attribution required, but recommended)
- Wikipedia: CC-BY-SA 4.0 (attribution required, share-alike)
- Wikimedia Commons: varies (CC-BY, CC-BY-SA, CC0, Public Domain)

IMPORTANT: Commercial use requires displaying these attributions
to end users in the application.
"""

from dataclasses import dataclass, field
from datetime import datetime, UTC

from daynimal.schemas import License


@dataclass
class AttributionInfo:
    """Attribution information for a single data source."""

    source_name: str
    license: License
    license_url: str

    # Required for CC-BY
    author: str | None = None
    title: str | None = None
    source_url: str | None = None

    # Access date (good practice)
    access_date: datetime | None = None

    # Whether modifications were made (important for CC-BY-SA)
    modified: bool = False

    def to_text(self, format: str = "full") -> str:
        """
        Generate attribution text.

        Args:
            format: "full" for complete attribution, "short" for compact version
        """
        if format == "short":
            return self._short_text()
        return self._full_text()

    def _full_text(self) -> str:
        """Generate full attribution text."""
        parts = []

        if self.title:
            parts.append(f'"{self.title}"')

        if self.author:
            parts.append(f"by {self.author}")

        parts.append(f"from {self.source_name}")

        if self.source_url:
            parts.append(f"({self.source_url})")

        parts.append(f"licensed under {self.license.value}")
        parts.append(f"({self.license_url})")

        if self.modified:
            parts.append("[modified]")

        return " ".join(parts)

    def _short_text(self) -> str:
        """Generate short attribution text."""
        author_str = f"{self.author} / " if self.author else ""
        return f"{author_str}{self.source_name} ({self.license.value})"

    def to_html(self) -> str:
        """Generate HTML attribution with links."""
        parts = []

        if self.title:
            if self.source_url:
                parts.append(f'<a href="{self.source_url}">{self.title}</a>')
            else:
                parts.append(f'<em>"{self.title}"</em>')

        if self.author:
            parts.append(f"by {self.author}")

        parts.append(f"from {self.source_name}")

        license_link = f'<a href="{self.license_url}">{self.license.value}</a>'
        parts.append(f"licensed under {license_link}")

        if self.modified:
            parts.append("<em>[modified]</em>")

        return " ".join(parts)


@dataclass
class DataAttribution:
    """
    Complete attribution for an animal's data.

    This should always accompany any AnimalInfo to ensure
    legal compliance when displaying data.
    """

    # Taxonomy attribution (always present)
    taxonomy: AttributionInfo = field(default_factory=lambda: GBIF_ATTRIBUTION)

    # Optional source attributions
    wikidata: AttributionInfo | None = None
    wikipedia: AttributionInfo | None = None
    images: list[AttributionInfo] = field(default_factory=list)

    def get_all(self) -> list[AttributionInfo]:
        """Get all attributions as a list."""
        result = [self.taxonomy]
        if self.wikidata:
            result.append(self.wikidata)
        if self.wikipedia:
            result.append(self.wikipedia)
        result.extend(self.images)
        return result

    def to_text(self, format: str = "full") -> str:
        """Generate complete attribution text."""
        lines = ["Data Sources and Attributions:", ""]
        for attr in self.get_all():
            lines.append(f"• {attr.to_text(format)}")
        return "\n".join(lines)

    def to_html(self) -> str:
        """Generate HTML attribution block."""
        items = [f"<li>{attr.to_html()}</li>" for attr in self.get_all()]
        return f"<h4>Data Sources and Attributions</h4>\n<ul>\n{''.join(items)}\n</ul>"

    def get_required_attributions(self) -> list[AttributionInfo]:
        """Get only attributions that are legally required (non-CC0)."""
        return [
            attr
            for attr in self.get_all()
            if attr.license not in (License.CC0, License.PUBLIC_DOMAIN)
        ]


# --- Standard attributions for each source ---

GBIF_ATTRIBUTION = AttributionInfo(
    source_name="GBIF Backbone Taxonomy",
    license=License.CC_BY,
    license_url="https://creativecommons.org/licenses/by/4.0/",
    author="GBIF Secretariat",
    title="GBIF Backbone Taxonomy",
    source_url="https://doi.org/10.15468/39omei",
)

TAXREF_ATTRIBUTION = AttributionInfo(
    source_name="TAXREF",
    license=License.CC_BY,  # Etalab Open License 2.0 is compatible with CC-BY
    license_url="https://github.com/etalab/licence-ouverte/blob/master/LO.md",
    author="Muséum national d'Histoire naturelle",
    title="TAXREF v17",
    source_url="https://inpn.mnhn.fr/",
)

WIKIDATA_ATTRIBUTION = AttributionInfo(
    source_name="Wikidata",
    license=License.CC0,
    license_url="https://creativecommons.org/publicdomain/zero/1.0/",
    author="Wikidata contributors",
)


def create_wikidata_attribution(qid: str) -> AttributionInfo:
    """Create attribution for a specific Wikidata entity."""
    return AttributionInfo(
        source_name="Wikidata",
        license=License.CC0,
        license_url="https://creativecommons.org/publicdomain/zero/1.0/",
        author="Wikidata contributors",
        title=f"Wikidata item {qid}",
        source_url=f"https://www.wikidata.org/wiki/{qid}",
        access_date=datetime.now(UTC),
    )


def create_wikipedia_attribution(
    title: str, language: str, url: str | None = None, modified: bool = False
) -> AttributionInfo:
    """Create attribution for a Wikipedia article."""
    if url is None:
        url = f"https://{language}.wikipedia.org/wiki/{title.replace(' ', '_')}"

    return AttributionInfo(
        source_name=f"Wikipedia ({language})",
        license=License.CC_BY_SA,
        license_url="https://creativecommons.org/licenses/by-sa/4.0/",
        author="Wikipedia contributors",
        title=title,
        source_url=url,
        access_date=datetime.now(UTC),
        modified=modified,
    )


def create_gbif_media_attribution(
    author: str | None, license: License | None, url: str | None = None
) -> AttributionInfo:
    """Create attribution for a GBIF Media image."""
    if license is None:
        license = License.CC_BY

    license_urls = {
        License.CC0: "https://creativecommons.org/publicdomain/zero/1.0/",
        License.PUBLIC_DOMAIN: "https://creativecommons.org/publicdomain/mark/1.0/",
        License.CC_BY: "https://creativecommons.org/licenses/by/4.0/",
        License.CC_BY_SA: "https://creativecommons.org/licenses/by-sa/4.0/",
    }

    return AttributionInfo(
        source_name="GBIF",
        license=license,
        license_url=license_urls.get(license, license_urls[License.CC_BY]),
        author=author or "Unknown author",
        source_url=url or "https://www.gbif.org/",
        access_date=datetime.now(UTC),
    )


def create_phylopic_attribution(
    author: str | None, license: License | None, url: str | None = None
) -> AttributionInfo:
    """Create attribution for a PhyloPic silhouette."""
    if license is None:
        license = License.CC0

    license_urls = {
        License.CC0: "https://creativecommons.org/publicdomain/zero/1.0/",
        License.PUBLIC_DOMAIN: "https://creativecommons.org/publicdomain/mark/1.0/",
        License.CC_BY: "https://creativecommons.org/licenses/by/4.0/",
        License.CC_BY_SA: "https://creativecommons.org/licenses/by-sa/4.0/",
    }

    return AttributionInfo(
        source_name="PhyloPic",
        license=license,
        license_url=license_urls.get(license, license_urls[License.CC0]),
        author=author or "Unknown author",
        source_url=url or "https://www.phylopic.org/",
        access_date=datetime.now(UTC),
    )


def create_commons_attribution(
    filename: str, author: str | None, license: License | None, url: str | None = None
) -> AttributionInfo:
    """Create attribution for a Wikimedia Commons image."""
    if url is None:
        url = f"https://commons.wikimedia.org/wiki/File:{filename.replace(' ', '_')}"

    # Default to CC-BY-SA if license unknown
    if license is None:
        license = License.CC_BY_SA

    license_urls = {
        License.CC0: "https://creativecommons.org/publicdomain/zero/1.0/",
        License.PUBLIC_DOMAIN: "https://creativecommons.org/publicdomain/mark/1.0/",
        License.CC_BY: "https://creativecommons.org/licenses/by/4.0/",
        License.CC_BY_SA: "https://creativecommons.org/licenses/by-sa/4.0/",
    }

    return AttributionInfo(
        source_name="Wikimedia Commons",
        license=license,
        license_url=license_urls.get(license, license_urls[License.CC_BY_SA]),
        author=author or "Unknown author",
        title=filename,
        source_url=url,
        access_date=datetime.now(UTC),
    )


# --- Legal notice templates ---

LEGAL_NOTICE_SHORT = """
Data provided by GBIF, Wikidata, Wikipedia, and Wikimedia Commons.
See individual entries for specific attributions and licenses.
"""

LEGAL_NOTICE_FULL = """
LEGAL NOTICE - DATA ATTRIBUTION

This application uses data from the following sources:

1. GBIF BACKBONE TAXONOMY
   "GBIF Backbone Taxonomy" by GBIF Secretariat
   Licensed under CC-BY 4.0
   https://doi.org/10.15468/39omei
   https://creativecommons.org/licenses/by/4.0/

2. TAXREF (French Vernacular Names)
   "TAXREF v17" by Muséum national d'Histoire naturelle
   Licensed under Etalab Open License 2.0 (compatible with CC-BY 4.0)
   https://inpn.mnhn.fr/
   https://github.com/etalab/licence-ouverte/blob/master/LO.md

3. WIKIDATA
   Data from Wikidata, the free knowledge base
   Licensed under CC0 (Public Domain)
   https://www.wikidata.org/
   https://creativecommons.org/publicdomain/zero/1.0/

4. WIKIPEDIA
   Text content from Wikipedia, the free encyclopedia
   Licensed under CC-BY-SA 4.0
   Individual article URLs provided with each entry
   https://creativecommons.org/licenses/by-sa/4.0/

5. WIKIMEDIA COMMONS
   Images from Wikimedia Commons
   Various licenses (CC-BY, CC-BY-SA, CC0, Public Domain)
   Individual image credits and licenses provided with each image
   https://commons.wikimedia.org/

6. GBIF MEDIA
   Occurrence photos from GBIF
   Various licenses (CC0, CC-BY, CC-BY-SA)
   https://www.gbif.org/

7. PHYLOPIC
   Silhouette images from PhyloPic
   Various licenses (CC0, CC-BY, CC-BY-SA)
   https://www.phylopic.org/

For specific attributions, see the credits displayed with each animal entry.
"""


def get_app_legal_notice(format: str = "full") -> str:
    """Get the application's legal notice for display in About page."""
    if format == "short":
        return LEGAL_NOTICE_SHORT.strip()
    return LEGAL_NOTICE_FULL.strip()
