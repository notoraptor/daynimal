"""Tests pour daynimal/db/import_gbif_utils.py — Utilitaires GBIF.

Couvre: extract_canonical_name, parse_int, download_backbone, constantes.

Stratégie: extract_canonical_name et parse_int sont des fonctions pures
facilement testables. download_backbone nécessite le mock de httpx.
"""

from unittest.mock import patch, MagicMock


from daynimal.db.import_gbif_utils import (
    extract_canonical_name,
    parse_int,
    download_backbone,
    GBIF_BACKBONE_URL,
    TAXON_COLUMNS,
    VERNACULAR_COLUMNS,
)


# =============================================================================
# SECTION 1 : extract_canonical_name
# =============================================================================


class TestExtractCanonicalName:
    """Tests pour extract_canonical_name(scientific_name)."""

    def test_genus_species(self):
        """Vérifie que 'Canis lupus' retourne 'Canis lupus' (déjà canonique)."""
        assert extract_canonical_name("Canis lupus") == "Canis lupus"

    def test_with_authority(self):
        """Vérifie que 'Canis lupus Linnaeus, 1758' retourne 'Canis lupus'."""
        assert extract_canonical_name("Canis lupus Linnaeus, 1758") == "Canis lupus"

    def test_with_parenthetical_authority(self):
        """Vérifie que 'Ursus arctos (Linnaeus, 1758)' retourne 'Ursus arctos'."""
        assert extract_canonical_name("Ursus arctos (Linnaeus, 1758)") == "Ursus arctos"

    def test_with_year_only(self):
        """Vérifie que 'Panthera leo 1758' retourne 'Panthera leo'."""
        assert extract_canonical_name("Panthera leo 1758") == "Panthera leo"

    def test_single_word(self):
        """Vérifie que 'Animalia' (un seul mot) retourne 'Animalia'."""
        assert extract_canonical_name("Animalia") == "Animalia"

    def test_subspecies(self):
        """Vérifie que 'Canis lupus familiaris Linnaeus' retourne 'Canis lupus'."""
        assert (
            extract_canonical_name("Canis lupus familiaris Linnaeus") == "Canis lupus"
        )

    def test_empty_string(self):
        """Vérifie que '' retourne ''."""
        assert extract_canonical_name("") == ""

    def test_complex_authority(self):
        """Vérifie que 'Balaenoptera musculus (Linnaeus, 1758) ssp. indica'
        retourne 'Balaenoptera musculus'."""
        result = extract_canonical_name(
            "Balaenoptera musculus (Linnaeus, 1758) ssp. indica"
        )
        assert result == "Balaenoptera musculus"


# =============================================================================
# SECTION 2 : parse_int
# =============================================================================


class TestParseInt:
    """Tests pour parse_int(value)."""

    def test_valid_integer(self):
        """Vérifie que '42' retourne 42."""
        assert parse_int("42") == 42

    def test_empty_string(self):
        """Vérifie que '' retourne None."""
        assert parse_int("") is None

    def test_whitespace(self):
        """Vérifie que '  ' (espaces) retourne None."""
        assert parse_int("  ") is None

    def test_non_numeric(self):
        """Vérifie que 'abc' retourne None."""
        assert parse_int("abc") is None

    def test_none_input(self):
        """Vérifie que None retourne None."""
        assert parse_int(None) is None

    def test_negative_integer(self):
        """Vérifie que '-5' retourne -5."""
        assert parse_int("-5") == -5

    def test_zero(self):
        """Vérifie que '0' retourne 0."""
        assert parse_int("0") == 0


# =============================================================================
# SECTION 3 : download_backbone
# =============================================================================


class TestDownloadBackbone:
    """Tests pour download_backbone(dest_path)."""

    @patch("daynimal.db.import_gbif_utils.httpx.stream")
    @patch("daynimal.db.import_gbif_utils.httpx.head")
    def test_fresh_download(self, mock_head, mock_stream, tmp_path):
        """Vérifie qu'un téléchargement frais télécharge le fichier complet."""
        dest = tmp_path / "backbone.zip"

        # Mock HEAD response
        mock_head_response = MagicMock()
        mock_head_response.headers = {
            "content-length": "1000",
            "accept-ranges": "bytes",
        }
        mock_head_response.raise_for_status = MagicMock()
        mock_head.return_value = mock_head_response

        # Mock stream response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.iter_bytes.return_value = [b"x" * 1000]
        mock_stream.return_value.__enter__ = MagicMock(return_value=mock_response)
        mock_stream.return_value.__exit__ = MagicMock(return_value=False)

        result = download_backbone(dest)

        assert result == dest
        assert dest.exists()
        mock_stream.assert_called_once()

    @patch("daynimal.db.import_gbif_utils.httpx.stream")
    @patch("daynimal.db.import_gbif_utils.httpx.head")
    def test_resume_partial_download(self, mock_head, mock_stream, tmp_path):
        """Vérifie que si un fichier .partial existe, le téléchargement reprend."""
        dest = tmp_path / "backbone.zip"
        partial = dest.with_suffix(".zip.partial")
        partial.write_bytes(b"x" * 100)

        # Mock HEAD
        mock_head_response = MagicMock()
        mock_head_response.headers = {
            "content-length": "1000",
            "accept-ranges": "bytes",
        }
        mock_head_response.raise_for_status = MagicMock()
        mock_head.return_value = mock_head_response

        # Mock stream
        mock_response = MagicMock()
        mock_response.status_code = 206
        mock_response.iter_bytes.return_value = [b"y" * 900]
        mock_stream.return_value.__enter__ = MagicMock(return_value=mock_response)
        mock_stream.return_value.__exit__ = MagicMock(return_value=False)

        result = download_backbone(dest)

        assert result == dest
        # Verify Range header was sent
        stream_call = mock_stream.call_args
        assert stream_call[1]["headers"] == {"Range": "bytes=100-"}

    @patch("daynimal.db.import_gbif_utils.httpx.head")
    def test_already_complete(self, mock_head, tmp_path):
        """Vérifie que si le fichier .partial est déjà complet, pas de re-téléchargement."""
        dest = tmp_path / "backbone.zip"
        partial = dest.with_suffix(".zip.partial")
        partial.write_bytes(b"x" * 1000)

        mock_head_response = MagicMock()
        mock_head_response.headers = {
            "content-length": "1000",
            "accept-ranges": "bytes",
        }
        mock_head_response.raise_for_status = MagicMock()
        mock_head.return_value = mock_head_response

        result = download_backbone(dest)

        assert result == dest
        assert dest.exists()

    @patch("daynimal.db.import_gbif_utils.httpx.stream")
    @patch("daynimal.db.import_gbif_utils.httpx.head")
    def test_server_no_resume_support(self, mock_head, mock_stream, tmp_path):
        """Vérifie que sans Accept-Ranges, le téléchargement recommence."""
        dest = tmp_path / "backbone.zip"
        partial = dest.with_suffix(".zip.partial")
        partial.write_bytes(b"x" * 100)

        mock_head_response = MagicMock()
        mock_head_response.headers = {"content-length": "1000"}
        mock_head_response.raise_for_status = MagicMock()
        mock_head.return_value = mock_head_response

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.iter_bytes.return_value = [b"y" * 1000]
        mock_stream.return_value.__enter__ = MagicMock(return_value=mock_response)
        mock_stream.return_value.__exit__ = MagicMock(return_value=False)

        result = download_backbone(dest)

        assert result == dest
        # Should NOT send Range header
        stream_call = mock_stream.call_args
        assert stream_call[1]["headers"] == {}


# =============================================================================
# SECTION 4 : Constants
# =============================================================================


class TestConstants:
    """Tests pour les constantes TAXON_COLUMNS et VERNACULAR_COLUMNS."""

    def test_taxon_columns_count(self):
        """Vérifie que TAXON_COLUMNS contient exactement 23 éléments."""
        assert len(TAXON_COLUMNS) == 23

    def test_vernacular_columns_count(self):
        """Vérifie que VERNACULAR_COLUMNS contient exactement 3 éléments."""
        assert len(VERNACULAR_COLUMNS) == 3

    def test_gbif_backbone_url(self):
        """Vérifie que GBIF_BACKBONE_URL pointe vers hosted.gbif.org."""
        assert "hosted" in GBIF_BACKBONE_URL
        assert "gbif" in GBIF_BACKBONE_URL
        assert "backbone" in GBIF_BACKBONE_URL
