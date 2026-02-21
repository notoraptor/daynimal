"""Tests pour daynimal/db/generate_distribution.py -- Generation des fichiers TSV.

Couvre: extract_and_filter_taxa, extract_and_filter_vernacular,
build_canonical_to_taxon_ids, parse_taxref_french_names,
merge_taxref_into_vernacular, cleanup_taxa_without_vernacular,
generate_distribution.

Strategie: on cree des fichiers ZIP/TSV/TAXREF temporaires avec tmp_path
pour simuler les donnees d'entree. On verifie les fichiers de sortie
generes et les statistiques retournees.
"""

import csv
import io
import zipfile
from unittest.mock import patch

import pytest

from daynimal.db.generate_distribution import (
    _split_vernacular_names,
    extract_and_filter_taxa,
    extract_and_filter_vernacular,
    build_canonical_to_taxon_ids,
    parse_taxref_french_names,
    merge_taxref_into_vernacular,
    cleanup_taxa_without_vernacular,
    generate_distribution,
)
from daynimal.db.import_gbif_utils import TAXON_COLUMNS


# =============================================================================
# Helpers pour creer des donnees de test
# =============================================================================


def _make_taxon_row(
    taxon_id="1",
    scientific_name="Canis lupus",
    canonical_name="Canis lupus",
    rank="species",
    kingdom="Animalia",
    phylum="Chordata",
    class_="Mammalia",
    order="Carnivora",
    family="Canidae",
    genus="Canis",
    parent_id="",
    accepted_id="",
    taxonomic_status="accepted",
):
    """Build a 23-column Taxon.tsv row matching GBIF backbone structure."""
    row = [""] * 23
    row[TAXON_COLUMNS["taxonID"]] = taxon_id
    row[TAXON_COLUMNS["scientificName"]] = scientific_name
    row[TAXON_COLUMNS["canonicalName"]] = canonical_name
    row[TAXON_COLUMNS["taxonRank"]] = rank
    row[TAXON_COLUMNS["kingdom"]] = kingdom
    row[TAXON_COLUMNS["phylum"]] = phylum
    row[TAXON_COLUMNS["class"]] = class_
    row[TAXON_COLUMNS["order"]] = order
    row[TAXON_COLUMNS["family"]] = family
    row[TAXON_COLUMNS["genus"]] = genus
    row[TAXON_COLUMNS["parentNameUsageID"]] = parent_id
    row[TAXON_COLUMNS["acceptedNameUsageID"]] = accepted_id
    row[TAXON_COLUMNS["taxonomicStatus"]] = taxonomic_status
    return row


def _make_vernacular_row(taxon_id="1", name="Wolf", language="en"):
    """Build a VernacularName.tsv row (3+ columns)."""
    return [str(taxon_id), name, language]


def _write_tsv_to_buffer(header, rows):
    """Write rows as TSV to a bytes buffer, suitable for adding to a ZIP."""
    buf = io.StringIO()
    writer = csv.writer(buf, delimiter="\t", quoting=csv.QUOTE_NONE, escapechar="\\")
    writer.writerow(header)
    for row in rows:
        writer.writerow(row)
    return buf.getvalue().encode("utf-8")


def _create_backbone_zip(zip_path, taxon_rows=None, vernacular_rows=None):
    """Create a backbone.zip with Taxon.tsv and/or VernacularName.tsv."""
    taxon_header = [""] * 23
    for col_name, idx in TAXON_COLUMNS.items():
        taxon_header[idx] = col_name

    vernacular_header = ["taxonID", "vernacularName", "language"]

    with zipfile.ZipFile(zip_path, "w") as zf:
        if taxon_rows is not None:
            data = _write_tsv_to_buffer(taxon_header, taxon_rows)
            zf.writestr("Taxon.tsv", data)
        if vernacular_rows is not None:
            data = _write_tsv_to_buffer(vernacular_header, vernacular_rows)
            zf.writestr("VernacularName.tsv", data)


def _create_taxa_tsv(path, rows):
    """Write a taxa TSV file (no header, 13 columns per row)."""
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, delimiter="\t", quoting=csv.QUOTE_NONE, escapechar="\\")
        for row in rows:
            writer.writerow(row)


def _create_vernacular_tsv(path, rows):
    """Write a vernacular TSV file (no header, 3 columns per row)."""
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, delimiter="\t", quoting=csv.QUOTE_NONE, escapechar="\\")
        for row in rows:
            writer.writerow(row)


def _read_tsv(path):
    """Read a TSV file and return all rows as lists."""
    rows = []
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.reader(f, delimiter="\t", quoting=csv.QUOTE_NONE)
        for row in reader:
            rows.append(row)
    return rows


def _create_taxref_file(path, rows):
    """Create a TAXREF tab-separated file with header and data rows.

    Each row is a dict with keys matching TAXREF columns.
    At minimum: REGNE, NOM_VERN, LB_NOM.
    """
    fieldnames = ["REGNE", "NOM_VERN", "LB_NOM"]
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f, fieldnames=fieldnames, delimiter="\t", extrasaction="ignore"
        )
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


# =============================================================================
# SECTION 1 : extract_and_filter_taxa
# =============================================================================


class TestExtractAndFilterTaxa:
    """Tests pour extract_and_filter_taxa(zip_path, output_path, mode)."""

    def test_full_mode_includes_all_ranks(self, tmp_path):
        """Verifie qu'en mode 'full', toutes les lignes du royaume Animalia
        sont extraites, quel que soit le rang (species, genus, family, etc.).
        On cree un ZIP avec Taxon.tsv contenant des lignes Animalia de rangs
        varies et des lignes Plantae. Seules les Animalia doivent etre dans
        la sortie."""
        zip_path = tmp_path / "backbone.zip"
        output_path = tmp_path / "taxa.tsv"

        rows = [
            _make_taxon_row(taxon_id="1", rank="species", kingdom="Animalia"),
            _make_taxon_row(taxon_id="2", rank="genus", kingdom="Animalia"),
            _make_taxon_row(taxon_id="3", rank="family", kingdom="Animalia"),
            _make_taxon_row(taxon_id="4", rank="order", kingdom="Animalia"),
            _make_taxon_row(taxon_id="10", rank="species", kingdom="Plantae"),
            _make_taxon_row(taxon_id="11", rank="genus", kingdom="Plantae"),
        ]
        _create_backbone_zip(zip_path, taxon_rows=rows)

        count, ids = extract_and_filter_taxa(zip_path, output_path, mode="full")

        assert count == 4
        assert ids == {1, 2, 3, 4}
        result_rows = _read_tsv(output_path)
        assert len(result_rows) == 4

    def test_minimal_mode_species_only(self, tmp_path):
        """Verifie qu'en mode 'minimal', seules les lignes de rang 'species'
        du royaume Animalia sont extraites. Les genus, family, etc. sont exclus."""
        zip_path = tmp_path / "backbone.zip"
        output_path = tmp_path / "taxa.tsv"

        rows = [
            _make_taxon_row(taxon_id="1", rank="species", kingdom="Animalia"),
            _make_taxon_row(taxon_id="2", rank="genus", kingdom="Animalia"),
            _make_taxon_row(taxon_id="3", rank="family", kingdom="Animalia"),
            _make_taxon_row(
                taxon_id="4",
                rank="species",
                kingdom="Animalia",
                scientific_name="Felis catus",
                canonical_name="Felis catus",
            ),
        ]
        _create_backbone_zip(zip_path, taxon_rows=rows)

        count, ids = extract_and_filter_taxa(zip_path, output_path, mode="minimal")

        assert count == 2
        assert ids == {1, 4}
        result_rows = _read_tsv(output_path)
        assert len(result_rows) == 2

    def test_filters_non_animalia(self, tmp_path):
        """Verifie que les lignes dont le royaume n'est pas 'Animalia'
        (Plantae, Fungi, etc.) sont filtrees."""
        zip_path = tmp_path / "backbone.zip"
        output_path = tmp_path / "taxa.tsv"

        rows = [
            _make_taxon_row(taxon_id="1", kingdom="Animalia"),
            _make_taxon_row(taxon_id="2", kingdom="Plantae"),
            _make_taxon_row(taxon_id="3", kingdom="Fungi"),
            _make_taxon_row(taxon_id="4", kingdom="Bacteria"),
        ]
        _create_backbone_zip(zip_path, taxon_rows=rows)

        count, ids = extract_and_filter_taxa(zip_path, output_path, mode="full")

        assert count == 1
        assert ids == {1}

    def test_skips_short_rows(self, tmp_path):
        """Verifie que les lignes avec moins de colonnes que prevu sont
        ignorees silencieusement sans causer d'erreur."""
        zip_path = tmp_path / "backbone.zip"
        output_path = tmp_path / "taxa.tsv"

        # Create a ZIP with raw content including a short row
        taxon_header = [""] * 23
        for col_name, idx in TAXON_COLUMNS.items():
            taxon_header[idx] = col_name

        buf = io.StringIO()
        writer = csv.writer(
            buf, delimiter="\t", quoting=csv.QUOTE_NONE, escapechar="\\"
        )
        writer.writerow(taxon_header)
        # Valid row
        writer.writerow(
            _make_taxon_row(taxon_id="1", kingdom="Animalia", rank="species")
        )
        # Short row (only 5 columns)
        writer.writerow(["short", "row", "only", "five", "cols"])
        # Another valid row
        writer.writerow(
            _make_taxon_row(taxon_id="2", kingdom="Animalia", rank="species")
        )

        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("Taxon.tsv", buf.getvalue().encode("utf-8"))

        count, ids = extract_and_filter_taxa(zip_path, output_path, mode="full")

        assert count == 2
        assert ids == {1, 2}

    def test_missing_taxon_file_raises(self, tmp_path):
        """Verifie que si le ZIP ne contient pas 'Taxon.tsv',
        FileNotFoundError est levee."""
        zip_path = tmp_path / "backbone.zip"
        output_path = tmp_path / "taxa.tsv"

        # Create a ZIP without Taxon.tsv
        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("SomeOtherFile.txt", "nothing here")

        with pytest.raises(FileNotFoundError, match="Taxon.tsv not found"):
            extract_and_filter_taxa(zip_path, output_path, mode="full")

    def test_returns_count_and_id_set(self, tmp_path):
        """Verifie que la fonction retourne (count, set_of_taxon_ids)
        avec le bon nombre de lignes et les bons IDs."""
        zip_path = tmp_path / "backbone.zip"
        output_path = tmp_path / "taxa.tsv"

        rows = [
            _make_taxon_row(taxon_id="100", kingdom="Animalia", rank="species"),
            _make_taxon_row(taxon_id="200", kingdom="Animalia", rank="genus"),
            _make_taxon_row(taxon_id="300", kingdom="Animalia", rank="family"),
        ]
        _create_backbone_zip(zip_path, taxon_rows=rows)

        count, ids = extract_and_filter_taxa(zip_path, output_path, mode="full")

        assert isinstance(count, int)
        assert isinstance(ids, set)
        assert count == 3
        assert ids == {100, 200, 300}

    def test_output_tsv_has_correct_columns(self, tmp_path):
        """Verifie que le fichier TSV de sortie a exactement les 13 colonnes
        attendues (TAXON_COLUMNS), sans en-tete."""
        zip_path = tmp_path / "backbone.zip"
        output_path = tmp_path / "taxa.tsv"

        rows = [
            _make_taxon_row(
                taxon_id="42",
                scientific_name="Canis lupus Linnaeus, 1758",
                canonical_name="Canis lupus",
                rank="species",
                kingdom="Animalia",
                phylum="Chordata",
                class_="Mammalia",
                order="Carnivora",
                family="Canidae",
                genus="Canis",
                parent_id="9612",
                accepted_id="",
                taxonomic_status="accepted",
            )
        ]
        _create_backbone_zip(zip_path, taxon_rows=rows)

        extract_and_filter_taxa(zip_path, output_path, mode="full")

        result_rows = _read_tsv(output_path)
        assert len(result_rows) == 1

        row = result_rows[0]
        assert len(row) == 13

        # Verify column values: taxon_id, sci_name, canonical, rank, kingdom,
        # phylum, class, order, family, genus, parent_id, accepted_id, is_synonym
        assert row[0] == "42"
        assert row[1] == "Canis lupus Linnaeus, 1758"
        assert row[2] == "Canis lupus"
        assert row[3] == "species"
        assert row[4] == "Animalia"
        assert row[5] == "Chordata"
        assert row[6] == "Mammalia"
        assert row[7] == "Carnivora"
        assert row[8] == "Canidae"
        assert row[9] == "Canis"
        assert row[10] == "9612"
        assert row[11] == ""
        assert row[12] == "0"  # not a synonym


# =============================================================================
# SECTION 2 : extract_and_filter_vernacular
# =============================================================================


class TestExtractAndFilterVernacular:
    """Tests pour extract_and_filter_vernacular(zip_path, output_path, valid_ids)."""

    def test_filters_to_valid_taxon_ids(self, tmp_path):
        """Verifie que seuls les noms vernaculaires dont le taxon_id est dans
        valid_taxon_ids sont extraits. On cree un ZIP avec des noms pour les
        IDs {1, 2, 3} et on passe valid_ids={1, 3}. Seuls 2 noms doivent
        etre dans la sortie."""
        zip_path = tmp_path / "backbone.zip"
        output_path = tmp_path / "vernacular.tsv"

        vernacular_rows = [
            _make_vernacular_row(taxon_id="1", name="Wolf", language="en"),
            _make_vernacular_row(taxon_id="2", name="Cat", language="en"),
            _make_vernacular_row(taxon_id="3", name="Eagle", language="en"),
        ]
        _create_backbone_zip(zip_path, taxon_rows=[], vernacular_rows=vernacular_rows)

        count = extract_and_filter_vernacular(
            zip_path, output_path, valid_taxon_ids={1, 3}
        )

        assert count == 2
        result_rows = _read_tsv(output_path)
        assert len(result_rows) == 2
        extracted_ids = {row[0] for row in result_rows}
        assert extracted_ids == {"1", "3"}

    def test_skips_short_rows(self, tmp_path):
        """Verifie que les lignes malformees sont ignorees."""
        zip_path = tmp_path / "backbone.zip"
        output_path = tmp_path / "vernacular.tsv"

        # Manually build the content with a short row
        header = ["taxonID", "vernacularName", "language"]
        buf = io.StringIO()
        writer = csv.writer(
            buf, delimiter="\t", quoting=csv.QUOTE_NONE, escapechar="\\"
        )
        writer.writerow(header)
        writer.writerow(["1", "Wolf", "en"])  # valid
        writer.writerow(["2"])  # short: only 1 col, < 3
        writer.writerow(["3", "Eagle", "en"])  # valid

        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("VernacularName.tsv", buf.getvalue().encode("utf-8"))

        count = extract_and_filter_vernacular(
            zip_path, output_path, valid_taxon_ids={1, 2, 3}
        )

        assert count == 2
        result_rows = _read_tsv(output_path)
        assert len(result_rows) == 2

    def test_missing_file_returns_zero(self, tmp_path):
        """Verifie que si le ZIP ne contient pas 'VernacularName.tsv',
        la fonction retourne 0 sans lever d'exception."""
        zip_path = tmp_path / "backbone.zip"
        output_path = tmp_path / "vernacular.tsv"

        # ZIP without VernacularName.tsv
        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("Taxon.tsv", "header\ndata")

        count = extract_and_filter_vernacular(
            zip_path, output_path, valid_taxon_ids={1}
        )

        assert count == 0

    def test_returns_count(self, tmp_path):
        """Verifie que la fonction retourne le nombre de noms extraits."""
        zip_path = tmp_path / "backbone.zip"
        output_path = tmp_path / "vernacular.tsv"

        vernacular_rows = [
            _make_vernacular_row(taxon_id="1", name="Wolf", language="en"),
            _make_vernacular_row(taxon_id="1", name="Loup", language="fr"),
            _make_vernacular_row(taxon_id="2", name="Cat", language="en"),
            _make_vernacular_row(taxon_id="3", name="Dog", language="en"),
        ]
        _create_backbone_zip(zip_path, taxon_rows=[], vernacular_rows=vernacular_rows)

        count = extract_and_filter_vernacular(
            zip_path, output_path, valid_taxon_ids={1, 2, 3}
        )

        assert count == 4


# =============================================================================
# SECTION 3 : build_canonical_to_taxon_ids
# =============================================================================


class TestBuildCanonicalToTaxonIds:
    """Tests pour build_canonical_to_taxon_ids(taxa_tsv)."""

    def test_builds_lowercase_mapping(self, tmp_path):
        """Verifie que la fonction cree un dict {canonical_name_lowercase: taxon_id}.
        'Canis lupus' avec ID 1 -> {'canis lupus': 1}."""
        tsv_path = tmp_path / "taxa.tsv"
        rows = [
            [
                "1",
                "Canis lupus Linnaeus",
                "Canis lupus",
                "species",
                "Animalia",
                "Chordata",
                "Mammalia",
                "Carnivora",
                "Canidae",
                "Canis",
                "",
                "",
                "0",
            ],
            [
                "2",
                "Felis catus Linnaeus",
                "Felis catus",
                "species",
                "Animalia",
                "Chordata",
                "Mammalia",
                "Carnivora",
                "Felidae",
                "Felis",
                "",
                "",
                "0",
            ],
        ]
        _create_taxa_tsv(tsv_path, rows)

        mapping = build_canonical_to_taxon_ids(tsv_path)

        assert mapping["canis lupus"] == 1
        assert mapping["felis catus"] == 2
        assert len(mapping) == 2

    def test_skips_malformed_rows(self, tmp_path):
        """Verifie que les lignes avec != 13 colonnes sont ignorees."""
        tsv_path = tmp_path / "taxa.tsv"

        with open(tsv_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(
                f, delimiter="\t", quoting=csv.QUOTE_NONE, escapechar="\\"
            )
            # Valid row (13 cols)
            writer.writerow(
                [
                    "1",
                    "Canis lupus",
                    "Canis lupus",
                    "species",
                    "Animalia",
                    "Chordata",
                    "Mammalia",
                    "Carnivora",
                    "Canidae",
                    "Canis",
                    "",
                    "",
                    "0",
                ]
            )
            # Malformed row (5 cols)
            writer.writerow(["2", "Bad", "Row", "only", "five"])
            # Malformed row (14 cols)
            writer.writerow(
                [
                    "3",
                    "Too",
                    "Many",
                    "Cols",
                    "A",
                    "B",
                    "C",
                    "D",
                    "E",
                    "F",
                    "G",
                    "H",
                    "I",
                    "J",
                ]
            )

        mapping = build_canonical_to_taxon_ids(tsv_path)

        assert len(mapping) == 1
        assert "canis lupus" in mapping

    def test_skips_empty_canonical_names(self, tmp_path):
        """Verifie que les lignes avec canonical_name vide ne sont pas ajoutees
        au dictionnaire."""
        tsv_path = tmp_path / "taxa.tsv"
        rows = [
            [
                "1",
                "Canis lupus",
                "Canis lupus",
                "species",
                "Animalia",
                "Chordata",
                "Mammalia",
                "Carnivora",
                "Canidae",
                "Canis",
                "",
                "",
                "0",
            ],
            [
                "2",
                "Some name",
                "",
                "species",
                "Animalia",
                "Chordata",
                "Mammalia",
                "Carnivora",
                "Canidae",
                "Felis",
                "",
                "",
                "0",
            ],
        ]
        _create_taxa_tsv(tsv_path, rows)

        mapping = build_canonical_to_taxon_ids(tsv_path)

        assert len(mapping) == 1
        assert "canis lupus" in mapping
        assert "" not in mapping

    def test_first_entry_wins_for_duplicates(self, tmp_path):
        """Verifie que si deux lignes ont le meme canonical_name (normalise),
        le dernier taxon_id est conserve (la source ecrase les doublons)."""
        tsv_path = tmp_path / "taxa.tsv"
        rows = [
            [
                "10",
                "Canis lupus Linnaeus",
                "Canis lupus",
                "species",
                "Animalia",
                "Chordata",
                "Mammalia",
                "Carnivora",
                "Canidae",
                "Canis",
                "",
                "",
                "0",
            ],
            [
                "20",
                "Canis lupus Other",
                "Canis lupus",
                "species",
                "Animalia",
                "Chordata",
                "Mammalia",
                "Carnivora",
                "Canidae",
                "Canis",
                "",
                "",
                "0",
            ],
        ]
        _create_taxa_tsv(tsv_path, rows)

        mapping = build_canonical_to_taxon_ids(tsv_path)

        assert "canis lupus" in mapping
        # Code does mapping[key] = value for each row, so the last entry wins
        assert mapping["canis lupus"] == 20


# =============================================================================
# SECTION 3b : _split_vernacular_names
# =============================================================================


class TestSplitVernacularNames:
    """Tests pour _split_vernacular_names(text)."""

    def test_single_name(self):
        assert _split_vernacular_names("Loup gris") == ["Loup gris"]

    def test_multiple_names(self):
        assert _split_vernacular_names("Loup gris, Loup commun, Loup") == [
            "Loup gris",
            "Loup commun",
            "Loup",
        ]

    def test_respects_parentheses(self):
        result = _split_vernacular_names(
            "Rapaces nocturnes (Chouettes, Hiboux), Strigiformes"
        )
        assert result == ["Rapaces nocturnes (Chouettes, Hiboux)", "Strigiformes"]

    def test_strips_whitespace(self):
        assert _split_vernacular_names("  Loup gris ,  Loup commun  ") == [
            "Loup gris",
            "Loup commun",
        ]

    def test_empty_string(self):
        assert _split_vernacular_names("") == []

    def test_trailing_comma(self):
        assert _split_vernacular_names("Loup gris,") == ["Loup gris"]


# =============================================================================
# SECTION 4 : parse_taxref_french_names
# =============================================================================


class TestParseTaxrefFrenchNames:
    """Tests pour parse_taxref_french_names(taxref_path)."""

    def test_filters_animalia(self, tmp_path):
        """Verifie que seules les entrees du regne Animalia sont extraites.
        Les entrees Plantae sont ignorees."""
        taxref_path = tmp_path / "TAXREF.txt"
        rows = [
            {"REGNE": "Animalia", "NOM_VERN": "Loup gris", "LB_NOM": "Canis lupus"},
            {"REGNE": "Plantae", "NOM_VERN": "Chene", "LB_NOM": "Quercus robur"},
            {
                "REGNE": "Animalia",
                "NOM_VERN": "Chat domestique",
                "LB_NOM": "Felis catus",
            },
        ]
        _create_taxref_file(taxref_path, rows)

        entries = parse_taxref_french_names(taxref_path)

        assert len(entries) == 2
        canonical_names = {e["canonical_name"] for e in entries}
        assert "Canis lupus" in canonical_names
        assert "Felis catus" in canonical_names
        assert "Quercus robur" not in canonical_names

    def test_extracts_canonical_name(self, tmp_path):
        """Verifie que le nom canonique est extrait depuis LB_NOM via
        extract_canonical_name (suppression des autorites et annees)."""
        taxref_path = tmp_path / "TAXREF.txt"
        rows = [
            {
                "REGNE": "Animalia",
                "NOM_VERN": "Loup gris",
                "LB_NOM": "Canis lupus Linnaeus, 1758",
            }
        ]
        _create_taxref_file(taxref_path, rows)

        entries = parse_taxref_french_names(taxref_path)

        assert len(entries) == 1
        assert entries[0]["canonical_name"] == "Canis lupus"

    def test_deduplicates(self, tmp_path):
        """Verifie que les doublons (meme canonical_name + meme nom vernaculaire)
        ne sont comptes qu'une fois."""
        taxref_path = tmp_path / "TAXREF.txt"
        rows = [
            {"REGNE": "Animalia", "NOM_VERN": "Loup gris", "LB_NOM": "Canis lupus"},
            {"REGNE": "Animalia", "NOM_VERN": "Loup gris", "LB_NOM": "Canis lupus"},
            {"REGNE": "Animalia", "NOM_VERN": "Loup gris", "LB_NOM": "Canis lupus"},
        ]
        _create_taxref_file(taxref_path, rows)

        entries = parse_taxref_french_names(taxref_path)

        assert len(entries) == 1

    def test_skips_empty_vernacular_names(self, tmp_path):
        """Verifie que les entrees sans NOM_VERN sont ignorees."""
        taxref_path = tmp_path / "TAXREF.txt"
        rows = [
            {"REGNE": "Animalia", "NOM_VERN": "", "LB_NOM": "Canis lupus"},
            {
                "REGNE": "Animalia",
                "NOM_VERN": "Chat domestique",
                "LB_NOM": "Felis catus",
            },
            {"REGNE": "Animalia", "NOM_VERN": "  ", "LB_NOM": "Ursus arctos"},
        ]
        _create_taxref_file(taxref_path, rows)

        entries = parse_taxref_french_names(taxref_path)

        assert len(entries) == 1
        assert entries[0]["french_name"] == "Chat domestique"

    def test_splits_comma_separated_names(self, tmp_path):
        """Verifie que si NOM_VERN contient des noms separes par des virgules
        (ex: 'Loup gris, Loup commun'), chaque nom donne une entree distincte."""
        taxref_path = tmp_path / "TAXREF.txt"
        rows = [
            {
                "REGNE": "Animalia",
                "NOM_VERN": "Loup gris, Loup commun",
                "LB_NOM": "Canis lupus",
            }
        ]
        _create_taxref_file(taxref_path, rows)

        entries = parse_taxref_french_names(taxref_path)

        assert len(entries) == 2
        names = {e["french_name"] for e in entries}
        assert names == {"Loup gris", "Loup commun"}

    def test_splits_respects_parentheses(self, tmp_path):
        """Verifie que les virgules a l'interieur de parentheses ne sont pas
        utilisees comme separateurs de noms."""
        taxref_path = tmp_path / "TAXREF.txt"
        rows = [
            {
                "REGNE": "Animalia",
                "NOM_VERN": "Rapaces nocturnes (Chouettes, Hiboux), Strigiformes",
                "LB_NOM": "Strigiformes",
            }
        ]
        _create_taxref_file(taxref_path, rows)

        entries = parse_taxref_french_names(taxref_path)

        assert len(entries) == 2
        names = {e["french_name"] for e in entries}
        assert names == {"Rapaces nocturnes (Chouettes, Hiboux)", "Strigiformes"}


# =============================================================================
# SECTION 5 : merge_taxref_into_vernacular
# =============================================================================


class TestMergeTaxrefIntoVernacular:
    """Tests pour merge_taxref_into_vernacular(tsv, entries, canonical_to_id)."""

    def test_appends_new_names(self, tmp_path):
        """Verifie que les noms TAXREF sont ajoutes a la fin du fichier TSV
        vernaculaire existant. On cree un TSV avec 2 noms, on fusionne
        2 noms TAXREF, et on verifie que le TSV contient 4 lignes."""
        tsv_path = tmp_path / "vernacular.tsv"
        _create_vernacular_tsv(tsv_path, [["1", "Wolf", "en"], ["2", "Cat", "en"]])

        taxref_entries = [
            {"canonical_name": "Canis lupus", "french_name": "Loup gris"},
            {"canonical_name": "Felis catus", "french_name": "Chat domestique"},
        ]
        canonical_to_id = {"canis lupus": 1, "felis catus": 2}

        added, no_match = merge_taxref_into_vernacular(
            tsv_path, taxref_entries, canonical_to_id
        )

        assert added == 2
        result_rows = _read_tsv(tsv_path)
        assert len(result_rows) == 4

        # Verify the appended rows
        new_rows = result_rows[2:]
        assert new_rows[0] == ["1", "Loup gris", "fr"]
        assert new_rows[1] == ["2", "Chat domestique", "fr"]

    def test_deduplicates_existing_names(self, tmp_path):
        """Verifie que si un nom TAXREF existe deja dans le TSV (meme
        taxon_id + meme nom vernaculaire normalise), il n'est pas ajoute
        en double."""
        tsv_path = tmp_path / "vernacular.tsv"
        _create_vernacular_tsv(tsv_path, [["1", "Loup gris", "fr"]])

        taxref_entries = [{"canonical_name": "Canis lupus", "french_name": "Loup gris"}]
        canonical_to_id = {"canis lupus": 1}

        added, no_match = merge_taxref_into_vernacular(
            tsv_path, taxref_entries, canonical_to_id
        )

        assert added == 0
        result_rows = _read_tsv(tsv_path)
        assert len(result_rows) == 1

    def test_counts_unmatched_canonical_names(self, tmp_path):
        """Verifie que la fonction retourne le nombre de noms TAXREF dont
        le canonical_name n'a pas de correspondance dans canonical_to_id."""
        tsv_path = tmp_path / "vernacular.tsv"
        _create_vernacular_tsv(tsv_path, [])

        taxref_entries = [
            {"canonical_name": "Canis lupus", "french_name": "Loup gris"},
            {"canonical_name": "Unknown species", "french_name": "Espece inconnue"},
            {"canonical_name": "Another missing", "french_name": "Autre"},
        ]
        # Only Canis lupus is mapped
        canonical_to_id = {"canis lupus": 1}

        added, no_match = merge_taxref_into_vernacular(
            tsv_path, taxref_entries, canonical_to_id
        )

        assert added == 1
        assert no_match == 2

    def test_returns_added_and_skipped_counts(self, tmp_path):
        """Verifie que la fonction retourne (added_count, no_match_count)."""
        tsv_path = tmp_path / "vernacular.tsv"
        _create_vernacular_tsv(
            tsv_path,
            [
                ["1", "Loup gris", "fr"]  # Will cause dedup for first entry
            ],
        )

        taxref_entries = [
            # dup -> skipped (exists in TSV)
            {"canonical_name": "Canis lupus", "french_name": "Loup gris"},
            # new -> added
            {"canonical_name": "Canis lupus", "french_name": "Loup"},
            # no match in canonical_to_id
            {"canonical_name": "No match sp", "french_name": "Rien"},
        ]
        canonical_to_id = {"canis lupus": 1}

        result = merge_taxref_into_vernacular(tsv_path, taxref_entries, canonical_to_id)

        assert isinstance(result, tuple)
        assert len(result) == 2
        added, no_match = result
        assert added == 1  # "Loup" was added
        assert no_match == 1  # "No match sp" not found


# =============================================================================
# SECTION 6 : cleanup_taxa_without_vernacular
# =============================================================================


class TestCleanupTaxaWithoutVernacular:
    """Tests pour cleanup_taxa_without_vernacular(taxa, vernacular, output)."""

    def test_removes_taxa_without_names(self, tmp_path):
        """Verifie que les taxa qui n'ont aucun nom vernaculaire dans le
        fichier vernacular sont supprimes. On cree un TSV taxa avec IDs
        {1, 2, 3} et un vernacular avec IDs {1, 3}. La sortie ne doit
        contenir que les IDs 1 et 3."""
        taxa_path = tmp_path / "taxa.tsv"
        vernacular_path = tmp_path / "vernacular.tsv"
        output_path = tmp_path / "taxa_clean.tsv"

        _create_taxa_tsv(
            taxa_path,
            [
                [
                    "1",
                    "Canis lupus",
                    "Canis lupus",
                    "species",
                    "Animalia",
                    "Chordata",
                    "Mammalia",
                    "Carnivora",
                    "Canidae",
                    "Canis",
                    "",
                    "",
                    "0",
                ],
                [
                    "2",
                    "Felis catus",
                    "Felis catus",
                    "species",
                    "Animalia",
                    "Chordata",
                    "Mammalia",
                    "Carnivora",
                    "Felidae",
                    "Felis",
                    "",
                    "",
                    "0",
                ],
                [
                    "3",
                    "Aquila chrysaetos",
                    "Aquila chrysaetos",
                    "species",
                    "Animalia",
                    "Chordata",
                    "Aves",
                    "Accipitriformes",
                    "Accipitridae",
                    "Aquila",
                    "",
                    "",
                    "0",
                ],
            ],
        )
        _create_vernacular_tsv(
            vernacular_path, [["1", "Wolf", "en"], ["3", "Golden Eagle", "en"]]
        )

        kept, removed = cleanup_taxa_without_vernacular(
            taxa_path, vernacular_path, output_path
        )

        assert kept == 2
        assert removed == 1
        result_rows = _read_tsv(output_path)
        result_ids = {row[0] for row in result_rows}
        assert result_ids == {"1", "3"}

    def test_keeps_taxa_with_names(self, tmp_path):
        """Verifie que les taxa ayant au moins un nom vernaculaire sont
        conserves."""
        taxa_path = tmp_path / "taxa.tsv"
        vernacular_path = tmp_path / "vernacular.tsv"
        output_path = tmp_path / "taxa_clean.tsv"

        _create_taxa_tsv(
            taxa_path,
            [
                [
                    "10",
                    "Canis lupus",
                    "Canis lupus",
                    "species",
                    "Animalia",
                    "Chordata",
                    "Mammalia",
                    "Carnivora",
                    "Canidae",
                    "Canis",
                    "",
                    "",
                    "0",
                ],
                [
                    "20",
                    "Felis catus",
                    "Felis catus",
                    "species",
                    "Animalia",
                    "Chordata",
                    "Mammalia",
                    "Carnivora",
                    "Felidae",
                    "Felis",
                    "",
                    "",
                    "0",
                ],
            ],
        )
        _create_vernacular_tsv(
            vernacular_path,
            [["10", "Wolf", "en"], ["10", "Loup", "fr"], ["20", "Cat", "en"]],
        )

        kept, removed = cleanup_taxa_without_vernacular(
            taxa_path, vernacular_path, output_path
        )

        assert kept == 2
        assert removed == 0
        result_rows = _read_tsv(output_path)
        assert len(result_rows) == 2

    def test_returns_kept_and_removed_counts(self, tmp_path):
        """Verifie que la fonction retourne (kept_count, removed_count)."""
        taxa_path = tmp_path / "taxa.tsv"
        vernacular_path = tmp_path / "vernacular.tsv"
        output_path = tmp_path / "taxa_clean.tsv"

        _create_taxa_tsv(
            taxa_path,
            [
                ["1", "S1", "S1", "species", "A", "C", "M", "O", "F", "G", "", "", "0"],
                ["2", "S2", "S2", "species", "A", "C", "M", "O", "F", "G", "", "", "0"],
                ["3", "S3", "S3", "species", "A", "C", "M", "O", "F", "G", "", "", "0"],
                ["4", "S4", "S4", "species", "A", "C", "M", "O", "F", "G", "", "", "0"],
                ["5", "S5", "S5", "species", "A", "C", "M", "O", "F", "G", "", "", "0"],
            ],
        )
        _create_vernacular_tsv(
            vernacular_path, [["1", "Name1", "en"], ["3", "Name3", "en"]]
        )

        result = cleanup_taxa_without_vernacular(
            taxa_path, vernacular_path, output_path
        )

        assert isinstance(result, tuple)
        assert len(result) == 2
        kept, removed = result
        assert kept == 2
        assert removed == 3


# =============================================================================
# SECTION 7 : generate_distribution (pipeline complet)
# =============================================================================


class TestGenerateDistribution:
    """Tests pour generate_distribution(mode, backbone_path, taxref_path, output_dir)."""

    @patch("daynimal.db.generate_distribution.download_backbone")
    def test_downloads_backbone_if_missing(self, mock_download, tmp_path):
        """Verifie que si backbone_path est None, la fonction appelle
        download_backbone() pour telecharger le ZIP."""
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        # download_backbone should create the zip file when called
        def fake_download(dest_path):
            _create_backbone_zip(
                dest_path,
                taxon_rows=[
                    _make_taxon_row(taxon_id="1", kingdom="Animalia", rank="species")
                ],
                vernacular_rows=[
                    _make_vernacular_row(taxon_id="1", name="Wolf", language="en")
                ],
            )
            return dest_path

        mock_download.side_effect = fake_download

        generate_distribution(
            mode="minimal", backbone_path=None, taxref_path=None, output_dir=output_dir
        )

        mock_download.assert_called_once()
        # The argument should be output_dir / "backbone.zip"
        call_args = mock_download.call_args[0]
        assert str(call_args[0]).endswith("backbone.zip")

    def test_minimal_mode_with_taxref(self, tmp_path):
        """Verifie le pipeline complet en mode minimal avec TAXREF:
        1. Extraction des taxa (species only)
        2. Extraction des noms vernaculaires
        3. Fusion TAXREF
        4. Cleanup des taxa sans noms
        5. Fichiers finaux avec suffixe '_minimal'."""
        zip_path = tmp_path / "backbone.zip"
        output_dir = tmp_path / "output"
        taxref_path = tmp_path / "TAXREF.txt"

        # Create backbone with species and genus
        taxon_rows = [
            _make_taxon_row(
                taxon_id="1",
                scientific_name="Canis lupus",
                canonical_name="Canis lupus",
                rank="species",
                kingdom="Animalia",
            ),
            _make_taxon_row(
                taxon_id="2",
                scientific_name="Felis catus",
                canonical_name="Felis catus",
                rank="species",
                kingdom="Animalia",
            ),
            _make_taxon_row(
                taxon_id="3",
                scientific_name="Aquila chrysaetos",
                canonical_name="Aquila chrysaetos",
                rank="species",
                kingdom="Animalia",
            ),
            _make_taxon_row(
                taxon_id="4",
                scientific_name="Canidae",
                canonical_name="Canidae",
                rank="family",
                kingdom="Animalia",
            ),
        ]
        vernacular_rows = [
            _make_vernacular_row(taxon_id="1", name="Wolf", language="en"),
            _make_vernacular_row(taxon_id="2", name="Cat", language="en"),
            # No vernacular for ID 3 (Aquila) from GBIF
        ]
        _create_backbone_zip(
            zip_path, taxon_rows=taxon_rows, vernacular_rows=vernacular_rows
        )

        # Create TAXREF with a French name for Aquila
        _create_taxref_file(
            taxref_path,
            [
                {
                    "REGNE": "Animalia",
                    "NOM_VERN": "Aigle royal",
                    "LB_NOM": "Aquila chrysaetos",
                },
                {"REGNE": "Animalia", "NOM_VERN": "Loup gris", "LB_NOM": "Canis lupus"},
            ],
        )

        generate_distribution(
            mode="minimal",
            backbone_path=zip_path,
            taxref_path=taxref_path,
            output_dir=output_dir,
        )

        # Check output files exist with '_minimal' suffix
        taxa_file = output_dir / "animalia_taxa_minimal.tsv"
        vern_file = output_dir / "animalia_vernacular_minimal.tsv"
        assert taxa_file.exists()
        assert vern_file.exists()

        # Minimal mode: only species, after cleanup only taxa with vernacular
        taxa_rows_result = _read_tsv(taxa_file)
        taxa_ids = {row[0] for row in taxa_rows_result}
        # All 3 species should remain (ID 3 got a name via TAXREF)
        assert "1" in taxa_ids
        assert "2" in taxa_ids
        assert "3" in taxa_ids
        # Family (ID 4) excluded by minimal mode
        assert "4" not in taxa_ids

        # Vernacular should include GBIF names + TAXREF French names
        vern_rows_result = _read_tsv(vern_file)
        vern_names = {(row[0], row[1]) for row in vern_rows_result}
        assert ("1", "Wolf") in vern_names
        assert ("2", "Cat") in vern_names
        assert ("3", "Aigle royal") in vern_names

    def test_minimal_mode_without_taxref(self, tmp_path):
        """Verifie le pipeline en mode minimal sans TAXREF:
        pas de fusion, mais le cleanup est quand meme effectue."""
        zip_path = tmp_path / "backbone.zip"
        output_dir = tmp_path / "output"

        taxon_rows = [
            _make_taxon_row(
                taxon_id="1",
                scientific_name="Canis lupus",
                canonical_name="Canis lupus",
                rank="species",
                kingdom="Animalia",
            ),
            _make_taxon_row(
                taxon_id="2",
                scientific_name="Felis catus",
                canonical_name="Felis catus",
                rank="species",
                kingdom="Animalia",
            ),
            _make_taxon_row(
                taxon_id="3",
                scientific_name="No Name Species",
                canonical_name="No Name Species",
                rank="species",
                kingdom="Animalia",
            ),
        ]
        vernacular_rows = [
            _make_vernacular_row(taxon_id="1", name="Wolf", language="en"),
            _make_vernacular_row(taxon_id="2", name="Cat", language="en"),
            # No vernacular for ID 3
        ]
        _create_backbone_zip(
            zip_path, taxon_rows=taxon_rows, vernacular_rows=vernacular_rows
        )

        generate_distribution(
            mode="minimal",
            backbone_path=zip_path,
            taxref_path=None,
            output_dir=output_dir,
        )

        taxa_file = output_dir / "animalia_taxa_minimal.tsv"
        vern_file = output_dir / "animalia_vernacular_minimal.tsv"
        assert taxa_file.exists()
        assert vern_file.exists()

        # After cleanup, ID 3 should be removed (no vernacular names)
        taxa_rows_result = _read_tsv(taxa_file)
        taxa_ids = {row[0] for row in taxa_rows_result}
        assert taxa_ids == {"1", "2"}

    def test_full_mode(self, tmp_path):
        """Verifie le pipeline en mode full: pas de cleanup,
        tous les rangs sont inclus. Les fichiers n'ont pas de suffixe
        '_minimal'."""
        zip_path = tmp_path / "backbone.zip"
        output_dir = tmp_path / "output"

        taxon_rows = [
            _make_taxon_row(taxon_id="1", rank="species", kingdom="Animalia"),
            _make_taxon_row(taxon_id="2", rank="genus", kingdom="Animalia"),
            _make_taxon_row(taxon_id="3", rank="family", kingdom="Animalia"),
            _make_taxon_row(
                taxon_id="4",
                rank="species",
                kingdom="Animalia",
                scientific_name="No vernac",
                canonical_name="No vernac",
            ),
        ]
        vernacular_rows = [
            _make_vernacular_row(taxon_id="1", name="Wolf", language="en")
        ]
        _create_backbone_zip(
            zip_path, taxon_rows=taxon_rows, vernacular_rows=vernacular_rows
        )

        generate_distribution(
            mode="full", backbone_path=zip_path, taxref_path=None, output_dir=output_dir
        )

        # Full mode: no '_minimal' suffix
        taxa_file = output_dir / "animalia_taxa.tsv"
        vern_file = output_dir / "animalia_vernacular.tsv"
        assert taxa_file.exists()
        assert vern_file.exists()

        # Full mode: all ranks, no cleanup, so all 4 taxa remain
        taxa_rows_result = _read_tsv(taxa_file)
        assert len(taxa_rows_result) == 4

        # No cleanup means ID 4 (without vernacular) is still present
        taxa_ids = {row[0] for row in taxa_rows_result}
        assert taxa_ids == {"1", "2", "3", "4"}

    def test_output_files_exist(self, tmp_path):
        """Verifie que les fichiers de sortie (taxa TSV et vernacular TSV)
        sont crees dans le repertoire output_dir."""
        zip_path = tmp_path / "backbone.zip"
        output_dir = tmp_path / "output"

        taxon_rows = [_make_taxon_row(taxon_id="1", rank="species", kingdom="Animalia")]
        vernacular_rows = [
            _make_vernacular_row(taxon_id="1", name="Wolf", language="en")
        ]
        _create_backbone_zip(
            zip_path, taxon_rows=taxon_rows, vernacular_rows=vernacular_rows
        )

        generate_distribution(
            mode="minimal",
            backbone_path=zip_path,
            taxref_path=None,
            output_dir=output_dir,
        )

        assert (output_dir / "animalia_taxa_minimal.tsv").exists()
        assert (output_dir / "animalia_vernacular_minimal.tsv").exists()

        # Run again in full mode
        generate_distribution(
            mode="full", backbone_path=zip_path, taxref_path=None, output_dir=output_dir
        )

        assert (output_dir / "animalia_taxa.tsv").exists()
        assert (output_dir / "animalia_vernacular.tsv").exists()
