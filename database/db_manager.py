import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "darkintel.db")

def get_db_connection():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    return sqlite3.connect(DB_PATH)

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS vendors (
        vendor_id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        alias TEXT
    )''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS vendor_identifiers (
        identifier_id INTEGER PRIMARY KEY AUTOINCREMENT,
        vendor_id INTEGER,
        type TEXT,
        value TEXT,
        FOREIGN KEY (vendor_id) REFERENCES vendors(vendor_id)
    )''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS dead_drops (
        drop_id INTEGER PRIMARY KEY AUTOINCREMENT,
        vendor_id INTEGER,
        raw_location_text TEXT,
        latitude REAL,
        longitude REAL,
        country TEXT
    )''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS raw_intel_logs (
        log_id INTEGER PRIMARY KEY AUTOINCREMENT,
        vendor_id INTEGER,
        market_or_forum TEXT,
        post_content TEXT,
        scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
