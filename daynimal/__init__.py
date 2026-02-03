"""
Daynimal - Daily Animal Discovery App

Provides enriched information about animals from multiple open data sources.

Data Sources:
- GBIF Backbone Taxonomy (CC-BY 4.0) - taxonomic base
- Wikidata (CC0) - structured data
- Wikipedia (CC-BY-SA) - descriptions
- Wikimedia Commons (CC-BY/CC-BY-SA/CC0) - images

All sources are compatible with commercial use.

IMPORTANT - LEGAL COMPLIANCE:
When using this library in a commercial application, you MUST display
proper attribution for the data sources. Use the following methods:

    animal = repo.get_by_name("Canis lupus")

    # Get attribution text (for CLI/text output)
    print(animal.get_attribution_text())

    # Get attribution HTML (for web/app output)
    html = animal.get_attribution_html()

    # Get structured attribution data (for JSON APIs)
    data = animal.get_required_attributions_summary()

For the app-wide legal notice (About page), use:

    from daynimal.attribution import get_app_legal_notice
    print(get_app_legal_notice())

Failure to display attributions may violate the CC-BY and CC-BY-SA licenses.
"""

from daynimal.repository import AnimalRepository
from daynimal.schemas import (
    AnimalInfo,
    Taxon,
    WikidataEntity,
    WikipediaArticle,
    CommonsImage,
)
from daynimal.attribution import (
    get_app_legal_notice,
    DataAttribution,
    AttributionInfo,
    create_wikipedia_attribution,
    create_wikidata_attribution,
    create_commons_attribution,
)

__version__ = "0.1.0"

__all__ = [
    # Main classes
    "AnimalRepository",
    "AnimalInfo",
    "Taxon",
    "WikidataEntity",
    "WikipediaArticle",
    "CommonsImage",
    # Attribution helpers
    "get_app_legal_notice",
    "DataAttribution",
    "AttributionInfo",
    "create_wikipedia_attribution",
    "create_wikidata_attribution",
    "create_commons_attribution",
]
