"""
Debug utilities for Daynimal Flet app.

Provides logging configuration and utilities to capture application logs,
stdout/stderr, and exceptions for easier debugging of the Flet application.
"""

import logging
import sys
from datetime import datetime
from pathlib import Path


class FletDebugger:
    """Centralized debugging system for Flet applications."""

    def __init__(self, log_dir: str = "logs", log_to_console: bool = True):
        """
        Initialize the Flet debugger.

        Args:
            log_dir: Directory to store log files
            log_to_console: Whether to also output logs to console
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)

        # Generate log filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_file = self.log_dir / f"daynimal_{timestamp}.log"

        # Configure logging
        self._setup_logging(log_to_console)

        # Store original stdout/stderr
        self.original_stdout = sys.stdout
        self.original_stderr = sys.stderr

    def _setup_logging(self, log_to_console: bool):
        """Configure Python logging with file and optional console handlers."""
        # Create logger
        self.logger = logging.getLogger("daynimal")
        self.logger.setLevel(logging.DEBUG)

        # Remove existing handlers
        self.logger.handlers.clear()

        # File handler (always enabled)
        file_handler = logging.FileHandler(self.log_file, encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        file_handler.setFormatter(file_formatter)
        self.logger.addHandler(file_handler)

        # Console handler (optional)
        if log_to_console:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(logging.INFO)
            console_formatter = logging.Formatter(
                "%(levelname)s: %(message)s"
            )
            console_handler.setFormatter(console_formatter)
            self.logger.addHandler(console_handler)

        # Also capture root logger
        logging.basicConfig(
            level=logging.DEBUG,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[file_handler],
        )

    def log_app_start(self):
        """Log application startup."""
        self.logger.info("=" * 60)
        self.logger.info("Daynimal Flet Application Starting")
        self.logger.info(f"Log file: {self.log_file}")
        self.logger.info("=" * 60)

    def log_app_stop(self):
        """Log application shutdown."""
        self.logger.info("=" * 60)
        self.logger.info("Daynimal Flet Application Stopped")
        self.logger.info("=" * 60)

    def log_view_change(self, view_name: str):
        """Log navigation to a new view."""
        self.logger.info(f"View changed to: {view_name}")

    def log_animal_load(self, mode: str, animal_name: str = None):
        """Log animal loading."""
        if animal_name:
            self.logger.info(f"Loading animal ({mode}): {animal_name}")
        else:
            self.logger.info(f"Loading animal ({mode})...")

    def log_search(self, query: str, results_count: int):
        """Log search operation."""
        self.logger.info(f"Search: '{query}' - {results_count} results")

    def log_error(self, context: str, error: Exception):
        """Log an error with context."""
        self.logger.error(f"Error in {context}: {type(error).__name__}: {error}")
        self.logger.exception(error)

    def log_exception(self, exc_type, exc_value, exc_traceback):
        """Log uncaught exception (for sys.excepthook)."""
        self.logger.critical(
            "Uncaught exception",
            exc_info=(exc_type, exc_value, exc_traceback)
        )

    def get_logger(self):
        """Get the logger instance for custom logging."""
        return self.logger

    def print_log_location(self):
        """Print the log file location to console."""
        # Use safe strings for Windows console (no emojis)
        try:
            print(f"\n[LOG] Logs are being written to: {self.log_file.absolute()}")
            print(f"[TIP] To follow logs in real-time, run:")
            print(f"      Get-Content -Path '{self.log_file.absolute()}' -Wait\n")
        except UnicodeEncodeError:
            # Fallback for very restrictive consoles
            print(f"\nLogs: {self.log_file.absolute()}\n")


# Global debugger instance
_debugger = None


def get_debugger(log_dir: str = "logs", log_to_console: bool = True) -> FletDebugger:
    """
    Get or create the global debugger instance.

    Args:
        log_dir: Directory to store log files
        log_to_console: Whether to also output logs to console

    Returns:
        The global FletDebugger instance
    """
    global _debugger
    if _debugger is None:
        _debugger = FletDebugger(log_dir=log_dir, log_to_console=log_to_console)

        # Set up global exception handler
        def exception_handler(exc_type, exc_value, exc_traceback):
            _debugger.log_exception(exc_type, exc_value, exc_traceback)
            # Call the original exception handler
            sys.__excepthook__(exc_type, exc_value, exc_traceback)

        sys.excepthook = exception_handler

    return _debugger


def log_info(message: str):
    """Quick logging function - info level."""
    if _debugger:
        _debugger.logger.info(message)


def log_error(message: str):
    """Quick logging function - error level."""
    if _debugger:
        _debugger.logger.error(message)


def log_debug(message: str):
    """Quick logging function - debug level."""
    if _debugger:
        _debugger.logger.debug(message)
