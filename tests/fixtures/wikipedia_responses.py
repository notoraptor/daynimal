"""
Mock responses for Wikipedia API.

These fixtures simulate real API responses without network calls.
"""

# Response for query with extracts for Canis lupus (French)
WIKIPEDIA_ARTICLE_CANIS_LUPUS_FR = {
    "query": {
        "pages": {
            "3135": {
                "pageid": 3135,
                "title": "Canis lupus",
                "extract": (
                    "Canis lupus, le Loup, plus spécifiquement désigné sous le nom "
                    "de Loup gris, plus rarement sous ceux de Loup commun ou Loup "
                    "vulgaire, est une espèce de mammifère carnivore de la famille "
                    "des canidés. La sous-espèce la plus connue est le chien domestique."
                ),
                "fullurl": "https://fr.wikipedia.org/wiki/Canis_lupus",
            }
        }
    }
}

# Response for query with extracts for Canis lupus (English)
WIKIPEDIA_ARTICLE_CANIS_LUPUS_EN = {
    "query": {
        "pages": {
            "39365": {
                "pageid": 39365,
                "title": "Wolf",
                "extract": (
                    "The wolf (Canis lupus), also known as the gray wolf or grey wolf, "
                    "is a large canine native to Eurasia and North America. More than "
                    "thirty subspecies of Canis lupus have been recognized."
                ),
                "fullurl": "https://en.wikipedia.org/wiki/Wolf",
            }
        }
    }
}

# Response for search
WIKIPEDIA_SEARCH_WOLF = {
    "query": {
        "search": [
            {"pageid": 3135, "title": "Canis lupus"},
            {"pageid": 12345, "title": "Loup gris"},
        ]
    }
}

# Response for article not found
WIKIPEDIA_NOT_FOUND = {"query": {"pages": {"-1": {"missing": ""}}}}
