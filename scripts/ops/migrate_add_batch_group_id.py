"""SQLite migration: add batch_group_id to workerbucketentry."""

import sqlite3
import sys
from pathlib import Path


def migrate(db_path: Path) -> None:
    print(f"Migrating {db_path} ...")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Check if column already exists
    cursor.execute("PRAGMA table_info(workerbucketentry)")
    columns = {row[1] for row in cursor.fetchall()}

    if "batch_group_id" in columns:
        print("  Column batch_group_id already exists, skipping.")
    else:
        cursor.execute(
            "ALTER TABLE workerbucketentry ADD COLUMN batch_group_id VARCHAR"
        )
        conn.commit()
        print("  Added column batch_group_id.")

    conn.close()
    print("Done.")

if __name__ == "__main__":
    db_file = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("node_01.db")
    if not db_file.exists():
        print(f"Database {db_file} not found.")
        sys.exit(1)
    migrate(db_file)
