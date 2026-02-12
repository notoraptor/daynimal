"""Tests for config.py mobile-aware path functions."""

from pathlib import Path
from unittest.mock import patch

from daynimal.config import get_app_data_dir, get_app_temp_dir


def test_get_app_data_dir_desktop():
    """Sans FLET_APP_STORAGE_DATA, retourne le répertoire courant."""
    with patch.dict("os.environ", {}, clear=True):
        assert get_app_data_dir() == Path(".")


def test_get_app_data_dir_mobile():
    """Avec FLET_APP_STORAGE_DATA, retourne le chemin Flet."""
    with patch.dict("os.environ", {"FLET_APP_STORAGE_DATA": "/data/app/storage"}):
        assert get_app_data_dir() == Path("/data/app/storage")


def test_get_app_temp_dir_desktop():
    """Sans FLET_APP_STORAGE_TEMP, retourne tmp/."""
    with patch.dict("os.environ", {}, clear=True):
        assert get_app_temp_dir() == Path("tmp")


def test_get_app_temp_dir_mobile():
    """Avec FLET_APP_STORAGE_TEMP, retourne le chemin Flet."""
    with patch.dict("os.environ", {"FLET_APP_STORAGE_TEMP": "/data/app/temp"}):
        assert get_app_temp_dir() == Path("/data/app/temp")
