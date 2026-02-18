#!/usr/bin/env python3
"""
Debug launcher for Daynimal Flet application.

This script launches the Flet app with full debug logging enabled.
Logs are written to logs/ directory with timestamps.

Usage (from project root):
    python debug/run_app_debug.py              # Run with console logs
    python debug/run_app_debug.py --quiet      # Run without console logs (file only)
    python debug/run_app_debug.py --tail       # Run and tail the log file in parallel
"""

import argparse
import subprocess
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from daynimal.debug import get_debugger


def main():
    """Launch the Flet app with debugging enabled."""
    parser = argparse.ArgumentParser(
        description="Launch Daynimal Flet app with debug logging"
    )
    parser.add_argument(
        "--quiet", action="store_true", help="Disable console logging (file only)"
    )
    parser.add_argument(
        "--tail",
        action="store_true",
        help="Tail the log file in a separate window (Windows only)",
    )
    parser.add_argument(
        "--web", action="store_true", help="Run as web app instead of desktop"
    )
    args = parser.parse_args()

    # Initialize debugger
    log_to_console = not args.quiet
    debugger = get_debugger(log_dir="logs", log_to_console=log_to_console)

    # Print log location
    debugger.print_log_location()

    # Log startup
    debugger.log_app_start()

    # Tail log file if requested (Windows)
    tail_process = None
    if args.tail:
        try:
            # Try PowerShell Get-Content -Wait (Windows equivalent of tail -f)
            tail_process = subprocess.Popen(
                [
                    "powershell",
                    "-Command",
                    f"Get-Content -Path '{debugger.log_file}' -Wait",
                ],
                creationflags=subprocess.CREATE_NEW_CONSOLE
                if sys.platform == "win32"
                else 0,
            )
            debugger.logger.info("Opened tail window for log file")
        except Exception as e:
            debugger.logger.warning(f"Could not start tail process: {e}")

    try:
        # Import and run the app
        import flet as ft
        from daynimal.app import DaynimalApp

        def app_main(page: ft.Page):
            from daynimal.app import _install_asyncio_exception_handler

            _install_asyncio_exception_handler()
            # Store debugger reference in page for access from app
            page.data = {"debugger": debugger}
            DaynimalApp(page)

        # Choose run mode
        if args.web:
            debugger.logger.info("Running in WEB mode")
            ft.run(main=app_main, view=ft.AppView.WEB_BROWSER, port=8000)
        else:
            debugger.logger.info("Running in DESKTOP mode")
            ft.run(main=app_main)

    except KeyboardInterrupt:
        debugger.logger.info("Application interrupted by user")
    except Exception as e:
        debugger.log_error("main", e)
        raise
    finally:
        # Log shutdown
        debugger.log_app_stop()

        # Clean up tail process
        if tail_process:
            tail_process.terminate()

        try:
            print(f"\n[OK] Application closed. Logs saved to: {debugger.log_file}")
        except UnicodeEncodeError:
            print(f"\nApplication closed. Logs: {debugger.log_file}")


if __name__ == "__main__":
    main()
