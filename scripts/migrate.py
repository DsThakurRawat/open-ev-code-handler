#!/usr/bin/env python3
"""Initialize or reset the CodeReview database."""
import sys
import os
# Ensure PYTHONPATH is set so we can import codereview_env
sys.path.append(os.getcwd())

from codereview_env.database import create_db_and_tables, get_engine
from codereview_env.config import get_settings
from sqlmodel import SQLModel

def init():
    settings = get_settings()
    print(f"Initializing database at: {settings.db_path}")
    create_db_and_tables()
    print("Database initialized successfully.")

def reset():
    settings = get_settings()
    engine = get_engine()
    print(f"Dropping all tables in: {settings.db_path}")
    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)
    print("Database reset successfully.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 scripts/migrate.py [init|reset]")
        sys.exit(1)
        
    cmd = sys.argv[1]
    if cmd == "init":
        init()
    elif cmd == "reset":
        reset()
    else:
        print(f"Unknown command: {cmd}. Use 'init' or 'reset'.")
        sys.exit(1)
