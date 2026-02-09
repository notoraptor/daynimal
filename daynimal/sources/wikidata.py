"""
Wikidata API client.

Wikidata content is licensed under CC0 (public domain).
https://www.wikidata.org/wiki/Wikidata:Licensing
"""

from daynimal.schemas import WikidataEntity, ConservationStatus, License
from daynimal.sources.base import DataSource

# Wikidata API endpoints
WIKIDATA_API = "https://www.wikidata.org/w/api.php"
WIKIDATA_SPARQL = "https://query.wikidata.org/sparql"

# Wikidata properties relevant to animals
PROPERTIES = {
    "P18": "image",
    "P105": "taxon_rank",
    "P171": "parent_taxon",
    "P225": "taxon_name",
    "P685": "ncbi_id",
    "P815": "itis_id",
    "P830": "eol_id",
    "P846": "gbif_id",
    "P141": "iucn_status",
    "P2067": "mass",
    "P2043": "length",
    "P2250": "lifespan",
    "P183": "endemic_to",
    "P2974": "habitat",
    "P1034": "diet",
}

# IUCN status QID mapping
IUCN_QID_MAP = {
    "Q237350": ConservationStatus.LEAST_CONCERN,
    "Q719675": ConservationStatus.NEAR_THREATENED,
    "Q278113": ConservationStatus.VULNERABLE,
    "Q11394": ConservationStatus.ENDANGERED,
    "Q219127": ConservationStatus.CRITICALLY_ENDANGERED,
    "Q239509": ConservationStatus.EXTINCT_IN_WILD,
    "Q58926": ConservationStatus.EXTINCT,
    "Q3245245": ConservationStatus.DATA_DEFICIENT,
    "Q8009752": ConservationStatus.NOT_EVALUATED,
}


class WikidataAPI(DataSource[WikidataEntity]):
    """
    Client for Wikidata API.

    License: CC0 (public domain) - free for commercial use.
    """

    @property
    def source_name(self) -> str:
        return "wikidata"

    @property
    def license(self) -> str:
        return License.CC0.value

    def get_by_source_id(self, source_id: str) -> WikidataEntity | None:
        """
        Fetch a Wikidata entity by its QID.

        Args:
            source_id: Wikidata QID (e.g., "Q144" for dog)
        """
        qid = source_id.upper()
        if not qid.startswith("Q"):
            qid = f"Q{qid}"

        params = {
            "action": "wbgetentities",
            "ids": qid,
            "format": "json",
            "props": "labels|descriptions|claims|sitelinks",
            "languages": "en|fr",
        }

        response = self._request_with_retry("get", WIKIDATA_API, params=params)
        if response is None or not response.is_success:
            return None

        data = response.json()

        entities = data.get("entities", {})
        if qid not in entities or "missing" in entities.get(qid, {}):
            return None

        return self._parse_entity(qid, entities[qid])

    def get_by_taxonomy(self, scientific_name: str) -> WikidataEntity | None:
        """
        Find a Wikidata entity by scientific name using SPARQL.

        Args:
            scientific_name: Scientific name (e.g., "Canis lupus")
        """
        # First, search for the taxon by name
        qid = self._find_taxon_qid(scientific_name)
        if not qid:
            return None

        return self.get_by_source_id(qid)

    def search(self, query: str, limit: int = 10) -> list[WikidataEntity]:
        """
        Search Wikidata for entities matching query.
        Limited to taxa (instance of taxon or subclass).
        """
        params = {
            "action": "wbsearchentities",
            "search": query,
            "format": "json",
            "language": "en",
            "type": "item",
            "limit": limit,
        }

        response = self._request_with_retry("get", WIKIDATA_API, params=params)
        if response is None or not response.is_success:
            return []

        data = response.json()

        results = []
        for item in data.get("search", []):
            entity = self.get_by_source_id(item["id"])
            if entity:
                results.append(entity)

        return results

    def _find_taxon_qid(self, scientific_name: str) -> str | None:
        """Find QID for a taxon by its scientific name."""
        # Use SPARQL to find exact match on taxon name (P225)
        query = f"""
        SELECT ?item WHERE {{
            ?item wdt:P225 "{scientific_name}" .
        }} LIMIT 1
        """

        response = self._request_with_retry(
            "get",
            WIKIDATA_SPARQL,
            params={"query": query, "format": "json"},
            headers={"Accept": "application/sparql-results+json"},
        )

        if response is None or not response.is_success:
            # Fallback to search API
            return self._search_taxon_qid(scientific_name)

        data = response.json()
        bindings = data.get("results", {}).get("bindings", [])

        if bindings:
            uri = bindings[0]["item"]["value"]
            return uri.split("/")[-1]

        # Fallback to search
        return self._search_taxon_qid(scientific_name)

    def _search_taxon_qid(self, scientific_name: str) -> str | None:
        """Fallback search for taxon QID."""
        params = {
            "action": "wbsearchentities",
            "search": scientific_name,
            "format": "json",
            "language": "en",
            "type": "item",
            "limit": 5,
        }

        response = self._request_with_retry("get", WIKIDATA_API, params=params)
        if response is None or not response.is_success:
            return None

        data = response.json()

        for item in data.get("search", []):
            # Verify this is a taxon by checking for taxon name property
            if self._is_taxon(item["id"]):
                return item["id"]

        return None

    def _is_taxon(self, qid: str) -> bool:
        """Check if an entity is a taxon (has P225 taxon name)."""
        params = {
            "action": "wbgetclaims",
            "entity": qid,
            "property": "P225",
            "format": "json",
        }

        response = self._request_with_retry("get", WIKIDATA_API, params=params)
        if response is None or not response.is_success:
            return False

        data = response.json()
        return bool(data.get("claims", {}).get("P225"))

    def _parse_entity(self, qid: str, data: dict) -> WikidataEntity:
        """Parse raw Wikidata entity into WikidataEntity schema."""
        entity = WikidataEntity(qid=qid)

        # Labels
        labels = data.get("labels", {})
        for lang, label_data in labels.items():
            entity.labels[lang] = label_data["value"]

        # Descriptions
        descriptions = data.get("descriptions", {})
        for lang, desc_data in descriptions.items():
            entity.descriptions[lang] = desc_data["value"]

        # Claims (properties)
        claims = data.get("claims", {})

        # Image (P18)
        if "P18" in claims:
            image_name = self._get_claim_value(claims["P18"])
            if image_name:
                entity.image_url = self._get_commons_url(image_name)

        # GBIF ID (P846)
        if "P846" in claims:
            gbif_id = self._get_claim_value(claims["P846"])
            if gbif_id:
                try:
                    entity.gbif_id = int(gbif_id)
                except ValueError:
                    pass

        # EOL ID (P830)
        if "P830" in claims:
            entity.eol_id = self._get_claim_value(claims["P830"])

        # IUCN status (P141)
        if "P141" in claims:
            status_qid = self._get_claim_value(
                claims["P141"], value_type="wikibase-entityid"
            )
            if status_qid and status_qid in IUCN_QID_MAP:
                entity.iucn_status = IUCN_QID_MAP[status_qid]

        # Mass (P2067)
        if "P2067" in claims:
            entity.mass = self._get_quantity_string(claims["P2067"])

        # Length (P2043)
        if "P2043" in claims:
            entity.length = self._get_quantity_string(claims["P2043"])

        # Lifespan (P2250)
        if "P2250" in claims:
            entity.lifespan = self._get_quantity_string(claims["P2250"])

        return entity

    def _get_claim_value(
        self, claim_list: list, value_type: str = "string"
    ) -> str | None:
        """Extract value from a claim list."""
        if not claim_list:
            return None

        mainsnak = claim_list[0].get("mainsnak", {})
        datavalue = mainsnak.get("datavalue", {})

        if value_type == "wikibase-entityid":
            return datavalue.get("value", {}).get("id")

        value = datavalue.get("value")
        if isinstance(value, dict):
            return value.get("text") or value.get("id")
        return value

    def _get_quantity_string(self, claim_list: list) -> str | None:
        """Extract quantity with unit from a claim."""
        if not claim_list:
            return None

        mainsnak = claim_list[0].get("mainsnak", {})
        datavalue = mainsnak.get("datavalue", {})
        value = datavalue.get("value", {})

        amount = value.get("amount", "")
        unit = value.get("unit", "")

        if amount:
            # Clean up amount (remove + prefix)
            amount = amount.lstrip("+")

            # Extract unit name from URI
            if unit and unit != "1":
                unit_qid = unit.split("/")[-1]
                # Common units
                unit_map = {
                    "Q11573": "m",
                    "Q174728": "cm",
                    "Q11570": "kg",
                    "Q41803": "g",
                    "Q577": "year",
                    "Q5151": "month",
                }
                unit = unit_map.get(unit_qid, "")

            return f"{amount} {unit}".strip()

        return None

    def _get_commons_url(self, filename: str) -> str:
        """Convert Commons filename to URL."""
        # Replace spaces with underscores
        filename = filename.replace(" ", "_")
        return f"https://commons.wikimedia.org/wiki/Special:FilePath/{filename}"
