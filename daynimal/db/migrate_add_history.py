"""
Migration script to add animal_history table to existing databases.

Run this if you already have a daynimal.db from before the history feature was added.
"""

from sqlalchemy import text

from daynimal.db.models import Base
from daynimal.db.session import get_engine


def migrate():
    """Create the animal_history table if it doesn't exist."""
    engine = get_engine()

    print("\n[Migrating Database - Adding History Table]")
    print("-" * 50)

    # Check if table already exists
    with engine.connect() as conn:
        result = conn.execute(
            text(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='animal_history'"
            )
        ).fetchone()

        if result:
            print("[OK] animal_history table already exists, no migration needed")
            return

    # Create all tables (will only create missing ones)
    Base.metadata.create_all(engine)

    print("[OK] Created animal_history table")
    print("-" * 50)
    print("[OK] Migration complete!")
    print("\nYou can now use: daynimal history")


if __name__ == "__main__":
    migrate()
