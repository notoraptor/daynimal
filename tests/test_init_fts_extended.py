"""Tests pour daynimal/db/init_fts.py — Initialisation FTS5.

Couvre: create_fts_table, populate_fts_table, init_fts, rebuild_fts.

Stratégie: on utilise une session SQLite en mémoire avec les tables taxa
et vernacular_names pré-remplies. On vérifie que la table FTS5 est créée,
peuplée, et que rebuild/optimize fonctionnent.

Note: les tests existants dans conftest.py utilisent déjà FTS5 via la
fixture session_with_fts, mais les fonctions de init_fts.py elles-mêmes
ne sont pas directement testées (22% couverture).
"""

from unittest.mock import patch, MagicMock

import pytest


# =============================================================================
# SECTION 1 : create_fts_table
# =============================================================================


class TestCreateFtsTable:
    """Tests pour create_fts_table(session)."""

    def test_drops_existing_table(self, populated_session):
        """Vérifie que create_fts_table supprime la table taxa_fts existante
        avant de la recréer. On crée d'abord la table FTS, puis on appelle
        create_fts_table à nouveau, et on vérifie qu'il n'y a pas d'erreur
        'table already exists'."""
        # todo
        pass

    def test_creates_fts5_virtual_table(self, populated_session):
        """Vérifie que create_fts_table crée une table virtuelle FTS5
        avec les colonnes: taxon_id, scientific_name, canonical_name,
        vernacular_names. On vérifie via sqlite_master que la table existe."""
        # todo
        pass


# =============================================================================
# SECTION 2 : populate_fts_table
# =============================================================================


class TestPopulateFtsTable:
    """Tests pour populate_fts_table(session)."""

    def test_inserts_all_taxa(self, populated_session):
        """Vérifie que populate_fts_table insère une ligne par taxon
        dans la table FTS5. Avec 53 taxa dans populated_session,
        la table FTS doit contenir 53 lignes."""
        # todo
        pass

    def test_aggregates_vernacular_names(self, populated_session):
        """Vérifie que les noms vernaculaires d'un même taxon sont agrégés
        dans un seul champ séparé par des espaces. On vérifie qu'un taxon
        avec 2 noms vernaculaires a les deux dans son champ vernacular_names."""
        # todo
        pass

    def test_taxa_without_vernacular_have_empty_field(self, populated_session):
        """Vérifie que les taxa sans noms vernaculaires ont un champ
        vernacular_names vide dans la table FTS."""
        # todo
        pass


# =============================================================================
# SECTION 3 : init_fts
# =============================================================================


class TestInitFts:
    """Tests pour init_fts(db_path)."""

    def test_with_custom_db_path(self, tmp_path):
        """Vérifie que init_fts(db_path) utilise le chemin fourni pour
        créer la session, au lieu du chemin par défaut dans settings.
        On passe un chemin personnalisé et on vérifie que les settings
        sont temporairement modifiées."""
        # todo
        pass

    def test_with_default_path(self):
        """Vérifie que init_fts(None) utilise le chemin par défaut
        de settings.database_url. On mocke get_session pour vérifier
        qu'il est appelé sans modification des settings."""
        # todo
        pass

    def test_full_pipeline(self, tmp_path):
        """Vérifie le pipeline complet: init_fts appelle create_fts_table
        puis populate_fts_table, et la recherche FTS fonctionne ensuite.
        On crée une DB temporaire avec des taxa, on appelle init_fts,
        puis on effectue une requête FTS pour vérifier."""
        # todo
        pass


# =============================================================================
# SECTION 4 : rebuild_fts
# =============================================================================


class TestRebuildFts:
    """Tests pour rebuild_fts()."""

    def test_sends_rebuild_command(self):
        """Vérifie que rebuild_fts() exécute INSERT INTO taxa_fts(taxa_fts)
        VALUES('rebuild') suivi de VALUES('optimize'). On mocke get_session
        et on vérifie les requêtes SQL exécutées."""
        # todo
        pass

    def test_prints_completion_message(self, capsys):
        """Vérifie que rebuild_fts() affiche un message de complétion."""
        # todo
        pass
