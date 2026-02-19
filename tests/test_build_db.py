"""Tests pour daynimal/db/build_db.py — Construction de la DB SQLite.

Couvre: optimize_database_for_import, restore_database_settings,
bulk_import_taxa, bulk_import_vernacular, build_database.

Stratégie: on utilise des fichiers TSV temporaires (tmp_path) et une DB
SQLite en mémoire ou temporaire. On vérifie que les données sont
importées correctement et que les lignes malformées sont ignorées.
"""

from pathlib import Path

import pytest
from sqlalchemy import create_engine, text

from daynimal.db.build_db import (
    optimize_database_for_import,
    restore_database_settings,
    bulk_import_taxa,
    bulk_import_vernacular,
    build_database,
)
from daynimal.db.models import Base


def _create_engine_with_tables(db_path):
    """Helper: crée un engine SQLite avec les tables du modèle."""
    url = f"sqlite:///{db_path}"
    engine = create_engine(url)
    Base.metadata.create_all(engine)
    return engine


def _write_taxa_tsv(path, rows):
    """Helper: écrit un fichier TSV taxa avec les lignes données (liste de listes 13 colonnes)."""
    with open(path, "w", encoding="utf-8") as f:
        for row in rows:
            f.write("\t".join(str(c) for c in row) + "\n")


def _write_vernacular_tsv(path, rows):
    """Helper: écrit un fichier TSV vernacular avec les lignes données (3 colonnes)."""
    with open(path, "w", encoding="utf-8") as f:
        for row in rows:
            f.write("\t".join(str(c) for c in row) + "\n")


def _make_taxa_row(
    taxon_id,
    sci_name="Test species",
    canonical="Test species",
    rank="species",
    kingdom="Animalia",
    phylum="",
    class_="",
    order="",
    family="",
    genus="",
    parent_id="",
    accepted_id="",
    is_synonym="0",
):
    """Helper: crée une ligne taxa TSV valide (13 colonnes)."""
    return [
        taxon_id,
        sci_name,
        canonical,
        rank,
        kingdom,
        phylum,
        class_,
        order,
        family,
        genus,
        parent_id,
        accepted_id,
        is_synonym,
    ]


# =============================================================================
# SECTION 1 : optimize_database_for_import / restore_database_settings
# =============================================================================


class TestDatabaseOptimization:
    """Tests pour optimize/restore database settings."""

    def test_optimize_sets_pragmas(self, tmp_path):
        """Vérifie que optimize_database_for_import() exécute les PRAGMAs."""
        db_path = tmp_path / "test.db"
        engine = _create_engine_with_tables(db_path)

        optimize_database_for_import(engine)

        with engine.connect() as conn:
            sync = conn.execute(text("PRAGMA synchronous")).scalar()
            assert sync == 0  # OFF

        engine.dispose()

    def test_restore_sets_pragmas(self, tmp_path):
        """Vérifie que restore_database_settings() remet synchronous=FULL."""
        db_path = tmp_path / "test.db"
        engine = _create_engine_with_tables(db_path)

        optimize_database_for_import(engine)
        restore_database_settings(engine)

        with engine.connect() as conn:
            sync = conn.execute(text("PRAGMA synchronous")).scalar()
            assert sync == 2  # FULL

        engine.dispose()


# =============================================================================
# SECTION 2 : bulk_import_taxa
# =============================================================================


class TestBulkImportTaxa:
    """Tests pour bulk_import_taxa(engine, tsv_path)."""

    def test_imports_valid_rows(self, tmp_path):
        """Vérifie que bulk_import_taxa importe correctement des lignes TSV valides."""
        db_path = tmp_path / "test.db"
        engine = _create_engine_with_tables(db_path)

        tsv = tmp_path / "taxa.tsv"
        rows = [
            _make_taxa_row(
                1,
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
            ),
            _make_taxa_row(
                2,
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
            ),
            _make_taxa_row(
                3,
                "Ursus arctos",
                "Ursus arctos",
                "species",
                "Animalia",
                "Chordata",
                "Mammalia",
                "Carnivora",
                "Ursidae",
                "Ursus",
                "",
                "",
                "0",
            ),
        ]
        _write_taxa_tsv(tsv, rows)

        count = bulk_import_taxa(engine, tsv)

        assert count == 3
        with engine.connect() as conn:
            db_count = conn.execute(text("SELECT COUNT(*) FROM taxa")).scalar()
            assert db_count == 3

        engine.dispose()

    def test_skips_malformed_rows(self, tmp_path):
        """Vérifie que les lignes avec un nombre de colonnes != 13 sont ignorées."""
        db_path = tmp_path / "test.db"
        engine = _create_engine_with_tables(db_path)

        tsv = tmp_path / "taxa.tsv"
        rows = [
            _make_taxa_row(
                1,
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
            ),
            ["bad", "row", "only", "five", "columns"],
            _make_taxa_row(
                2,
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
            ),
        ]
        _write_taxa_tsv(tsv, rows)

        count = bulk_import_taxa(engine, tsv)

        assert count == 2
        engine.dispose()

    def test_handles_empty_optional_fields(self, tmp_path):
        """Vérifie que les champs optionnels vides sont convertis en None."""
        db_path = tmp_path / "test.db"
        engine = _create_engine_with_tables(db_path)

        tsv = tmp_path / "taxa.tsv"
        rows = [
            _make_taxa_row(
                1,
                "Canis lupus",
                "",
                "species",
                "Animalia",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "0",
            )
        ]
        _write_taxa_tsv(tsv, rows)

        bulk_import_taxa(engine, tsv)

        with engine.connect() as conn:
            row = conn.execute(
                text(
                    "SELECT canonical_name, phylum, parent_id FROM taxa WHERE taxon_id = 1"
                )
            ).fetchone()
            assert row[0] is None  # canonical_name empty → None
            assert row[1] is None  # phylum empty → None
            assert row[2] is None  # parent_id empty → None

        engine.dispose()

    def test_batching_5000(self, tmp_path):
        """Vérifie que l'import fonctionne avec plus de 5000 lignes."""
        db_path = tmp_path / "test.db"
        engine = _create_engine_with_tables(db_path)

        tsv = tmp_path / "taxa.tsv"
        rows = [
            _make_taxa_row(i, f"Species {i}", f"Species {i}") for i in range(1, 5501)
        ]
        _write_taxa_tsv(tsv, rows)

        count = bulk_import_taxa(engine, tsv)

        assert count == 5500
        with engine.connect() as conn:
            db_count = conn.execute(text("SELECT COUNT(*) FROM taxa")).scalar()
            assert db_count == 5500

        engine.dispose()

    def test_returns_count(self, tmp_path):
        """Vérifie que bulk_import_taxa retourne le nombre total de lignes importées."""
        db_path = tmp_path / "test.db"
        engine = _create_engine_with_tables(db_path)

        tsv = tmp_path / "taxa.tsv"
        rows = [_make_taxa_row(i, f"Species {i}") for i in range(1, 8)]
        _write_taxa_tsv(tsv, rows)

        count = bulk_import_taxa(engine, tsv)

        assert count == 7
        engine.dispose()


# =============================================================================
# SECTION 3 : bulk_import_vernacular
# =============================================================================


class TestBulkImportVernacular:
    """Tests pour bulk_import_vernacular(engine, tsv_path)."""

    def test_imports_valid_rows(self, tmp_path):
        """Vérifie que bulk_import_vernacular importe des lignes TSV valides."""
        db_path = tmp_path / "test.db"
        engine = _create_engine_with_tables(db_path)

        # Insert a taxon first (FK constraint)
        taxa_tsv = tmp_path / "taxa.tsv"
        _write_taxa_tsv(taxa_tsv, [_make_taxa_row(1, "Species 1")])
        bulk_import_taxa(engine, taxa_tsv)

        vern_tsv = tmp_path / "vernacular.tsv"
        _write_vernacular_tsv(
            vern_tsv, [[1, "Wolf", "en"], [1, "Loup", "fr"], [1, "Lobo", "es"]]
        )

        count = bulk_import_vernacular(engine, vern_tsv)

        assert count == 3
        with engine.connect() as conn:
            db_count = conn.execute(
                text("SELECT COUNT(*) FROM vernacular_names")
            ).scalar()
            assert db_count == 3

        engine.dispose()

    def test_skips_malformed_rows(self, tmp_path):
        """Vérifie que les lignes avec != 3 colonnes sont ignorées."""
        db_path = tmp_path / "test.db"
        engine = _create_engine_with_tables(db_path)

        taxa_tsv = tmp_path / "taxa.tsv"
        _write_taxa_tsv(taxa_tsv, [_make_taxa_row(1, "Species 1")])
        bulk_import_taxa(engine, taxa_tsv)

        vern_tsv = tmp_path / "vernacular.tsv"
        with open(vern_tsv, "w", encoding="utf-8") as f:
            f.write("1\tWolf\ten\n")
            f.write("bad\trow\n")  # Only 2 columns
            f.write("1\tLoup\tfr\n")

        count = bulk_import_vernacular(engine, vern_tsv)

        assert count == 2
        engine.dispose()

    def test_returns_count(self, tmp_path):
        """Vérifie que bulk_import_vernacular retourne le nombre importé."""
        db_path = tmp_path / "test.db"
        engine = _create_engine_with_tables(db_path)

        taxa_tsv = tmp_path / "taxa.tsv"
        _write_taxa_tsv(taxa_tsv, [_make_taxa_row(1, "Species 1")])
        bulk_import_taxa(engine, taxa_tsv)

        vern_tsv = tmp_path / "vernacular.tsv"
        _write_vernacular_tsv(vern_tsv, [[1, "Name1", "en"], [1, "Name2", "fr"]])

        count = bulk_import_vernacular(engine, vern_tsv)

        assert count == 2
        engine.dispose()

    def test_batching_10000(self, tmp_path):
        """Vérifie que l'import fonctionne avec plus de 10000 lignes."""
        db_path = tmp_path / "test.db"
        engine = _create_engine_with_tables(db_path)

        # Create enough taxa
        taxa_tsv = tmp_path / "taxa.tsv"
        _write_taxa_tsv(
            taxa_tsv, [_make_taxa_row(i, f"Species {i}") for i in range(1, 101)]
        )
        bulk_import_taxa(engine, taxa_tsv)

        vern_tsv = tmp_path / "vernacular.tsv"
        rows = []
        for i in range(1, 101):
            for j in range(110):
                rows.append([i, f"Name_{i}_{j}", "en"])
        _write_vernacular_tsv(vern_tsv, rows)

        count = bulk_import_vernacular(engine, vern_tsv)

        assert count == 11000
        engine.dispose()


# =============================================================================
# SECTION 4 : build_database
# =============================================================================


class TestBuildDatabase:
    """Tests pour build_database(taxa_tsv, vernacular_tsv, db_filename)."""

    def test_success_creates_db_file(self, tmp_path):
        """Vérifie que build_database crée le fichier SQLite avec les tables."""
        taxa_tsv = tmp_path / "taxa.tsv"
        vern_tsv = tmp_path / "vernacular.tsv"
        db_file = str(tmp_path / "test.db")

        _write_taxa_tsv(
            taxa_tsv,
            [
                _make_taxa_row(
                    1,
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
                )
            ],
        )
        _write_vernacular_tsv(vern_tsv, [[1, "Wolf", "en"]])

        build_database(taxa_tsv, vern_tsv, db_file)

        db_path = Path(db_file)
        assert db_path.exists()

        engine = create_engine(f"sqlite:///{db_file}")
        with engine.connect() as conn:
            tables = [
                row[0]
                for row in conn.execute(
                    text("SELECT name FROM sqlite_master WHERE type='table'")
                )
            ]
            assert "taxa" in tables
            assert "vernacular_names" in tables

            taxa_count = conn.execute(text("SELECT COUNT(*) FROM taxa")).scalar()
            assert taxa_count == 1

        engine.dispose()

    def test_missing_taxa_file_raises(self, tmp_path):
        """Vérifie que build_database lève FileNotFoundError pour taxa TSV manquant."""
        vern_tsv = tmp_path / "vernacular.tsv"
        _write_vernacular_tsv(vern_tsv, [])

        with pytest.raises(FileNotFoundError, match="Taxa TSV not found"):
            build_database(tmp_path / "nonexistent.tsv", vern_tsv, "test.db")

    def test_missing_vernacular_file_raises(self, tmp_path):
        """Vérifie que build_database lève FileNotFoundError pour vernacular TSV manquant."""
        taxa_tsv = tmp_path / "taxa.tsv"
        _write_taxa_tsv(taxa_tsv, [_make_taxa_row(1)])

        with pytest.raises(FileNotFoundError, match="Vernacular TSV not found"):
            build_database(taxa_tsv, tmp_path / "nonexistent.tsv", "test.db")

    def test_restores_original_db_url(self, tmp_path):
        """Vérifie que build_database restaure settings.database_url dans le finally."""
        from daynimal.config import settings

        taxa_tsv = tmp_path / "taxa.tsv"
        vern_tsv = tmp_path / "vernacular.tsv"
        db_file = str(tmp_path / "test.db")

        _write_taxa_tsv(taxa_tsv, [_make_taxa_row(1)])
        _write_vernacular_tsv(vern_tsv, [])

        original_url = settings.database_url

        build_database(taxa_tsv, vern_tsv, db_file)

        assert settings.database_url == original_url

    def test_restores_url_on_error(self, tmp_path):
        """Vérifie que settings.database_url est restauré même si l'import échoue."""
        from daynimal.config import settings

        original_url = settings.database_url

        with pytest.raises(FileNotFoundError):
            build_database(
                tmp_path / "nonexistent.tsv",
                tmp_path / "also_nonexistent.tsv",
                str(tmp_path / "test.db"),
            )

        assert settings.database_url == original_url

    def test_prints_stats(self, tmp_path, capsys):
        """Vérifie que build_database affiche les statistiques d'import."""
        taxa_tsv = tmp_path / "taxa.tsv"
        vern_tsv = tmp_path / "vernacular.tsv"
        db_file = str(tmp_path / "test.db")

        _write_taxa_tsv(
            taxa_tsv, [_make_taxa_row(1, "Canis lupus", "Canis lupus", "species")]
        )
        _write_vernacular_tsv(vern_tsv, [[1, "Wolf", "en"]])

        build_database(taxa_tsv, vern_tsv, db_file)

        captured = capsys.readouterr()
        assert "Total taxa:" in captured.out
        assert "Species:" in captured.out
        assert "BUILD COMPLETE" in captured.out
