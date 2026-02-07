#!/usr/bin/env python3
"""
Filter and display relevant logs from Daynimal application.

This script filters out verbose Flet internal logs and shows only
application-level events (INFO, WARNING, ERROR, CRITICAL).

Usage (from project root):
    python debug/debug_filter.py                    # Show filtered latest log
    python debug/debug_filter.py --tail             # Follow filtered log
    python debug/debug_filter.py --errors-only      # Show only errors
    python debug/debug_filter.py --search "keyword" # Search for specific keyword
"""

import argparse
import re
import subprocess
import sys
import time
from pathlib import Path


def get_latest_log():
    """Get the most recent log file."""
    log_dir = Path("logs")
    if not log_dir.exists():
        return None

    log_files = sorted(
        log_dir.glob("daynimal_*.log"),
        key=lambda p: p.stat().st_mtime,
        reverse=True
    )
    return log_files[0] if log_files else None


def filter_line(line: str, errors_only: bool = False, search: str = None) -> bool:
    """Determine if a line should be displayed."""
    # Skip verbose Flet internal logs
    if " - flet_controls - DEBUG - " in line:
        return False
    if " - flet_transport - DEBUG - " in line:
        return False
    if " - flet_desktop - " in line and " - INFO - " in line:
        return False

    # Filter by level if errors_only
    if errors_only:
        if not any(level in line for level in [" - ERROR - ", " - CRITICAL - ", " - WARNING - "]):
            return False

    # Filter by search keyword
    if search and search.lower() not in line.lower():
        return False

    return True


def colorize_log_line(line: str) -> str:
    """Add color to log lines based on level (ANSI escape codes)."""
    if " - ERROR - " in line or " - CRITICAL - " in line:
        return f"\033[91m{line}\033[0m"  # Red
    elif " - WARNING - " in line:
        return f"\033[93m{line}\033[0m"  # Yellow
    elif " - INFO - " in line:
        return f"\033[92m{line}\033[0m"  # Green
    elif " - DEBUG - " in line:
        return f"\033[94m{line}\033[0m"  # Blue
    else:
        return line


def show_filtered_log(log_file: Path, errors_only: bool = False, search: str = None, colorize: bool = True):
    """Display filtered log file."""
    print(f"[LOG] {log_file}")
    print("=" * 60)

    with open(log_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.rstrip()
            if filter_line(line, errors_only=errors_only, search=search):
                try:
                    if colorize and sys.stdout.isatty():
                        print(colorize_log_line(line))
                    else:
                        print(line)
                except UnicodeEncodeError:
                    # Fallback for consoles that don't support full Unicode
                    print(line.encode('ascii', errors='replace').decode('ascii'))


def tail_filtered_log(log_file: Path, errors_only: bool = False, search: str = None):
    """Follow log file and display filtered lines in real-time."""
    print(f"[LOG] Following: {log_file}")
    print("[TIP] Press Ctrl+C to stop")
    print("=" * 60)

    with open(log_file, 'r', encoding='utf-8') as f:
        # Move to end of file
        f.seek(0, 2)

        try:
            while True:
                line = f.readline()
                if line:
                    line = line.rstrip()
                    if filter_line(line, errors_only=errors_only, search=search):
                        if sys.stdout.isatty():
                            print(colorize_log_line(line))
                        else:
                            print(line)
                else:
                    time.sleep(0.1)
        except KeyboardInterrupt:
            print("\n[STOP] Stopped following log file")


def show_statistics(log_file: Path):
    """Show statistics about the log file."""
    stats = {
        'total': 0,
        'debug': 0,
        'info': 0,
        'warning': 0,
        'error': 0,
        'critical': 0,
        'daynimal': 0,
        'flet': 0,
    }

    with open(log_file, 'r', encoding='utf-8') as f:
        for line in f:
            stats['total'] += 1
            if " - DEBUG - " in line:
                stats['debug'] += 1
            if " - INFO - " in line:
                stats['info'] += 1
            if " - WARNING - " in line:
                stats['warning'] += 1
            if " - ERROR - " in line:
                stats['error'] += 1
            if " - CRITICAL - " in line:
                stats['critical'] += 1
            if " - daynimal - " in line:
                stats['daynimal'] += 1
            if " - flet" in line:
                stats['flet'] += 1

    print(f"\n[STATS] {log_file.name}")
    print("=" * 60)
    print(f"Total lines:     {stats['total']:,}")
    print(f"  DEBUG:         {stats['debug']:,}")
    print(f"  INFO:          {stats['info']:,}")
    print(f"  WARNING:       {stats['warning']:,}")
    print(f"  ERROR:         {stats['error']:,}")
    print(f"  CRITICAL:      {stats['critical']:,}")
    print()
    print(f"Daynimal logs:   {stats['daynimal']:,} ({stats['daynimal']/stats['total']*100:.1f}%)")
    print(f"Flet logs:       {stats['flet']:,} ({stats['flet']/stats['total']*100:.1f}%)")
    print()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Filter and display Daynimal application logs"
    )
    parser.add_argument(
        "--tail",
        action="store_true",
        help="Follow the log file in real-time",
    )
    parser.add_argument(
        "--errors-only",
        action="store_true",
        help="Show only ERROR, CRITICAL, and WARNING logs",
    )
    parser.add_argument(
        "--search",
        type=str,
        help="Search for lines containing this keyword",
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="Show statistics about the log file",
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        help="Disable colored output",
    )
    args = parser.parse_args()

    # Get latest log file
    log_file = get_latest_log()
    if not log_file:
        print("No log files found in logs/ directory")
        print("Run the app with: python run_app_debug.py")
        sys.exit(1)

    # Show stats if requested
    if args.stats:
        show_statistics(log_file)
        return

    # Display filtered log
    colorize = not args.no_color

    if args.tail:
        tail_filtered_log(log_file, errors_only=args.errors_only, search=args.search)
    else:
        show_filtered_log(log_file, errors_only=args.errors_only, search=args.search, colorize=colorize)


if __name__ == "__main__":
    main()
