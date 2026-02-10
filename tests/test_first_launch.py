"""Tests for first-launch setup module."""

import hashlib
import json
import sqlite3
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from daynimal.db.first_launch import (
    DB_CONFIG_FILENAME,
    download_and_setup_db,
    is_db_valid,
    resolve_database,
    save_db_config,
    verify_checksum,
)


@pytest.fixture
def tmp_cwd(tmp_path, monkeypatch):
    """Change working directory to a temp path."""
    monkeypatch.chdir(tmp_path)
    return tmp_path


def _create_valid_db(path: Path):
    """Create a minimal valid SQLite DB with a taxa table."""
    conn = sqlite3.connect(str(path))
    conn.execute(
        "CREATE TABLE taxa (taxon_id INTEGER PRIMARY KEY, scientific_name TEXT)"
    )
    conn.execute("INSERT INTO taxa VALUES (1, 'Canis lupus')")
    conn.commit()
    conn.close()


# --- is_db_valid ---


def test_is_db_valid_no_file(tmp_cwd):
    assert is_db_valid(tmp_cwd / "nonexistent.db") is False


def test_is_db_valid_empty_file(tmp_cwd):
    p = tmp_cwd / "empty.db"
    p.write_bytes(b"")
    assert is_db_valid(p) is False


def test_is_db_valid_no_taxa_table(tmp_cwd):
    p = tmp_cwd / "bad.db"
    conn = sqlite3.connect(str(p))
    conn.execute("CREATE TABLE other (id INTEGER)")
    conn.commit()
    conn.close()
    assert is_db_valid(p) is False


def test_is_db_valid_ok(tmp_cwd):
    p = tmp_cwd / "good.db"
    _create_valid_db(p)
    assert is_db_valid(p) is True


# --- resolve_database ---


def test_resolve_database_default(tmp_cwd):
    """Default DB exists -> returns it."""
    db = tmp_cwd / "daynimal.db"
    _create_valid_db(db)
    with patch("daynimal.db.first_launch.settings") as mock_settings:
        mock_settings.database_url = f"sqlite:///{db}"
        result = resolve_database()
    assert result == db


def test_resolve_database_via_config(tmp_cwd):
    """Default DB missing, .daynimal_config points to minimal DB."""
    minimal_db = tmp_cwd / "daynimal_minimal.db"
    _create_valid_db(minimal_db)
    config_path = tmp_cwd / DB_CONFIG_FILENAME
    config_path.write_text(
        json.dumps({"database_path": str(minimal_db)}), encoding="utf-8"
    )
    with patch("daynimal.db.first_launch.settings") as mock_settings:
        mock_settings.database_url = f"sqlite:///{tmp_cwd / 'daynimal.db'}"
        result = resolve_database()
    assert result == minimal_db


def test_resolve_database_none(tmp_cwd):
    """No DB and no config -> returns None."""
    with patch("daynimal.db.first_launch.settings") as mock_settings:
        mock_settings.database_url = f"sqlite:///{tmp_cwd / 'daynimal.db'}"
        result = resolve_database()
    assert result is None


# --- save_db_config ---


def test_save_db_config(tmp_cwd):
    db = tmp_cwd / "daynimal_minimal.db"
    with patch("daynimal.db.first_launch.settings") as mock_settings:
        mock_settings.database_url = f"sqlite:///{tmp_cwd / 'daynimal.db'}"
        save_db_config(db)
    config_path = tmp_cwd / DB_CONFIG_FILENAME
    assert config_path.exists()
    data = json.loads(config_path.read_text(encoding="utf-8"))
    assert data["database_path"] == str(db)


# --- verify_checksum ---


def test_verify_checksum_valid(tmp_cwd):
    p = tmp_cwd / "file.bin"
    content = b"hello world"
    p.write_bytes(content)
    expected = hashlib.sha256(content).hexdigest()
    assert verify_checksum(p, expected) is True


def test_verify_checksum_invalid(tmp_cwd):
    p = tmp_cwd / "file.bin"
    p.write_bytes(b"hello world")
    assert verify_checksum(p, "0" * 64) is False


# --- download_and_setup_db ---


def test_download_and_setup_db(tmp_cwd):
    """Mock httpx and build functions to test the full pipeline."""
    manifest = {
        "files": [
            {"name": "animalia_taxa_minimal.tsv.gz", "sha256": "abc123"},
            {"name": "animalia_vernacular_minimal.tsv.gz", "sha256": "def456"},
        ]
    }

    with (
        patch("daynimal.db.first_launch.download_file") as mock_download,
        patch("daynimal.db.first_launch.verify_checksum", return_value=True),
        patch("daynimal.db.first_launch.settings") as mock_settings,
        patch("daynimal.db.first_launch.gzip") as mock_gzip,
        patch("daynimal.db.first_launch.shutil"),
        patch("daynimal.db.build_db.build_database") as mock_build,
        patch("daynimal.db.init_fts.init_fts") as mock_fts,
    ):
        mock_settings.distribution_base_url = "https://example.com"
        mock_settings.database_url = f"sqlite:///{tmp_cwd / 'daynimal.db'}"

        # Make manifest download write the file
        def fake_download(url, dest, progress_callback=None):
            if "manifest.json" in url:
                dest.write_text(json.dumps(manifest), encoding="utf-8")
            else:
                dest.write_bytes(b"fake")
            return dest

        mock_download.side_effect = fake_download
        mock_gzip.open.return_value.__enter__ = MagicMock()
        mock_gzip.open.return_value.__exit__ = MagicMock(return_value=False)

        callback = MagicMock()
        download_and_setup_db(progress_callback=callback)

        mock_build.assert_called_once()
        mock_fts.assert_called_once()
        # Callback was called for multiple stages
        assert callback.call_count > 0


def test_download_failure_cleanup(tmp_cwd):
    """On failure, partial DB should be deleted."""
    db_path = tmp_cwd / "daynimal_minimal.db"

    with (
        patch(
            "daynimal.db.first_launch.download_file",
            side_effect=RuntimeError("Network error"),
        ),
        patch("daynimal.db.first_launch.settings") as mock_settings,
    ):
        mock_settings.distribution_base_url = "https://example.com"
        mock_settings.database_url = f"sqlite:///{tmp_cwd / 'daynimal.db'}"

        with pytest.raises(RuntimeError, match="Network error"):
            download_and_setup_db()

    assert not db_path.exists()


# --- CLI setup ---


def test_cli_setup():
    """Test that 'daynimal setup' calls cmd_setup."""
    with (
        patch("sys.argv", ["daynimal", "setup"]),
        patch("daynimal.main.cmd_setup") as mock_setup,
    ):
        from daynimal.main import main

        main()
        mock_setup.assert_called_once()
