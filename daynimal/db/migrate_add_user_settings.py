#!/usr/bin/env python3
"""
Migration script to add user_settings table.

This script adds the user_settings table to existing databases
to support app preferences like theme selection.

Usage:
    python -m daynimal.db.migrate_add_user_settings
    # Or with custom DB:
    python -m daynimal.db.migrate_add_user_settings --db path/to/daynimal.db
"""

import argparse
import sqlite3
import sys
from pathlib import Path


def migrate_add_user_settings(db_path: str) -> None:
    """
    Add user_settings table to database.

    Args:
        db_path: Path to the SQLite database
    """
    db_file = Path(db_path)

    if not db_file.exists():
        print(f"[ERROR] Database not found: {db_path}")
        sys.exit(1)

    print(f"[INFO] Migrating database: {db_path}")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Check if table already exists
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='user_settings'"
        )
        if cursor.fetchone():
            print("[OK] user_settings table already exists - skipping migration")
            return

        # Create user_settings table
        print("[INFO] Creating user_settings table...")
        cursor.execute("""
            CREATE TABLE user_settings (
                key TEXT PRIMARY KEY NOT NULL,
                value TEXT NOT NULL
            )
        """)

        # Add default theme setting
        cursor.execute(
            "INSERT INTO user_settings (key, value) VALUES (?, ?)",
            ("theme_mode", "light")
        )

        conn.commit()
        print("[OK] Migration successful!")
        print("   - user_settings table created")
        print("   - Default theme_mode set to 'light'")

    except Exception as e:
        print(f"[ERROR] Migration failed: {e}")
        conn.rollback()
        sys.exit(1)

    finally:
        conn.close()


def main():
    """Main entry point for migration script."""
    parser = argparse.ArgumentParser(
        description="Add user_settings table to Daynimal database"
    )
    parser.add_argument(
        "--db",
        type=str,
        default="daynimal.db",
        help="Path to database file (default: daynimal.db)",
    )

    args = parser.parse_args()
    migrate_add_user_settings(args.db)


if __name__ == "__main__":
    main()
