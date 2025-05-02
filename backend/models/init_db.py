import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'yk_dev.db')

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT UNIQUE NOT NULL,
    username TEXT UNIQUE NOT NULL,
    display_name TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS credentials (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    credential_id TEXT UNIQUE NOT NULL,
    public_key TEXT NOT NULL,
    sign_count INTEGER,
    nickname TEXT,
    registered_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS challenges (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    challenge TEXT NOT NULL,
    type TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    expires_at DATETIME,
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS seeds (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    encrypted_seed BLOB NOT NULL,
    iv BLOB NOT NULL,
    salt BLOB NOT NULL,
    wrapped_key BLOB NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS seed_credentials (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    seed_id INTEGER NOT NULL,
    credential_id INTEGER NOT NULL,
    FOREIGN KEY(seed_id) REFERENCES seeds(id) ON DELETE CASCADE,
    FOREIGN KEY(credential_id) REFERENCES credentials(id) ON DELETE CASCADE
);
"""

def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.executescript(SCHEMA)
        print("Database initialized.")

def reset_db():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("PRAGMA foreign_keys = OFF;")
        # Drop all tables
        cursor.executescript("""
        DROP TABLE IF EXISTS seed_credentials;
        DROP TABLE IF EXISTS seeds;
        DROP TABLE IF EXISTS challenges;
        DROP TABLE IF EXISTS credentials;
        DROP TABLE IF EXISTS users;
        """)
        conn.commit()
        cursor.execute("PRAGMA foreign_keys = ON;")
        print("All tables dropped.")
    init_db()

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Initialize or reset the SQLite database.")
    parser.add_argument('--reset', action='store_true', help='Reset (drop and recreate) all tables.')
    args = parser.parse_args()
    if args.reset:
        reset_db()
    else:
        init_db()

if __name__ == "__main__":
    main() 