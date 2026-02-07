#!/usr/bin/env python3
"""
Migration script to add favorites table.

This script adds the favorites table to existing databases
to support marking animals as favorites.

Usage:
    python -m daynimal.db.migrate_add_favorites
    # Or with custom DB:
    python -m daynimal.db.migrate_add_favorites --db path/to/daynimal.db
"""

import argparse
import sqlite3
import sys
from pathlib import Path


def migrate_add_favorites(db_path: str) -> None:
    """
    Add favorites table to database.

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
            "SELECT name FROM sqlite_master WHERE type='table' AND name='favorites'"
        )
        if cursor.fetchone():
            print("[OK] favorites table already exists - skipping migration")
            return

        # Create favorites table
        print("[INFO] Creating favorites table...")
        cursor.execute("""
            CREATE TABLE favorites (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                taxon_id INTEGER NOT NULL,
                added_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (taxon_id) REFERENCES taxa (taxon_id) ON DELETE CASCADE
            )
        """)

        # Create indexes
        print("[INFO] Creating indexes...")
        cursor.execute("""
            CREATE UNIQUE INDEX ix_favorites_taxon_id ON favorites (taxon_id)
        """)
        cursor.execute("""
            CREATE INDEX ix_favorites_added_at ON favorites (added_at)
        """)

        conn.commit()
        print("[OK] Migration successful!")
        print("   - favorites table created")
        print("   - Indexes created (taxon_id unique, added_at)")

    except Exception as e:
        print(f"[ERROR] Migration failed: {e}")
        conn.rollback()
        sys.exit(1)

    finally:
        conn.close()


def main():
    """Main entry point for migration script."""
    parser = argparse.ArgumentParser(
        description="Add favorites table to Daynimal database"
    )
    parser.add_argument(
        "--db",
        type=str,
        default="daynimal.db",
        help="Path to database file (default: daynimal.db)",
    )

    args = parser.parse_args()
    migrate_add_favorites(args.db)


if __name__ == "__main__":
    main()
