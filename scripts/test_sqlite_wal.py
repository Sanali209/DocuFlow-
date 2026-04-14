
import sqlite3
import os
from sqlalchemy import text
from sqlmodel import Session, create_engine, SQLModel
from docuflow.infrastructure.config import Config
from docuflow.infrastructure.di import AppProvider

def check_wal(node_id):
    db_file = f"{node_id}.db"
    if not os.path.exists(db_file):
        print(f"Database {db_file} not found.")
        return

    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    cursor.execute("PRAGMA journal_mode")
    mode = cursor.fetchone()[0]
    print(f"Database: {db_file}, Journal Mode: {mode}")
    
    cursor.execute("PRAGMA synchronous")
    sync = cursor.fetchone()[0]
    print(f"Synchronous: {sync} (1=NORMAL, 2=FULL)")
    
    conn.close()

def main():
    config = Config(node_id="test_opt")
    provider = AppProvider(config)
    engine = provider.get_engine(config)
    
    # Trigger connection and check pragmas within the same connection
    with engine.connect() as conn:
        mode = conn.execute(text("PRAGMA journal_mode")).fetchone()[0]
        sync = conn.execute(text("PRAGMA synchronous")).fetchone()[0]
        fk = conn.execute(text("PRAGMA foreign_keys")).fetchone()[0]
        print(f"SQLAlchemy Connection - Mode: {mode}, Synchronous: {sync}, FK: {fk}")
    
    # Clean up test DB (dispose engine first to release file locks on Windows)
    engine.dispose()
    if os.path.exists("test_opt.db"):
        os.remove("test_opt.db")
    if os.path.exists("test_opt.db-wal"):
        os.remove("test_opt.db-wal")
    if os.path.exists("test_opt.db-shm"):
        os.remove("test_opt.db-shm")

if __name__ == "__main__":
    main()
