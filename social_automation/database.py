# database.py
import sqlite3
import os
from pathlib import Path
from contextlib import contextmanager

DB_PATH = Path(__file__).parent / "data.db"

def get_connection():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

@contextmanager
def get_db():
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()

def init_db():
    with get_db() as conn:
        cur = conn.cursor()
        # videos queue
        cur.execute("""
        CREATE TABLE IF NOT EXISTS videos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_path TEXT NOT NULL,
            title TEXT,
            description TEXT,
            tags TEXT,          -- comma separated
            status TEXT DEFAULT 'pending',  -- pending, posted, error
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            posted_at TIMESTAMP
        );
        """)
        # logs
        cur.execute("""
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            video_id INTEGER,
            platform TEXT,
            status TEXT,
            message TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(video_id) REFERENCES videos(id)
        );
        """)
        # accounts status
        cur.execute("""
        CREATE TABLE IF NOT EXISTS accounts (
            platform TEXT PRIMARY KEY,
            connected BOOLEAN DEFAULT 0,
            session_data TEXT,  -- JSON of cookies/tokens
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)
    print("Database initialized at", DB_PATH)

if __name__ == "__main__":
    init_db()
