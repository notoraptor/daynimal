from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class TaxonomicRank(str, Enum):
    KINGDOM = "kingdom"
    PHYLUM = "phylum"
    CLASS = "class"
    ORDER = "order"
    FAMILY = "family"
    GENUS = "genus"
    SPECIES = "species"
    SUBSPECIES = "subspecies"


class ConservationStatus(str, Enum):
    """IUCN Red List categories."""

    EXTINCT = "EX"
    EXTINCT_IN_WILD = "EW"
    CRITICALLY_ENDANGERED = "CR"
    ENDANGERED = "EN"
    VULNERABLE = "VU"
    NEAR_THREATENED = "NT"
    LEAST_CONCERN = "LC"
    DATA_DEFICIENT = "DD"
    NOT_EVALUATED = "NE"


class License(str, Enum):
    """Licenses compatible with commercial use."""

    CC0 = "CC0"
    CC_BY = "CC-BY"
    CC_BY_SA = "CC-BY-SA"
    PUBLIC_DOMAIN = "PUBLIC_DOMAIN"


# --- GBIF / Taxonomy schemas ---


@dataclass
class Taxon:
    """Core taxonomic data from GBIF Backbone."""

    taxon_id: int
    scientific_name: str
    canonical_name: str | None = None
    rank: TaxonomicRank | None = None

    # Classification hierarchy
    kingdom: str | None = None
    phylum: str | None = None
    class_: str | None = None  # 'class' is reserved in Python
    order: str | None = None
    family: str | None = None
    genus: str | None = None

    # Parent relationship
    parent_id: int | None = None

    # Accepted name (for synonyms)
    accepted_id: int | None = None

    # Vernacular names
    vernacular_names: dict[str, list[str]] = field(default_factory=dict)


# --- Wikidata schemas ---


@dataclass
class WikidataEntity:
    """Data retrieved from Wikidata."""

    qid: str  # e.g., "Q144" for dog

    # Labels and descriptions in different languages
    labels: dict[str, str] = field(default_factory=dict)
    descriptions: dict[str, str] = field(default_factory=dict)

    # Key properties
    iucn_status: ConservationStatus | None = None
    habitat: list[str] = field(default_factory=list)
    diet: list[str] = field(default_factory=list)
    lifespan: str | None = None
    mass: str | None = None
    length: str | None = None

    # External identifiers
    gbif_id: int | None = None
    iucn_id: str | None = None
    eol_id: str | None = None

    # Image from Wikidata (P18)
    image_url: str | None = None


# --- Wikipedia schemas ---


@dataclass
class WikipediaArticle:
    """Data retrieved from Wikipedia."""

    title: str
    language: str
    page_id: int

    # Content
    summary: str | None = None
    full_text: str | None = None

    # URL
    url: str | None = None

    # License is always CC-BY-SA for Wikipedia
    license: License = License.CC_BY_SA

    @property
    def article_url(self) -> str:
        """URL to the Wikipedia article."""
        if self.url:
            return self.url
        safe_title = self.title.replace(" ", "_")
        return f"https://{self.language}.wikipedia.org/wiki/{safe_title}"

    @property
    def license_url(self) -> str:
        """URL to CC-BY-SA 4.0 license."""
        return "https://creativecommons.org/licenses/by-sa/4.0/"

    def get_attribution_text(self) -> str:
        """
        Generate required attribution text.
        MUST be displayed when using Wikipedia content in a commercial app.
        """
        return (
            f'"{self.title}" from Wikipedia ({self.language}), '
            f"licensed under CC-BY-SA 4.0. "
            f"Source: {self.article_url}"
        )

    def get_attribution_html(self) -> str:
        """Generate HTML attribution with proper links."""
        return (
            f'"<a href="{self.article_url}">{self.title}</a>" '
            f"from Wikipedia ({self.language}), licensed under "
            f'<a href="{self.license_url}">CC-BY-SA 4.0</a>.'
        )


# --- Wikimedia Commons schemas ---


@dataclass
class CommonsImage:
    """Image data from Wikimedia Commons."""

    filename: str
    url: str
    thumbnail_url: str | None = None

    # Metadata
    width: int | None = None
    height: int | None = None
    mime_type: str | None = None

    # Attribution (REQUIRED for legal compliance)
    author: str | None = None
    license: License | None = None
    attribution_required: bool = True

    # Description
    description: str | None = None

    @property
    def commons_page_url(self) -> str:
        """URL to the image's page on Wikimedia Commons."""
        safe_filename = self.filename.replace(" ", "_")
        return f"https://commons.wikimedia.org/wiki/File:{safe_filename}"

    @property
    def license_url(self) -> str:
        """URL to the license."""
        urls = {
            License.CC0: "https://creativecommons.org/publicdomain/zero/1.0/",
            License.PUBLIC_DOMAIN: "https://creativecommons.org/publicdomain/mark/1.0/",
            License.CC_BY: "https://creativecommons.org/licenses/by/4.0/",
            License.CC_BY_SA: "https://creativecommons.org/licenses/by-sa/4.0/",
        }
        return urls.get(self.license, urls[License.CC_BY_SA])

    def get_attribution_text(self) -> str:
        """
        Generate required attribution text for this image.
        MUST be displayed when showing this image in a commercial app.
        """
        author_str = self.author or "Unknown author"
        # Handle both enum and string (from cache)
        license_str = (
            (self.license.value if hasattr(self.license, "value") else self.license)
            if self.license
            else "CC-BY-SA"
        )
        return (
            f'"{self.filename}" by {author_str}, via Wikimedia Commons ({license_str})'
        )

    def get_attribution_html(self) -> str:
        """Generate HTML attribution with proper links."""
        author_str = self.author or "Unknown author"
        # Handle both enum and string (from cache)
        license_str = (
            (self.license.value if hasattr(self.license, "value") else self.license)
            if self.license
            else "CC-BY-SA"
        )
        return (
            f'<a href="{self.commons_page_url}">{self.filename}</a> '
            f"by {author_str}, via "
            f'<a href="https://commons.wikimedia.org">Wikimedia Commons</a> '
            f'(<a href="{self.license_url}">{license_str}</a>)'
        )


# --- Aggregated animal data ---

# GBIF Attribution constant (always required)
GBIF_ATTRIBUTION_TEXT = (
    "Taxonomic data from GBIF Backbone Taxonomy, "
    "GBIF Secretariat (https://doi.org/10.15468/39omei), "
    "licensed under CC-BY 4.0."
)

GBIF_ATTRIBUTION_HTML = (
    'Taxonomic data from <a href="https://doi.org/10.15468/39omei">GBIF Backbone Taxonomy</a>, '
    "GBIF Secretariat, licensed under "
    '<a href="https://creativecommons.org/licenses/by/4.0/">CC-BY 4.0</a>.'
)


@dataclass
class AnimalInfo:
    """
    Aggregated animal information from all sources.

    IMPORTANT: When displaying this data in a commercial application,
    you MUST call get_attribution_text() or get_attribution_html()
    and display the result to comply with license requirements.
    """

    # Core identity
    taxon: Taxon

    # Enriched data (populated lazily)
    wikidata: WikidataEntity | None = None
    wikipedia: WikipediaArticle | None = None
    images: list[CommonsImage] = field(default_factory=list)

    # Enrichment status
    is_enriched: bool = False

    # History metadata (populated when retrieved from history)
    viewed_at: datetime | None = None
    command: str | None = None

    @property
    def display_name(self) -> str:
        """Best name to display to users."""
        # Prefer French vernacular name, then English, then scientific
        if self.taxon.vernacular_names.get("fr"):
            return self.taxon.vernacular_names["fr"][0]
        if self.taxon.vernacular_names.get("en"):
            return self.taxon.vernacular_names["en"][0]
        return self.taxon.canonical_name or self.taxon.scientific_name

    @property
    def description(self) -> str | None:
        """Best description available."""
        if self.wikipedia and self.wikipedia.summary:
            return self.wikipedia.summary
        if self.wikidata and self.wikidata.descriptions:
            for lang in ["fr", "en"]:
                if lang in self.wikidata.descriptions:
                    return self.wikidata.descriptions[lang]
        return None

    @property
    def main_image(self) -> CommonsImage | None:
        """Primary image for display."""
        if self.images:
            return self.images[0]
        return None

    def get_attribution_text(self) -> str:
        """
        Generate complete attribution text for all data sources used.

        LEGAL REQUIREMENT: This text MUST be displayed somewhere visible
        when showing this animal's information in a commercial application.

        Returns:
            Multi-line attribution text covering all sources.
        """
        lines = ["--- Data Sources & Licenses ---", "", f"• {GBIF_ATTRIBUTION_TEXT}"]

        if self.wikidata:
            lines.append(
                f"• Structured data from Wikidata ({self.wikidata.qid}), "
                f"https://www.wikidata.org/wiki/{self.wikidata.qid}, "
                "licensed under CC0 (public domain)."
            )

        if self.wikipedia:
            lines.append(f"• {self.wikipedia.get_attribution_text()}")

        if self.images:
            lines.append("")
            lines.append("Image credits:")
            for img in self.images:
                lines.append(f"  • {img.get_attribution_text()}")

        return "\n".join(lines)

    def get_attribution_html(self) -> str:
        """
        Generate complete HTML attribution for all data sources.

        LEGAL REQUIREMENT: This HTML MUST be displayed somewhere visible
        when showing this animal's information in a commercial application.

        Returns:
            HTML string with proper links to sources and licenses.
        """
        items = [f"<li>{GBIF_ATTRIBUTION_HTML}</li>"]

        if self.wikidata:
            wikidata_url = f"https://www.wikidata.org/wiki/{self.wikidata.qid}"
            items.append(
                f'<li>Structured data from <a href="{wikidata_url}">Wikidata</a> '
                f"({self.wikidata.qid}), licensed under "
                '<a href="https://creativecommons.org/publicdomain/zero/1.0/">CC0</a>.</li>'
            )

        if self.wikipedia:
            items.append(f"<li>{self.wikipedia.get_attribution_html()}</li>")

        html = "<h4>Data Sources & Licenses</h4>\n<ul>\n" + "\n".join(items) + "\n</ul>"

        if self.images:
            image_items = [
                f"<li>{img.get_attribution_html()}</li>" for img in self.images
            ]
            html += (
                "\n<h4>Image Credits</h4>\n<ul>\n" + "\n".join(image_items) + "\n</ul>"
            )

        return html

    def get_required_attributions_summary(self) -> dict[str, str]:
        """
        Get a summary of required attributions as a dictionary.

        Useful for structured output (JSON APIs, etc.).

        Returns:
            Dictionary mapping source names to attribution strings.
        """
        result = {
            "taxonomy": {
                "source": "GBIF Backbone Taxonomy",
                "license": "CC-BY 4.0",
                "url": "https://doi.org/10.15468/39omei",
            }
        }

        if self.wikidata:
            result["wikidata"] = {
                "source": "Wikidata",
                "license": "CC0",
                "qid": self.wikidata.qid,
                "url": f"https://www.wikidata.org/wiki/{self.wikidata.qid}",
            }

        if self.wikipedia:
            result["wikipedia"] = {
                "source": f"Wikipedia ({self.wikipedia.language})",
                "license": "CC-BY-SA 4.0",
                "title": self.wikipedia.title,
                "url": self.wikipedia.article_url,
            }

        if self.images:
            result["images"] = [
                {
                    "source": "Wikimedia Commons",
                    "license": img.license.value if img.license else "CC-BY-SA",
                    "filename": img.filename,
                    "author": img.author or "Unknown",
                    "url": img.commons_page_url,
                }
                for img in self.images
            ]

        return result
