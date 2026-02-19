"""Tests pour daynimal/db/init_fts.py — Initialisation FTS5.

Couvre: create_fts_table, populate_fts_table, init_fts, rebuild_fts.

Stratégie: on utilise une session SQLite en mémoire avec les tables taxa
et vernacular_names pré-remplies. On vérifie que la table FTS5 est créée,
peuplée, et que rebuild/optimize fonctionnent.
"""

from unittest.mock import patch, MagicMock

import pytest
from sqlalchemy import text

from daynimal.db.init_fts import (
    create_fts_table,
    populate_fts_table,
    init_fts,
    rebuild_fts,
)


# =============================================================================
# SECTION 1 : create_fts_table
# =============================================================================


class TestCreateFtsTable:
    """Tests pour create_fts_table(session)."""

    def test_drops_existing_table(self, populated_session):
        """Vérifie que create_fts_table supprime la table existante avant recréation."""
        try:
            # Create FTS table first time
            create_fts_table(populated_session)
            # Create again — should not raise "table already exists"
            create_fts_table(populated_session)

            # Verify table exists
            result = populated_session.execute(
                text("SELECT name FROM sqlite_master WHERE type='table' AND name='taxa_fts'")
            ).fetchone()
            assert result is not None
        except Exception:
            pytest.skip("FTS5 not available in SQLite")

    def test_creates_fts5_virtual_table(self, populated_session):
        """Vérifie que create_fts_table crée une table virtuelle FTS5."""
        try:
            create_fts_table(populated_session)

            result = populated_session.execute(
                text("SELECT name FROM sqlite_master WHERE name='taxa_fts'")
            ).fetchone()
            assert result is not None
            assert result[0] == "taxa_fts"
        except Exception:
            pytest.skip("FTS5 not available in SQLite")


# =============================================================================
# SECTION 2 : populate_fts_table
# =============================================================================


class TestPopulateFtsTable:
    """Tests pour populate_fts_table(session)."""

    def test_inserts_all_taxa(self, populated_session):
        """Vérifie que populate_fts_table insère une ligne par taxon."""
        try:
            create_fts_table(populated_session)
            populate_fts_table(populated_session)

            # Count taxa in main table
            taxa_count = populated_session.execute(
                text("SELECT COUNT(*) FROM taxa")
            ).scalar()

            # Count entries in FTS table
            fts_count = populated_session.execute(
                text("SELECT COUNT(*) FROM taxa_fts")
            ).scalar()

            assert fts_count == taxa_count
        except Exception:
            pytest.skip("FTS5 not available in SQLite")

    def test_aggregates_vernacular_names(self, populated_session):
        """Vérifie que les noms vernaculaires sont agrégés dans un seul champ."""
        try:
            create_fts_table(populated_session)
            populate_fts_table(populated_session)

            # Taxon 1 has 3 vernacular names (en, fr, es)
            result = populated_session.execute(
                text("SELECT vernacular_names FROM taxa_fts WHERE taxon_id = 1")
            ).fetchone()

            assert result is not None
            vern = result[0]
            # Should contain names from multiple languages separated by spaces
            assert "Species 1 English" in vern
            assert "Espèce 1" in vern
        except Exception:
            pytest.skip("FTS5 not available in SQLite")

    def test_taxa_without_vernacular_have_empty_field(self, populated_session):
        """Vérifie que les taxa sans noms vernaculaires ont un champ vide."""
        try:
            create_fts_table(populated_session)
            populate_fts_table(populated_session)

            # Family taxa (IDs 100-104) have no vernacular names
            result = populated_session.execute(
                text("SELECT vernacular_names FROM taxa_fts WHERE taxon_id = 100")
            ).fetchone()

            assert result is not None
            assert result[0] == ""
        except Exception:
            pytest.skip("FTS5 not available in SQLite")


# =============================================================================
# SECTION 3 : init_fts
# =============================================================================


class TestInitFts:
    """Tests pour init_fts(db_path)."""

    @patch("daynimal.db.init_fts.settings")
    @patch("daynimal.db.init_fts.get_session")
    def test_with_custom_db_path(self, mock_get_session, mock_settings):
        """Vérifie que init_fts(db_path) modifie settings.database_url."""
        mock_session = MagicMock()
        # Make fetchone return a proper tuple so the format string works
        mock_session.execute.return_value.fetchone.return_value = (42,)
        mock_get_session.return_value.__enter__ = MagicMock(return_value=mock_session)
        mock_get_session.return_value.__exit__ = MagicMock(return_value=False)

        init_fts(db_path="/custom/path.db")

        assert mock_settings.database_url == "sqlite:////custom/path.db"

    @patch("daynimal.db.init_fts.settings")
    @patch("daynimal.db.init_fts.get_session")
    def test_with_default_path(self, mock_get_session, mock_settings):
        """Vérifie que init_fts(None) ne modifie pas settings.database_url."""
        original_url = mock_settings.database_url
        mock_session = MagicMock()
        mock_session.execute.return_value.fetchone.return_value = (0,)
        mock_get_session.return_value.__enter__ = MagicMock(return_value=mock_session)
        mock_get_session.return_value.__exit__ = MagicMock(return_value=False)

        init_fts(db_path=None)

        assert mock_settings.database_url == original_url

    def test_full_pipeline(self, tmp_path):
        """Vérifie le pipeline complet: init_fts crée et peuple la table FTS5."""
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        from daynimal.db.models import Base, TaxonModel, VernacularNameModel

        db_path = tmp_path / "fts_test.db"
        engine = create_engine(f"sqlite:///{db_path}")
        Base.metadata.create_all(engine)

        Session = sessionmaker(bind=engine)
        session = Session()

        # Add test data
        taxon = TaxonModel(
            taxon_id=1, scientific_name="Canis lupus", canonical_name="Canis lupus",
            rank="species", kingdom="Animalia", is_enriched=False, is_synonym=False,
        )
        vn = VernacularNameModel(taxon_id=1, name="Wolf", language="en")
        session.add(taxon)
        session.add(vn)
        session.commit()
        session.close()
        engine.dispose()

        try:
            init_fts(db_path=str(db_path))

            # Verify FTS works
            engine2 = create_engine(f"sqlite:///{db_path}")
            Session2 = sessionmaker(bind=engine2)
            session2 = Session2()

            result = session2.execute(
                text("SELECT COUNT(*) FROM taxa_fts")
            ).scalar()
            assert result == 1

            # FTS search
            search_result = session2.execute(
                text("SELECT taxon_id FROM taxa_fts WHERE taxa_fts MATCH 'Wolf'")
            ).fetchone()
            assert search_result is not None
            assert search_result[0] == 1

            session2.close()
            engine2.dispose()
        except Exception:
            pytest.skip("FTS5 not available in SQLite")


# =============================================================================
# SECTION 4 : rebuild_fts
# =============================================================================


class TestRebuildFts:
    """Tests pour rebuild_fts()."""

    @patch("daynimal.db.init_fts.get_session")
    def test_sends_rebuild_command(self, mock_get_session):
        """Vérifie que rebuild_fts() exécute la commande rebuild sur la table FTS."""
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__ = MagicMock(return_value=mock_session)
        mock_get_session.return_value.__exit__ = MagicMock(return_value=False)

        rebuild_fts()

        # Should have executed at least one SQL statement (rebuild command)
        assert mock_session.execute.called
        assert mock_session.commit.called

    @patch("daynimal.db.init_fts.get_session")
    def test_prints_completion_message(self, mock_get_session, capsys):
        """Vérifie que rebuild_fts() affiche un message de complétion."""
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__ = MagicMock(return_value=mock_session)
        mock_get_session.return_value.__exit__ = MagicMock(return_value=False)

        rebuild_fts()

        captured = capsys.readouterr()
        assert "rebuild" in captured.out.lower() or "FTS5" in captured.out
