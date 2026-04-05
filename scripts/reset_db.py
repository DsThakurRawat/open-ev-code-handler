#!/usr/bin/env python3
"""
Reset the CodeLens database: deletes the SQLite file and re-initializes tables.
Useful for clearing test data and starting fresh evaluation benchmarks.
"""

import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from codelens_env.config import get_settings
from codelens_env.database import create_db_and_tables

def reset_db():
    settings = get_settings()
    db_path = Path(settings.db_path)
    
    # 1. Delete existing database file
    if db_path.exists():
        print(f"Removing existing database at: {db_path}")
        try:
            os.remove(db_path)
            print("Successfully deleted old records.")
        except Exception as e:
            print(f"Error deleting file: {e}")
            sys.exit(1)
    else:
        print(f"No existing database found at {db_path}")

    # 2. Re-initialize
    print(f"Re-initializing schema...")
    try:
        create_db_and_tables()
        print("Database reset successfully. You now have a clean dashboard.")
    except Exception as e:
        print(f"Error re-initializing: {e}")
        sys.exit(1)

if __name__ == "__main__":
    confirm = input("This will permanently delete all leaderboard and episode data. Proceed? [y/N]: ")
    if confirm.lower() == 'y':
        reset_db()
    else:
        print("Reset aborted.")
