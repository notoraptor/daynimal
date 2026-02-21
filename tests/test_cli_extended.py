"""
Extended tests for CLI commands covering enrichment display and error paths.

Covers print_animal with wikidata/wikipedia/images, empty DB paths,
and cmd_history edge cases.
"""

import io
import sys
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from daynimal import AnimalInfo, Taxon
from daynimal.schemas import (
    WikidataEntity,
    WikipediaArticle,
    CommonsImage,
    ConservationStatus,
    License,
)
from daynimal.main import (
    cmd_today,
    cmd_random,
    cmd_history,
    cmd_setup,
    cmd_rebuild,
    cmd_clear_cache,
    temporary_database,
    main,
    print_animal,
)


def capture_stdout(func, *args, **kwargs):
    """Helper to capture stdout from a function."""
    old_stdout = sys.stdout
    sys.stdout = buffer = io.StringIO()
    try:
        func(*args, **kwargs)
        output = buffer.getvalue()
    finally:
        sys.stdout = old_stdout
    return output


def _make_enriched_animal():
    """Create a fully enriched animal for testing."""
    taxon = Taxon(
        taxon_id=5219173,
        scientific_name="Canis lupus",
        canonical_name="Canis lupus",
        kingdom="Animalia",
        phylum="Chordata",
        class_="Mammalia",
        order="Carnivora",
        family="Canidae",
        genus="Canis",
        rank="species",
        vernacular_names={"en": ["Wolf"], "fr": ["Loup"]},
    )

    wikidata = WikidataEntity(
        qid="Q18498",
        labels={"en": "Canis lupus", "fr": "loup"},
        descriptions={"en": "species of mammal"},
        iucn_status=ConservationStatus.LEAST_CONCERN,
        mass="40 kg",
        length="1.5 m",
        lifespan="15 year",
    )

    wikipedia = WikipediaArticle(
        title="Canis lupus",
        language="fr",
        page_id=3135,
        summary="Le Loup gris (Canis lupus) est un mammifere de la famille des canides.",
    )

    images = [
        CommonsImage(
            filename="Wolf1.jpg",
            url="https://upload.wikimedia.org/wolf1.jpg",
            thumbnail_url="https://upload.wikimedia.org/thumb/wolf1.jpg",
            author="Photographer1",
            license=License.CC_BY_SA,
        )
    ]

    return AnimalInfo(
        taxon=taxon,
        wikidata=wikidata,
        wikipedia=wikipedia,
        images=images,
        is_enriched=True,
    )


class TestPrintAnimalEnriched:
    """Tests for print_animal with enriched data."""

    def test_displays_wikidata_info(self):
        """Test that Wikidata info is displayed."""
        animal = _make_enriched_animal()
        output = capture_stdout(print_animal, animal)

        assert "Q18498" in output
        assert "LC" in output
        assert "40 kg" in output
        assert "1.5 m" in output
        assert "15 year" in output

    def test_displays_wikipedia_description(self):
        """Test that Wikipedia description is displayed."""
        animal = _make_enriched_animal()
        output = capture_stdout(print_animal, animal)

        assert "Description from Wikipedia" in output
        assert "Loup" in output

    def test_truncates_long_description(self):
        """Test that long description is truncated at 500 chars."""
        animal = _make_enriched_animal()
        animal.wikipedia.summary = "A " * 300  # >500 chars
        output = capture_stdout(print_animal, animal)

        assert "..." in output

    def test_displays_images_with_attribution(self):
        """Test that images are displayed with attribution."""
        animal = _make_enriched_animal()
        output = capture_stdout(print_animal, animal)

        assert "Images" in output
        assert "1 found" in output
        assert "Credit:" in output
        assert "Wolf1.jpg" in output

    def test_wikidata_status_as_string(self):
        """Test that IUCN status works as string (from cache)."""
        animal = _make_enriched_animal()
        animal.wikidata.iucn_status = "LC"  # String instead of enum
        output = capture_stdout(print_animal, animal)

        assert "LC" in output

    def test_wikidata_without_optional_fields(self):
        """Test print_animal when wikidata has no mass/length/lifespan."""
        animal = _make_enriched_animal()
        animal.wikidata.mass = None
        animal.wikidata.length = None
        animal.wikidata.lifespan = None
        animal.wikidata.iucn_status = None
        output = capture_stdout(print_animal, animal)

        assert "Q18498" in output
        assert "Mass" not in output
        assert "Length" not in output
        assert "Lifespan" not in output


class TestCmdTodayNoAnimal:
    """Tests for cmd_today when no animal in DB."""

    @patch("daynimal.main.AnimalRepository")
    def test_no_animal_in_db(self, mock_repo_class):
        """Test cmd_today when get_animal_of_the_day returns None."""
        repo = Mock()
        repo.get_animal_of_the_day.return_value = None
        mock_repo_class.return_value.__enter__.return_value = repo

        output = capture_stdout(cmd_today)
        assert "No animals" in output


class TestCmdRandomNoAnimal:
    """Tests for cmd_random when no animal in DB."""

    @patch("daynimal.main.AnimalRepository")
    def test_no_animal_in_db(self, mock_repo_class):
        """Test cmd_random when get_random returns None."""
        repo = Mock()
        repo.get_random.return_value = None
        mock_repo_class.return_value.__enter__.return_value = repo

        output = capture_stdout(cmd_random)
        assert "No animals" in output


class TestCmdHistoryEdgeCases:
    """Tests for cmd_history edge cases."""

    def test_page_less_than_1(self):
        """Test cmd_history with page < 1."""
        output = capture_stdout(lambda: cmd_history(page=0, per_page=10))
        assert "page must be >= 1" in output

    def test_per_page_less_than_1(self):
        """Test cmd_history with per_page < 1."""
        output = capture_stdout(lambda: cmd_history(page=1, per_page=0))
        assert "per-page must be >= 1" in output

    @patch("daynimal.main.AnimalRepository")
    def test_empty_page_beyond_total(self, mock_repo_class):
        """Test cmd_history when page exceeds total pages."""
        repo = Mock()
        repo.get_history.return_value = ([], 5)  # 5 total but empty on this page
        mock_repo_class.return_value.__enter__.return_value = repo

        output = capture_stdout(lambda: cmd_history(page=10, per_page=5))
        assert "No entries on page" in output

    @patch("daynimal.main.AnimalRepository")
    def test_multi_page_navigation_middle(self, mock_repo_class):
        """Test cmd_history shows both next/previous on middle page."""
        taxon = Taxon(
            taxon_id=1,
            scientific_name="Test Species",
            canonical_name="Test Species",
            rank="species",
            vernacular_names={"en": ["Test"]},
        )
        animal = AnimalInfo(taxon=taxon)
        animal.viewed_at = datetime.now()
        animal.command = "random"

        repo = Mock()
        repo.get_history.return_value = ([animal], 25)
        mock_repo_class.return_value.__enter__.return_value = repo

        output = capture_stdout(lambda: cmd_history(page=2, per_page=10))

        assert "Next page" in output
        assert "Previous page" in output

    @patch("daynimal.main.AnimalRepository")
    def test_last_page_no_next(self, mock_repo_class):
        """Test cmd_history on last page doesn't show 'Next page'."""
        taxon = Taxon(
            taxon_id=1,
            scientific_name="Test Species",
            canonical_name="Test Species",
            rank="species",
            vernacular_names={"en": ["Test"]},
        )
        animal = AnimalInfo(taxon=taxon)
        animal.viewed_at = datetime.now()
        animal.command = "today"

        repo = Mock()
        repo.get_history.return_value = ([animal], 15)
        mock_repo_class.return_value.__enter__.return_value = repo

        output = capture_stdout(lambda: cmd_history(page=2, per_page=10))

        assert "Previous page" in output
        assert "Next page" not in output

    @patch("daynimal.main.AnimalRepository")
    def test_animal_without_viewed_at(self, mock_repo_class):
        """Test cmd_history with animal missing viewed_at."""
        taxon = Taxon(
            taxon_id=1,
            scientific_name="Test Species",
            canonical_name="Test Species",
            rank="species",
            vernacular_names={},
        )
        animal = AnimalInfo(taxon=taxon)
        animal.viewed_at = None
        animal.command = None

        repo = Mock()
        repo.get_history.return_value = ([animal], 1)
        mock_repo_class.return_value.__enter__.return_value = repo

        output = capture_stdout(cmd_history)

        assert "Unknown" in output
        assert "Test Species" in output


# =============================================================================
# SECTION 5 : CLI setup command (main.py lignes ~240-382, 0% couverture)
# =============================================================================


class TestCmdSetup:
    """Tests pour cmd_setup(mode, no_taxref) et les helpers _setup_minimal/_setup_full."""

    @patch("daynimal.main.resolve_database", return_value="/some/path.db")
    def test_setup_db_already_exists(self, mock_resolve, capsys):
        """Vérifie que cmd_setup ne fait rien quand la DB existe déjà."""
        cmd_setup()

        captured = capsys.readouterr()
        assert "already exists" in captured.out

    @patch("daynimal.main.resolve_database", return_value=None)
    @patch("daynimal.main.download_and_setup_db")
    def test_setup_minimal_mode(self, mock_download, mock_resolve, capsys):
        """Vérifie que cmd_setup(mode='minimal') appelle download_and_setup_db."""
        cmd_setup(mode="minimal")

        mock_download.assert_called_once()
        captured = capsys.readouterr()
        assert "complete" in captured.out.lower() or "Setup" in captured.out

    @patch("daynimal.main.resolve_database", return_value=None)
    @patch(
        "daynimal.main.download_and_setup_db", side_effect=Exception("Network error")
    )
    def test_setup_minimal_failure(self, mock_download, mock_resolve):
        """Vérifie que si download_and_setup_db échoue, SystemExit(1) est levé."""
        with pytest.raises(SystemExit) as exc_info:
            cmd_setup(mode="minimal")

        assert exc_info.value.code == 1

    @patch("daynimal.main.resolve_database", return_value=None)
    @patch("daynimal.db.init_fts.init_fts")
    @patch("daynimal.db.build_db.build_database")
    @patch("daynimal.db.generate_distribution.generate_distribution")
    @patch("daynimal.db.first_launch.save_db_config")
    @patch("daynimal.db.first_launch.download_file")
    def test_setup_full_mode(
        self, mock_dl, mock_save, mock_gen, mock_build, mock_fts, mock_resolve, capsys
    ):
        """Vérifie que cmd_setup(mode='full') appelle generate_distribution, build_database, init_fts."""
        cmd_setup(mode="full", no_taxref=True)

        mock_gen.assert_called_once()
        mock_build.assert_called_once()
        mock_fts.assert_called_once()

    @patch("daynimal.main.resolve_database", return_value=None)
    @patch("daynimal.db.init_fts.init_fts")
    @patch("daynimal.db.build_db.build_database")
    @patch("daynimal.db.generate_distribution.generate_distribution")
    @patch("daynimal.db.first_launch.save_db_config")
    @patch("daynimal.db.first_launch.download_file")
    def test_setup_full_no_taxref(
        self, mock_dl, mock_save, mock_gen, mock_build, mock_fts, mock_resolve, capsys
    ):
        """Vérifie que cmd_setup(mode='full', no_taxref=True) passe taxref_path=None."""
        cmd_setup(mode="full", no_taxref=True)

        mock_gen.assert_called_once()
        call_kwargs = mock_gen.call_args
        # taxref_path should be None when no_taxref=True
        assert call_kwargs[1].get("taxref_path") is None or call_kwargs[0][2] is None


# =============================================================================
# SECTION 5b : cmd_rebuild (main.py)
# =============================================================================


class TestCmdRebuild:
    """Tests pour cmd_rebuild(mode)."""

    def test_rebuild_no_backbone_zip(self, tmp_path, monkeypatch):
        """Vérifie que cmd_rebuild échoue si backbone.zip n'existe pas."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / "data").mkdir()
        # No backbone.zip created

        with pytest.raises(SystemExit) as exc_info:
            cmd_rebuild(mode="full")

        assert exc_info.value.code == 1

    @patch("daynimal.db.init_fts.init_fts")
    @patch("daynimal.db.build_db.build_database")
    @patch("daynimal.db.generate_distribution.generate_distribution")
    @patch("daynimal.db.first_launch.save_db_config")
    def test_rebuild_full_mode(
        self, mock_save, mock_gen, mock_build, mock_fts, tmp_path, monkeypatch, capsys
    ):
        """Vérifie que cmd_rebuild(mode='full') appelle les 3 étapes avec bons fichiers."""
        monkeypatch.chdir(tmp_path)
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        (data_dir / "backbone.zip").touch()

        cmd_rebuild(mode="full")

        mock_gen.assert_called_once()
        gen_kwargs = mock_gen.call_args[1]
        assert gen_kwargs["mode"] == "full"
        assert gen_kwargs["backbone_path"] == Path("data/backbone.zip")
        assert gen_kwargs["taxref_path"] is None  # No TAXREF file

        mock_build.assert_called_once()
        build_args = mock_build.call_args[0]
        assert str(build_args[0]).endswith("animalia_taxa.tsv")
        assert str(build_args[1]).endswith("animalia_vernacular.tsv")

        mock_fts.assert_called_once()

    @patch("daynimal.db.init_fts.init_fts")
    @patch("daynimal.db.build_db.build_database")
    @patch("daynimal.db.generate_distribution.generate_distribution")
    @patch("daynimal.db.first_launch.save_db_config")
    def test_rebuild_minimal_mode(
        self, mock_save, mock_gen, mock_build, mock_fts, tmp_path, monkeypatch, capsys
    ):
        """Vérifie que cmd_rebuild(mode='minimal') utilise les fichiers _minimal."""
        monkeypatch.chdir(tmp_path)
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        (data_dir / "backbone.zip").touch()

        cmd_rebuild(mode="minimal")

        mock_gen.assert_called_once()
        gen_kwargs = mock_gen.call_args[1]
        assert gen_kwargs["mode"] == "minimal"

        mock_build.assert_called_once()
        build_args = mock_build.call_args[0]
        assert str(build_args[0]).endswith("animalia_taxa_minimal.tsv")
        assert str(build_args[1]).endswith("animalia_vernacular_minimal.tsv")

    @patch("daynimal.db.init_fts.init_fts")
    @patch("daynimal.db.build_db.build_database")
    @patch("daynimal.db.generate_distribution.generate_distribution")
    @patch("daynimal.db.first_launch.save_db_config")
    def test_rebuild_with_taxref(
        self, mock_save, mock_gen, mock_build, mock_fts, tmp_path, monkeypatch, capsys
    ):
        """Vérifie que cmd_rebuild détecte TAXREFv18.txt et le passe à generate_distribution."""
        monkeypatch.chdir(tmp_path)
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        (data_dir / "backbone.zip").touch()
        (data_dir / "TAXREFv18.txt").touch()

        cmd_rebuild(mode="full")

        gen_kwargs = mock_gen.call_args[1]
        assert gen_kwargs["taxref_path"] == Path("data/TAXREFv18.txt")

        captured = capsys.readouterr()
        assert "TAXREF found" in captured.out

    @patch("daynimal.db.init_fts.init_fts")
    @patch("daynimal.db.build_db.build_database")
    @patch("daynimal.db.generate_distribution.generate_distribution")
    @patch("daynimal.db.first_launch.save_db_config")
    def test_rebuild_always_saves_config(
        self, mock_save, mock_gen, mock_build, mock_fts, tmp_path, monkeypatch
    ):
        """Vérifie que save_db_config est toujours appelé."""
        monkeypatch.chdir(tmp_path)
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        (data_dir / "backbone.zip").touch()

        cmd_rebuild(mode="full")

        mock_save.assert_called_once()

    @patch("daynimal.db.init_fts.init_fts")
    @patch("daynimal.db.build_db.build_database")
    @patch("daynimal.db.generate_distribution.generate_distribution")
    @patch("daynimal.db.first_launch.save_db_config")
    @patch("daynimal.db.session.get_engine")
    def test_rebuild_clears_taxonomy_tables(
        self,
        mock_engine,
        mock_save,
        mock_gen,
        mock_build,
        mock_fts,
        tmp_path,
        monkeypatch,
        capsys,
    ):
        """Vérifie que les tables taxonomiques sont vidées (pas la DB entière)."""
        from unittest.mock import MagicMock

        monkeypatch.chdir(tmp_path)
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        (data_dir / "backbone.zip").touch()
        db_file = tmp_path / "daynimal.db"
        db_file.touch()  # DB already exists

        # Track SQL statements executed
        mock_conn = MagicMock()
        mock_engine.return_value.begin.return_value.__enter__ = lambda s: mock_conn
        mock_engine.return_value.begin.return_value.__exit__ = MagicMock(
            return_value=False
        )

        cmd_rebuild(mode="full")

        # Verify taxonomy tables were cleared
        executed_sql = [str(call[0][0]) for call in mock_conn.execute.call_args_list]
        assert any("DELETE FROM taxa" in sql for sql in executed_sql)
        assert any("DELETE FROM vernacular_names" in sql for sql in executed_sql)
        assert any("DELETE FROM enrichment_cache" in sql for sql in executed_sql)

        # DB file should still exist (not deleted)
        assert db_file.exists()

        captured = capsys.readouterr()
        assert "preserving history, favorites, settings" in captured.out.lower()

    @patch(
        "daynimal.db.generate_distribution.generate_distribution",
        side_effect=Exception("Parse error"),
    )
    def test_rebuild_failure(self, mock_gen, tmp_path, monkeypatch):
        """Vérifie que si une étape échoue, SystemExit(1) est levé."""
        monkeypatch.chdir(tmp_path)
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        (data_dir / "backbone.zip").touch()

        with pytest.raises(SystemExit) as exc_info:
            cmd_rebuild(mode="full")

        assert exc_info.value.code == 1


# =============================================================================
# SECTION 6 : cmd_clear_cache (main.py lignes ~461-477, 0% couverture)
# =============================================================================


class TestCmdClearCache:
    """Tests pour cmd_clear_cache()."""

    @patch("daynimal.main.AnimalRepository")
    def test_clear_cache_non_empty(self, mock_repo_class, capsys):
        """Vérifie que cmd_clear_cache supprime le cache et affiche le nombre."""
        repo = Mock()
        # Mock session.query().count() to return 10
        mock_query = Mock()
        mock_query.count.return_value = 10
        mock_query.delete.return_value = 10
        mock_query.filter.return_value = mock_query
        mock_query.update.return_value = 10
        repo.session.query.return_value = mock_query
        mock_repo_class.return_value.__enter__.return_value = repo

        cmd_clear_cache()

        captured = capsys.readouterr()
        assert "10" in captured.out
        assert "Cleared" in captured.out
        repo.session.commit.assert_called_once()

    @patch("daynimal.main.AnimalRepository")
    def test_clear_cache_empty(self, mock_repo_class, capsys):
        """Vérifie que cmd_clear_cache affiche un message quand le cache est vide."""
        repo = Mock()
        mock_query = Mock()
        mock_query.count.return_value = 0
        repo.session.query.return_value = mock_query
        mock_repo_class.return_value.__enter__.return_value = repo

        cmd_clear_cache()

        captured = capsys.readouterr()
        assert "already empty" in captured.out


# =============================================================================
# SECTION 7 : temporary_database (main.py lignes ~30-42)
# =============================================================================


class TestTemporaryDatabase:
    """Tests pour temporary_database(database_url) context manager."""

    def test_none_url_no_change(self):
        """Vérifie que temporary_database(None) ne modifie pas settings.database_url."""
        from daynimal.config import settings

        original = settings.database_url

        with temporary_database(None):
            assert settings.database_url == original

        assert settings.database_url == original

    def test_custom_url_sets_and_restores(self):
        """Vérifie que temporary_database('sqlite:///custom.db') modifie puis restaure."""
        from daynimal.config import settings

        original = settings.database_url

        with temporary_database("sqlite:///custom.db"):
            assert settings.database_url == "sqlite:///custom.db"

        assert settings.database_url == original

    def test_restores_on_exception(self):
        """Vérifie que settings.database_url est restauré même après exception."""
        from daynimal.config import settings

        original = settings.database_url

        try:
            with temporary_database("sqlite:///custom.db"):
                assert settings.database_url == "sqlite:///custom.db"
                raise ValueError("test error")
        except ValueError:
            pass

        assert settings.database_url == original


# =============================================================================
# SECTION 8 : main() routing (main.py lignes ~480-600)
# =============================================================================


class TestMainRouting:
    """Tests pour le routage dans main()."""

    @patch("sys.argv", ["daynimal"])
    @patch("daynimal.main.resolve_database", return_value="/path.db")
    @patch("daynimal.main.cmd_today")
    def test_default_command_is_today(self, mock_today, mock_resolve):
        """Vérifie que sans sous-commande, main() appelle cmd_today()."""
        main()
        mock_today.assert_called_once()

    @patch("sys.argv", ["daynimal", "setup", "--mode", "minimal"])
    @patch("daynimal.main.cmd_setup")
    def test_setup_does_not_require_db(self, mock_setup):
        """Vérifie que 'daynimal setup' fonctionne même sans DB."""
        main()
        mock_setup.assert_called_once_with(mode="minimal", no_taxref=False)

    @patch("sys.argv", ["daynimal", "rebuild", "--mode", "minimal"])
    @patch("daynimal.main.cmd_rebuild")
    def test_rebuild_does_not_require_db(self, mock_rebuild):
        """Vérifie que 'daynimal rebuild' fonctionne même sans DB."""
        main()
        mock_rebuild.assert_called_once_with(mode="minimal")

    @patch("sys.argv", ["daynimal", "rebuild"])
    @patch("daynimal.main.cmd_rebuild")
    def test_rebuild_default_mode_is_full(self, mock_rebuild):
        """Vérifie que 'daynimal rebuild' sans --mode utilise 'full'."""
        main()
        mock_rebuild.assert_called_once_with(mode="full")

    @patch("sys.argv", ["daynimal", "today"])
    @patch("daynimal.main.resolve_database", return_value=None)
    def test_missing_db_raises_system_exit(self, mock_resolve):
        """Vérifie que si resolve_database retourne None, SystemExit est levé."""
        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 1
