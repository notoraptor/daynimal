"""Tests pour daynimal/db/build_db.py — Construction de la DB SQLite.

Couvre: optimize_database_for_import, restore_database_settings,
bulk_import_taxa, bulk_import_vernacular, build_database.

Stratégie: on utilise des fichiers TSV temporaires (tmp_path) et une DB
SQLite en mémoire ou temporaire. On vérifie que les données sont
importées correctement et que les lignes malformées sont ignorées.
"""

from unittest.mock import patch, MagicMock

import pytest


# =============================================================================
# SECTION 1 : optimize_database_for_import / restore_database_settings
# =============================================================================


class TestDatabaseOptimization:
    """Tests pour optimize/restore database settings."""

    def test_optimize_sets_pragmas(self):
        """Vérifie que optimize_database_for_import() exécute les PRAGMAs
        journal_mode=OFF, synchronous=OFF, cache_size, locking_mode=EXCLUSIVE
        sur l'engine fourni. On crée un engine SQLite en mémoire et on
        vérifie les PRAGMAs après appel."""
        # todo
        pass

    def test_restore_sets_pragmas(self):
        """Vérifie que restore_database_settings() remet journal_mode=DELETE
        et synchronous=FULL sur l'engine."""
        # todo
        pass


# =============================================================================
# SECTION 2 : bulk_import_taxa
# =============================================================================


class TestBulkImportTaxa:
    """Tests pour bulk_import_taxa(engine, tsv_path)."""

    def test_imports_valid_rows(self, tmp_path):
        """Vérifie que bulk_import_taxa importe correctement des lignes TSV
        valides (13 colonnes : taxon_id, scientific_name, canonical_name,
        rank, status, kingdom, phylum, class_, order, family, genus,
        parent_id, is_synonym). On crée un TSV avec 3 lignes valides et
        on vérifie que 3 rows sont insérées dans la table taxa."""
        # todo
        pass

    def test_skips_malformed_rows(self, tmp_path):
        """Vérifie que les lignes avec un nombre de colonnes != 13 sont
        ignorées silencieusement. On crée un TSV avec 2 lignes valides
        et 1 ligne courte (5 colonnes), et on vérifie que seules 2 rows
        sont importées."""
        # todo
        pass

    def test_handles_empty_optional_fields(self, tmp_path):
        """Vérifie que les champs optionnels vides (parent_id='', etc.)
        sont convertis en None par parse_int/bool."""
        # todo
        pass

    def test_batching_5000(self, tmp_path):
        """Vérifie que l'import fonctionne correctement avec plus de 5000
        lignes (la taille du batch). On vérifie que toutes les lignes sont
        importées malgré le batching."""
        # todo
        pass

    def test_returns_count(self, tmp_path):
        """Vérifie que bulk_import_taxa retourne le nombre total de lignes
        importées."""
        # todo
        pass


# =============================================================================
# SECTION 3 : bulk_import_vernacular
# =============================================================================


class TestBulkImportVernacular:
    """Tests pour bulk_import_vernacular(engine, tsv_path)."""

    def test_imports_valid_rows(self, tmp_path):
        """Vérifie que bulk_import_vernacular importe correctement des lignes
        TSV valides (3 colonnes : taxon_id, vernacular_name, language).
        On crée un TSV avec 3 lignes et on vérifie l'insertion."""
        # todo
        pass

    def test_skips_malformed_rows(self, tmp_path):
        """Vérifie que les lignes avec != 3 colonnes sont ignorées."""
        # todo
        pass

    def test_returns_count(self, tmp_path):
        """Vérifie que bulk_import_vernacular retourne le nombre de lignes
        importées."""
        # todo
        pass

    def test_batching_10000(self, tmp_path):
        """Vérifie que l'import fonctionne correctement avec plus de 10000
        lignes (taille du batch pour les noms vernaculaires)."""
        # todo
        pass


# =============================================================================
# SECTION 4 : build_database
# =============================================================================


class TestBuildDatabase:
    """Tests pour build_database(taxa_tsv, vernacular_tsv, db_filename)."""

    def test_success_creates_db_file(self, tmp_path):
        """Vérifie que build_database crée le fichier SQLite avec les
        tables taxa et vernacular_names. On fournit des TSV valides
        et on vérifie que le fichier DB existe et contient les bonnes tables."""
        # todo
        pass

    def test_missing_taxa_file_raises(self, tmp_path):
        """Vérifie que build_database lève FileNotFoundError quand le
        fichier taxa TSV n'existe pas."""
        # todo
        pass

    def test_missing_vernacular_file_raises(self, tmp_path):
        """Vérifie que build_database lève FileNotFoundError quand le
        fichier vernacular TSV n'existe pas."""
        # todo
        pass

    def test_runs_vacuum(self, tmp_path):
        """Vérifie que build_database exécute VACUUM à la fin de l'import
        pour compacter la base de données."""
        # todo
        pass

    def test_restores_original_db_url(self, tmp_path):
        """Vérifie que build_database restaure settings.database_url
        à sa valeur originale dans le bloc finally, même si l'import échoue."""
        # todo
        pass

    def test_prints_stats(self, tmp_path, capsys):
        """Vérifie que build_database affiche les statistiques d'import
        (nombre de taxa et de noms vernaculaires importés)."""
        # todo
        pass
