"""Tests pour daynimal/db/generate_distribution.py — Génération des fichiers TSV.

Couvre: extract_and_filter_taxa, extract_and_filter_vernacular,
build_canonical_to_taxon_ids, parse_taxref_french_names,
merge_taxref_into_vernacular, cleanup_taxa_without_vernacular,
generate_distribution.

Stratégie: on crée des fichiers ZIP/TSV/TAXREF temporaires avec tmp_path
pour simuler les données d'entrée. On vérifie les fichiers de sortie
générés et les statistiques retournées.
"""

import csv
import zipfile
from unittest.mock import patch, MagicMock

import pytest


# =============================================================================
# Helpers pour créer des données de test
# =============================================================================

# Les helpers créent des fichiers ZIP simulant backbone.zip de GBIF,
# des TSV de taxa/vernacular, et des fichiers TAXREF.
# Voir la section "todo" dans chaque test pour les détails.


# =============================================================================
# SECTION 1 : extract_and_filter_taxa
# =============================================================================


class TestExtractAndFilterTaxa:
    """Tests pour extract_and_filter_taxa(zip_path, output_path, mode)."""

    def test_full_mode_includes_all_ranks(self, tmp_path):
        """Vérifie qu'en mode 'full', toutes les lignes du royaume Animalia
        sont extraites, quel que soit le rang (species, genus, family, etc.).
        On crée un ZIP avec Taxon.tsv contenant des lignes Animalia de rangs
        variés et des lignes Plantae. Seules les Animalia doivent être dans
        la sortie."""
        # todo
        pass

    def test_minimal_mode_species_only(self, tmp_path):
        """Vérifie qu'en mode 'minimal', seules les lignes de rang 'species'
        du royaume Animalia sont extraites. Les genus, family, etc. sont exclus."""
        # todo
        pass

    def test_filters_non_animalia(self, tmp_path):
        """Vérifie que les lignes dont le royaume n'est pas 'Animalia'
        (Plantae, Fungi, etc.) sont filtrées."""
        # todo
        pass

    def test_skips_short_rows(self, tmp_path):
        """Vérifie que les lignes avec moins de colonnes que prévu sont
        ignorées silencieusement sans causer d'erreur."""
        # todo
        pass

    def test_missing_taxon_file_raises(self, tmp_path):
        """Vérifie que si le ZIP ne contient pas 'Taxon.tsv',
        FileNotFoundError est levée."""
        # todo
        pass

    def test_returns_count_and_id_set(self, tmp_path):
        """Vérifie que la fonction retourne (count, set_of_taxon_ids)
        avec le bon nombre de lignes et les bons IDs."""
        # todo
        pass

    def test_output_tsv_has_correct_columns(self, tmp_path):
        """Vérifie que le fichier TSV de sortie a exactement les 13 colonnes
        attendues (TAXON_COLUMNS), sans en-tête."""
        # todo
        pass


# =============================================================================
# SECTION 2 : extract_and_filter_vernacular
# =============================================================================


class TestExtractAndFilterVernacular:
    """Tests pour extract_and_filter_vernacular(zip_path, output_path, valid_ids)."""

    def test_filters_to_valid_taxon_ids(self, tmp_path):
        """Vérifie que seuls les noms vernaculaires dont le taxon_id est dans
        valid_taxon_ids sont extraits. On crée un ZIP avec des noms pour les
        IDs {1, 2, 3} et on passe valid_ids={1, 3}. Seuls 2 noms doivent
        être dans la sortie."""
        # todo
        pass

    def test_skips_short_rows(self, tmp_path):
        """Vérifie que les lignes malformées sont ignorées."""
        # todo
        pass

    def test_missing_file_returns_zero(self, tmp_path):
        """Vérifie que si le ZIP ne contient pas 'VernacularName.tsv',
        la fonction retourne 0 sans lever d'exception."""
        # todo
        pass

    def test_returns_count(self, tmp_path):
        """Vérifie que la fonction retourne le nombre de noms extraits."""
        # todo
        pass


# =============================================================================
# SECTION 3 : build_canonical_to_taxon_ids
# =============================================================================


class TestBuildCanonicalToTaxonIds:
    """Tests pour build_canonical_to_taxon_ids(taxa_tsv)."""

    def test_builds_lowercase_mapping(self, tmp_path):
        """Vérifie que la fonction crée un dict {canonical_name_lowercase: taxon_id}.
        'Canis lupus' avec ID 1 → {'canis lupus': 1}."""
        # todo
        pass

    def test_skips_malformed_rows(self, tmp_path):
        """Vérifie que les lignes avec != 13 colonnes sont ignorées."""
        # todo
        pass

    def test_skips_empty_canonical_names(self, tmp_path):
        """Vérifie que les lignes avec canonical_name vide ne sont pas ajoutées
        au dictionnaire."""
        # todo
        pass

    def test_first_entry_wins_for_duplicates(self, tmp_path):
        """Vérifie que si deux lignes ont le même canonical_name (normalisé),
        le premier taxon_id est conservé."""
        # todo
        pass


# =============================================================================
# SECTION 4 : parse_taxref_french_names
# =============================================================================


class TestParseTaxrefFrenchNames:
    """Tests pour parse_taxref_french_names(taxref_path)."""

    def test_filters_animalia(self, tmp_path):
        """Vérifie que seules les entrées du règne Animalia sont extraites.
        Les entrées Plantae sont ignorées. Le fichier TAXREF est un CSV
        tabulé avec les colonnes REGNE, NOM_VERN, LB_NOM."""
        # todo
        pass

    def test_extracts_canonical_name(self, tmp_path):
        """Vérifie que le nom canonique est extrait depuis LB_NOM via
        extract_canonical_name (suppression des autorités et années)."""
        # todo
        pass

    def test_deduplicates(self, tmp_path):
        """Vérifie que les doublons (même canonical_name + même nom vernaculaire)
        ne sont comptés qu'une fois."""
        # todo
        pass

    def test_skips_empty_vernacular_names(self, tmp_path):
        """Vérifie que les entrées sans NOM_VERN sont ignorées."""
        # todo
        pass

    def test_splits_comma_separated_names(self, tmp_path):
        """Vérifie que si NOM_VERN contient des noms séparés par des virgules
        (ex: 'Loup gris, Loup commun'), seul le premier est utilisé."""
        # todo
        pass


# =============================================================================
# SECTION 5 : merge_taxref_into_vernacular
# =============================================================================


class TestMergeTaxrefIntoVernacular:
    """Tests pour merge_taxref_into_vernacular(tsv, entries, canonical_to_id)."""

    def test_appends_new_names(self, tmp_path):
        """Vérifie que les noms TAXREF sont ajoutés à la fin du fichier TSV
        vernaculaire existant. On crée un TSV avec 2 noms, on fusionne
        2 noms TAXREF, et on vérifie que le TSV contient 4 lignes."""
        # todo
        pass

    def test_deduplicates_existing_names(self, tmp_path):
        """Vérifie que si un nom TAXREF existe déjà dans le TSV (même
        taxon_id + même nom vernaculaire normalisé), il n'est pas ajouté
        en double."""
        # todo
        pass

    def test_counts_unmatched_canonical_names(self, tmp_path):
        """Vérifie que la fonction retourne le nombre de noms TAXREF dont
        le canonical_name n'a pas de correspondance dans canonical_to_id."""
        # todo
        pass

    def test_returns_added_and_skipped_counts(self, tmp_path):
        """Vérifie que la fonction retourne (added_count, skipped_count)."""
        # todo
        pass


# =============================================================================
# SECTION 6 : cleanup_taxa_without_vernacular
# =============================================================================


class TestCleanupTaxaWithoutVernacular:
    """Tests pour cleanup_taxa_without_vernacular(taxa, vernacular, output)."""

    def test_removes_taxa_without_names(self, tmp_path):
        """Vérifie que les taxa qui n'ont aucun nom vernaculaire dans le
        fichier vernacular sont supprimés. On crée un TSV taxa avec IDs
        {1, 2, 3} et un vernacular avec IDs {1, 3}. La sortie ne doit
        contenir que les IDs 1 et 3."""
        # todo
        pass

    def test_keeps_taxa_with_names(self, tmp_path):
        """Vérifie que les taxa ayant au moins un nom vernaculaire sont conservés."""
        # todo
        pass

    def test_returns_kept_and_removed_counts(self, tmp_path):
        """Vérifie que la fonction retourne (kept_count, removed_count)."""
        # todo
        pass


# =============================================================================
# SECTION 7 : generate_distribution (pipeline complet)
# =============================================================================


class TestGenerateDistribution:
    """Tests pour generate_distribution(mode, backbone_path, taxref_path, output_dir)."""

    @patch("daynimal.db.generate_distribution.download_backbone")
    def test_downloads_backbone_if_missing(self, mock_download, tmp_path):
        """Vérifie que si backbone_path est None, la fonction appelle
        download_backbone() pour télécharger le ZIP."""
        # todo
        pass

    def test_minimal_mode_with_taxref(self, tmp_path):
        """Vérifie le pipeline complet en mode minimal avec TAXREF:
        1. Extraction des taxa (species only)
        2. Extraction des noms vernaculaires
        3. Fusion TAXREF
        4. Cleanup des taxa sans noms
        5. Fichiers finaux avec suffixe '_minimal'."""
        # todo
        pass

    def test_minimal_mode_without_taxref(self, tmp_path):
        """Vérifie le pipeline en mode minimal sans TAXREF:
        pas de fusion, mais le cleanup est quand même effectué."""
        # todo
        pass

    def test_full_mode(self, tmp_path):
        """Vérifie le pipeline en mode full: pas de cleanup,
        tous les rangs sont inclus. Les fichiers n'ont pas de suffixe '_minimal'."""
        # todo
        pass

    def test_output_files_exist(self, tmp_path):
        """Vérifie que les fichiers de sortie (taxa TSV et vernacular TSV)
        sont créés dans le répertoire output_dir."""
        # todo
        pass
