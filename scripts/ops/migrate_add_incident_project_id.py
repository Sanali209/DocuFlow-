"""SQLite migration: add project_id to incidentlog."""

import sqlite3
import sys
from pathlib import Path


def migrate(db_path: Path) -> None:
    print(f"Migrating {db_path} ...")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("PRAGMA table_info(incidentlog)")
    columns = {row[1] for row in cursor.fetchall()}

    if "project_id" in columns:
        print("  Column project_id already exists, skipping.")
    else:
        cursor.execute(
            "ALTER TABLE incidentlog ADD COLUMN project_id INTEGER"
        )
        conn.commit()
        print("  Added column project_id.")

    conn.close()
    print("Done.")


if __name__ == "__main__":
    db_file = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("node_01.db")
    if not db_file.exists():
        print(f"Database {db_file} not found.")
        sys.exit(1)
    migrate(db_file)
