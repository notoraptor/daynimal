#!/usr/bin/env python3
"""
Utility script to view Daynimal logs.

Usage (from project root):
    python debug/view_logs.py              # Show latest log file
    python debug/view_logs.py --tail       # Follow latest log file (real-time)
    python debug/view_logs.py --list       # List all log files
    python debug/view_logs.py --all        # Show all logs concatenated
"""

import argparse
import subprocess
import sys
from pathlib import Path


def get_log_files():
    """Get all log files sorted by modification time (newest first)."""
    log_dir = Path("logs")
    if not log_dir.exists():
        return []

    log_files = sorted(
        log_dir.glob("daynimal_*.log"), key=lambda p: p.stat().st_mtime, reverse=True
    )
    return log_files


def show_latest_log(tail: bool = False):
    """Show or tail the latest log file."""
    log_files = get_log_files()

    if not log_files:
        print("No log files found in logs/ directory")
        print("Run the app with: python run_app_debug.py")
        return

    latest_log = log_files[0]
    print(f"[LOG] {latest_log}")
    print("=" * 60)

    if tail:
        # Follow the log file
        try:
            if sys.platform == "win32":
                subprocess.run(
                    [
                        "powershell",
                        "-Command",
                        f"Get-Content -Path '{latest_log}' -Wait",
                    ],
                    check=True,
                )
            else:
                subprocess.run(["tail", "-f", str(latest_log)], check=True)
        except KeyboardInterrupt:
            print("\nStopped following log file")
    else:
        # Show the entire file
        with open(latest_log, "r", encoding="utf-8") as f:
            print(f.read())


def list_log_files():
    """List all log files with their sizes and timestamps."""
    log_files = get_log_files()

    if not log_files:
        print("No log files found in logs/ directory")
        return

    print(f"Found {len(log_files)} log file(s):\n")

    for log_file in log_files:
        stat = log_file.stat()
        size_kb = stat.st_size / 1024
        mtime = Path(log_file).stat().st_mtime

        from datetime import datetime

        mtime_str = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")

        print(f"  {log_file.name}")
        print(f"    Size: {size_kb:.1f} KB")
        print(f"    Modified: {mtime_str}")
        print()


def show_all_logs():
    """Show all log files concatenated."""
    log_files = get_log_files()

    if not log_files:
        print("No log files found in logs/ directory")
        return

    print(f"[LOG] Showing {len(log_files)} log file(s)")
    print("=" * 60)

    for log_file in reversed(log_files):  # Oldest first
        print(f"\n### {log_file.name} ###\n")
        with open(log_file, "r", encoding="utf-8") as f:
            print(f.read())
        print("\n" + "=" * 60)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="View Daynimal application logs")
    parser.add_argument(
        "--tail", action="store_true", help="Follow the latest log file (real-time)"
    )
    parser.add_argument("--list", action="store_true", help="List all log files")
    parser.add_argument("--all", action="store_true", help="Show all logs concatenated")
    args = parser.parse_args()

    if args.list:
        list_log_files()
    elif args.all:
        show_all_logs()
    else:
        show_latest_log(tail=args.tail)


if __name__ == "__main__":
    main()
