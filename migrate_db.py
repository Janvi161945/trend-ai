#!/usr/bin/env python3
"""
Database migration script to add missing columns to existing database.
"""
import sqlite3
import os
from src.config import DATABASE_PATH

def check_column_exists(cursor, table_name, column_name):
    """Check if a column exists in a table."""
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [col[1] for col in cursor.fetchall()]
    return column_name in columns

def migrate():
    """Add missing columns to the database."""
    print(f"Migrating database at: {DATABASE_PATH}")

    if not os.path.exists(DATABASE_PATH):
        print("❌ Database not found. Please run init_db() first.")
        return

    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    # Check and add missing columns to creators table
    missing_columns = []

    columns_to_check = {
        'last_post_id': 'TEXT',
        'last_post_date': 'TIMESTAMP',
        'last_scraped_at': 'TIMESTAMP'
    }

    for col_name, col_type in columns_to_check.items():
        if not check_column_exists(cursor, 'creators', col_name):
            missing_columns.append((col_name, col_type))
            print(f"  ➕ Adding column: {col_name} ({col_type})")
            cursor.execute(f"ALTER TABLE creators ADD COLUMN {col_name} {col_type}")
        else:
            print(f"  ✅ Column already exists: {col_name}")

    conn.commit()
    conn.close()

    if missing_columns:
        print(f"\n✅ Migration complete! Added {len(missing_columns)} column(s).")
    else:
        print("\n✅ Database schema is up to date.")

if __name__ == "__main__":
    migrate()