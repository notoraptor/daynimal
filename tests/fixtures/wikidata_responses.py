"""
Mock responses for Wikidata API.

These fixtures simulate real API responses without network calls.
"""

# Response for wbgetentities with Q18498 (Canis lupus / Wolf)
WIKIDATA_ENTITY_Q18498 = {
    "entities": {
        "Q18498": {
            "type": "item",
            "id": "Q18498",
            "labels": {
                "en": {"language": "en", "value": "Canis lupus"},
                "fr": {"language": "fr", "value": "loup"},
            },
            "descriptions": {
                "en": {"language": "en", "value": "species of mammal"},
                "fr": {"language": "fr", "value": "espèce de mammifères"},
            },
            "claims": {
                "P18": [
                    {
                        "mainsnak": {
                            "datavalue": {
                                "value": "Eurasian_wolf_2.jpg",
                                "type": "string",
                            }
                        }
                    }
                ],
                "P846": [
                    {"mainsnak": {"datavalue": {"value": "5219173", "type": "string"}}}
                ],
                "P225": [
                    {
                        "mainsnak": {
                            "datavalue": {"value": "Canis lupus", "type": "string"}
                        }
                    }
                ],
                "P141": [
                    {
                        "mainsnak": {
                            "datavalue": {
                                "value": {"id": "Q237350"},
                                "type": "wikibase-entityid",
                            }
                        }
                    }
                ],
                "P2067": [
                    {
                        "mainsnak": {
                            "datavalue": {
                                "value": {
                                    "amount": "+40",
                                    "unit": "http://www.wikidata.org/entity/Q11570",
                                },
                                "type": "quantity",
                            }
                        }
                    }
                ],
            },
        }
    }
}

# Response for SPARQL query finding QID by scientific name
WIKIDATA_SPARQL_CANIS_LUPUS = {
    "results": {
        "bindings": [{"item": {"value": "http://www.wikidata.org/entity/Q18498"}}]
    }
}

# Response for wbsearchentities
WIKIDATA_SEARCH_WOLF = {
    "search": [
        {"id": "Q18498", "label": "Canis lupus", "description": "species of mammal"},
        {"id": "Q144", "label": "dog", "description": "domestic animal"},
    ]
}

# Response for entity not found
WIKIDATA_NOT_FOUND = {"entities": {"Q999999999": {"missing": ""}}}
