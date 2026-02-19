"""Tests pour daynimal/debug.py — Utilitaires de debug.

Couvre: FletDebugger (init, setup_logging, log_*, print_log_location),
_default_log_dir, get_debugger (singleton), log_info/log_error/log_debug.

Stratégie: on utilise tmp_path pour les logs, on vérifie le contenu des
fichiers logs et les appels au logger.
"""

import logging
import sys
from unittest.mock import patch, MagicMock

import pytest

import daynimal.debug as debug_module
from daynimal.debug import (
    FletDebugger,
    _default_log_dir,
    get_debugger,
    log_info,
    log_error,
    log_debug,
)


def _close_debugger(d):
    "Close all file handlers to avoid resource leaks on Windows."
    for h in d.logger.handlers[:]:
        h.close()
        d.logger.removeHandler(h)


@pytest.fixture(autouse=True)
def reset_global_debugger():
    "Reset the global _debugger singleton before/after each test."
    original = debug_module._debugger
    debug_module._debugger = None
    yield
    if debug_module._debugger is not None:
        _close_debugger(debug_module._debugger)
    debug_module._debugger = original


# =============================================================================
# SECTION 1 : _default_log_dir
# =============================================================================


class TestDefaultLogDir:
    "Tests pour _default_log_dir()."

    @patch.dict("os.environ", {}, clear=True)
    def test_desktop_returns_logs_dir(self):
        """Vérifie que sans FLET_APP_STORAGE_DATA, _default_log_dir()
        retourne logs (chemin relatif au répertoire courant)."""
        result = _default_log_dir()
        assert result == "logs"

    @patch.dict("os.environ", {"FLET_APP_STORAGE_DATA": "/data/app"})
    def test_mobile_returns_storage_logs(self):
        """Vérifie qu avec FLET_APP_STORAGE_DATA=/data/app, _default_log_dir()
        retourne /data/app/logs."""
        result = _default_log_dir()
        from pathlib import Path

        assert result == str(Path("/data/app") / "logs")


# =============================================================================
# SECTION 2 : FletDebugger.__init__
# =============================================================================


class TestFletDebuggerInit:
    "Tests pour FletDebugger.__init__."

    def test_creates_log_directory(self, tmp_path):
        """Vérifie que FletDebugger crée le répertoire de logs s il n existe pas.
        On passe tmp_path / new_logs et on vérifie que le dossier est créé."""
        log_dir = tmp_path / "new_logs"
        assert not log_dir.exists()
        d = FletDebugger(log_dir=str(log_dir), log_to_console=False)
        _close_debugger(d)
        assert log_dir.exists()

    def test_generates_timestamped_filename(self, tmp_path):
        """Vérifie que le fichier de log est nommé daynimal_YYYYMMDD_HHMMSS.log.
        On vérifie que self.log_file.name commence par daynimal_ et finit par .log."""
        d = FletDebugger(log_dir=str(tmp_path), log_to_console=False)
        name = d.log_file.name
        _close_debugger(d)
        assert name.startswith("daynimal_")
        assert name.endswith(".log")

    def test_log_file_exists_after_init(self, tmp_path):
        """Vérifie que le fichier de log est bien créé sur le disque
        après l initialisation du FletDebugger."""
        d = FletDebugger(log_dir=str(tmp_path), log_to_console=False)
        log_file = d.log_file
        _close_debugger(d)
        assert log_file.exists()


# =============================================================================
# SECTION 3 : FletDebugger._setup_logging
# =============================================================================


class TestSetupLogging:
    "Tests pour FletDebugger._setup_logging."

    def test_with_console_handler(self, tmp_path):
        """Vérifie que _setup_logging(log_to_console=True) ajoute
        un StreamHandler au logger en plus du FileHandler."""
        d = FletDebugger(log_dir=str(tmp_path), log_to_console=True)
        has_stream = any(
            isinstance(h, logging.StreamHandler)
            and not isinstance(h, logging.FileHandler)
            for h in d.logger.handlers
        )
        _close_debugger(d)
        assert has_stream

    def test_without_console_handler(self, tmp_path):
        """Vérifie que _setup_logging(log_to_console=False) n ajoute pas
        de StreamHandler. Seul le FileHandler est présent."""
        d = FletDebugger(log_dir=str(tmp_path), log_to_console=False)
        has_stream = any(
            isinstance(h, logging.StreamHandler)
            and not isinstance(h, logging.FileHandler)
            for h in d.logger.handlers
        )
        _close_debugger(d)
        assert not has_stream

    def test_logger_level_is_debug(self, tmp_path):
        "Vérifie que le logger est configuré au niveau DEBUG."
        d = FletDebugger(log_dir=str(tmp_path), log_to_console=False)
        level = d.logger.level
        _close_debugger(d)
        assert level == logging.DEBUG


# =============================================================================
# SECTION 4 : FletDebugger log methods
# =============================================================================


class TestFletDebuggerLogMethods:
    "Tests pour les méthodes de log du FletDebugger."

    def _make_debugger(self, tmp_path):
        return FletDebugger(log_dir=str(tmp_path), log_to_console=False)

    def _read_log(self, d):
        _close_debugger(d)
        return d.log_file.read_text(encoding="utf-8")

    def test_log_app_start(self, tmp_path):
        "Vérifie que log_app_start() écrit Application starting dans le log."
        d = self._make_debugger(tmp_path)
        d.log_app_start()
        content = self._read_log(d)
        assert "Application Starting" in content

    def test_log_app_stop(self, tmp_path):
        "Vérifie que log_app_stop() écrit Application stopping dans le log."
        d = self._make_debugger(tmp_path)
        d.log_app_stop()
        content = self._read_log(d)
        assert "Application Stopped" in content

    def test_log_view_change(self, tmp_path):
        "Vérifie que log_view_change(search) écrit un message contenant search dans le log."
        d = self._make_debugger(tmp_path)
        d.log_view_change("search")
        content = self._read_log(d)
        assert "search" in content

    def test_log_animal_load_with_name(self, tmp_path):
        "Vérifie que log_animal_load(today, Canis lupus) écrit un message contenant today et Canis lupus."
        d = self._make_debugger(tmp_path)
        d.log_animal_load("today", "Canis lupus")
        content = self._read_log(d)
        assert "today" in content
        assert "Canis lupus" in content

    def test_log_animal_load_without_name(self, tmp_path):
        "Vérifie que log_animal_load(random, None) écrit un message contenant random sans planter sur None."
        d = self._make_debugger(tmp_path)
        d.log_animal_load("random", None)
        content = self._read_log(d)
        assert "random" in content

    def test_log_search(self, tmp_path):
        "Vérifie que log_search(lion, 5) écrit un message contenant lion et 5."
        d = self._make_debugger(tmp_path)
        d.log_search("lion", 5)
        content = self._read_log(d)
        assert "lion" in content
        assert "5" in content

    def test_log_error_with_exception(self, tmp_path):
        "Vérifie que log_error(context, ValueError(test)) écrit le contexte et l exception dans le log."
        d = self._make_debugger(tmp_path)
        d.log_error("mycontext", ValueError("test error"))
        content = self._read_log(d)
        assert "mycontext" in content
        assert "ValueError" in content

    def test_log_error_without_exception(self, tmp_path):
        "Vérifie que log_error(context, None) écrit le contexte dans le log sans planter."
        d = self._make_debugger(tmp_path)
        d.log_error("mycontext", None)
        content = self._read_log(d)
        assert "mycontext" in content

    def test_log_exception(self, tmp_path):
        "Vérifie que log_exception(exc_type, exc_value, exc_traceback) écrit un message CRITICAL avec les informations d exception."
        d = self._make_debugger(tmp_path)
        try:
            raise ValueError("uncaught!")
        except ValueError:
            import sys as _sys

            exc_type, exc_value, exc_tb = _sys.exc_info()
            d.log_exception(exc_type, exc_value, exc_tb)
        content = self._read_log(d)
        assert "CRITICAL" in content
        assert "Uncaught exception" in content


# =============================================================================
# SECTION 5 : FletDebugger utility methods
# =============================================================================


class TestFletDebuggerUtility:
    "Tests pour get_logger et print_log_location."

    def test_get_logger_returns_logger(self, tmp_path):
        "Vérifie que get_logger() retourne l instance logger interne."
        d = FletDebugger(log_dir=str(tmp_path), log_to_console=False)
        logger = d.get_logger()
        _close_debugger(d)
        assert logger is d.logger

    def test_print_log_location(self, tmp_path, capsys):
        "Vérifie que print_log_location() affiche le chemin absolu du fichier de log sur stdout."
        d = FletDebugger(log_dir=str(tmp_path), log_to_console=False)
        d.print_log_location()
        _close_debugger(d)
        captured = capsys.readouterr()
        assert str(d.log_file.name) in captured.out

    @patch(
        "builtins.print",
        side_effect=[UnicodeEncodeError("utf-8", "", 0, 1, "test"), None],
    )
    def test_print_log_location_unicode_error(self, mock_print, tmp_path):
        "Vérifie que print_log_location() gère UnicodeEncodeError sans lever d exception (fallback vers print simplifié)."
        d = FletDebugger(log_dir=str(tmp_path), log_to_console=False)
        d.print_log_location()  # Should not raise
        _close_debugger(d)


# =============================================================================
# SECTION 6 : get_debugger singleton
# =============================================================================


class TestGetDebugger:
    "Tests pour get_debugger()."

    def test_creates_new_debugger(self, tmp_path):
        "Vérifie que get_debugger() crée un FletDebugger quand aucun n existe encore (première invocation après reset du global)."
        assert debug_module._debugger is None
        d = get_debugger(log_dir=str(tmp_path), log_to_console=False)
        assert isinstance(d, FletDebugger)

    def test_returns_same_instance(self, tmp_path):
        "Vérifie que deux appels consécutifs à get_debugger() retournent le même objet (pattern singleton)."
        d1 = get_debugger(log_dir=str(tmp_path), log_to_console=False)
        d2 = get_debugger(log_dir=str(tmp_path), log_to_console=False)
        assert d1 is d2

    def test_installs_excepthook(self, tmp_path):
        "Vérifie que get_debugger() installe sys.excepthook pointant vers FletDebugger.log_exception."
        original_hook = sys.excepthook
        try:
            get_debugger(log_dir=str(tmp_path), log_to_console=False)
            assert sys.excepthook is not original_hook
        finally:
            sys.excepthook = original_hook


# =============================================================================
# SECTION 7 : Module-level log functions
# =============================================================================


class TestModuleLevelLogFunctions:
    "Tests pour log_info, log_error, log_debug au niveau module."

    @patch.object(debug_module, "_debugger")
    def test_log_info_with_debugger(self, mock_debugger):
        "Vérifie que log_info(msg) appelle _debugger.logger.info(msg) quand _debugger est initialisé."
        log_info("hello")
        mock_debugger.logger.info.assert_called_once_with("hello")

    @patch.object(debug_module, "_debugger", None)
    def test_log_info_without_debugger(self):
        "Vérifie que log_info(msg) ne plante pas quand _debugger est None. C est un no-op silencieux."
        log_info("hello")  # Should not raise

    @patch.object(debug_module, "_debugger")
    def test_log_error_function_with_debugger(self, mock_debugger):
        "Vérifie que log_error(msg) appelle _debugger.logger.error(msg)."
        log_error("error msg")
        mock_debugger.logger.error.assert_called_once_with("error msg")

    @patch.object(debug_module, "_debugger", None)
    def test_log_error_function_without_debugger(self):
        "Vérifie que log_error(msg) ne plante pas quand _debugger est None."
        log_error("error msg")  # Should not raise

    @patch.object(debug_module, "_debugger")
    def test_log_debug_with_debugger(self, mock_debugger):
        "Vérifie que log_debug(msg) appelle _debugger.logger.debug(msg)."
        log_debug("debug msg")
        mock_debugger.logger.debug.assert_called_once_with("debug msg")

    @patch.object(debug_module, "_debugger", None)
    def test_log_debug_without_debugger(self):
        "Vérifie que log_debug(msg) ne plante pas quand _debugger est None."
        log_debug("debug msg")  # Should not raise
