import os
import sqlite3

db_path = r"d:\github\DocuFlow-\sql_app.db"
if not os.path.exists(db_path):
    print(f"DB not found at {db_path} (root)")

print(f"Opening DB: {db_path}")
try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print("Tables:")
    for t in tables:
        print(t[0])

    print("-" * 20)
    # Try querying config/settings if name found
    for t in tables:
        if "setting" in t[0] or "config" in t[0]:
            print(f"\n--- Querying {t[0]} ---")
            cursor.execute(f"SELECT * FROM {t[0]}")
            rows = cursor.fetchall()
            for r in rows:
                print(f"  {r}")
    conn.close()
except Exception as e:
    print(f"Error: {e}")
