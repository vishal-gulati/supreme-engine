"""Storage module for The Daily Broadsheet newspaper app.
Handles SQLite database persistence for sources, configuration, and editions.
"""

import json
import os
import sqlite3
import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "newspaper.db")


def get_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS config (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sources (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                url TEXT NOT NULL UNIQUE,
                section TEXT NOT NULL,
                enabled INTEGER DEFAULT 1,
                max_items INTEGER DEFAULT 5,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS editions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                edition_number INTEGER NOT NULL,
                date_str TEXT NOT NULL,
                title TEXT NOT NULL,
                content_json TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()


def get_config():
    default_config = {
        "paper_name": "THE DAILY CHRONICLE",
        "motto": "The Independent Reader's Compendium of Record",
        "city": "India & Global Edition",
        "weather_city": "Bengaluru",
        "price": "Two Bits",
        "theme": "classic",
        "gemini_api_key": "",
        "lead_section": "Front Page",
        "ai_rewriting": "0",
    }
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT key, value FROM config")
        rows = cursor.fetchall()
        for r in rows:
            default_config[r["key"]] = r["value"]
    return default_config


def update_config(key_value_pairs):
    with get_db() as conn:
        cursor = conn.cursor()
        for k, v in key_value_pairs.items():
            cursor.execute(
                "INSERT INTO config (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                (k, str(v)),
            )
        conn.commit()


def get_sources():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM sources ORDER BY section ASC, name ASC")
        return [dict(r) for r in cursor.fetchall()]


def add_source(name, url, section, enabled=1, max_items=5):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO sources (name, url, section, enabled, max_items)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(url) DO UPDATE SET
                name=excluded.name,
                section=excluded.section,
                enabled=excluded.enabled,
                max_items=excluded.max_items
        """, (name, url, section, enabled, max_items))
        conn.commit()
        return cursor.lastrowid


def update_source(source_id, **kwargs):
    fields = []
    values = []
    for k, v in kwargs.items():
        if k in ("name", "url", "section", "enabled", "max_items"):
            fields.append(f"{k} = ?")
            values.append(v)
    if not fields:
        return False
    values.append(source_id)
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(f"UPDATE sources SET {', '.join(fields)} WHERE id = ?", tuple(values))
        conn.commit()
        return cursor.rowcount > 0


def delete_source(source_id):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM sources WHERE id = ?", (source_id,))
        conn.commit()
        return cursor.rowcount > 0


def save_edition(edition_data):
    content_json = json.dumps(edition_data, ensure_ascii=False)
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) as count FROM editions")
        count = cursor.fetchone()["count"]
        edition_number = count + 1
        date_str = edition_data.get("date_str", datetime.date.today().strftime("%A, %B %d, %Y"))
        title = edition_data.get("title", f"Edition #{edition_number}")

        cursor.execute("""
            INSERT INTO editions (edition_number, date_str, title, content_json)
            VALUES (?, ?, ?, ?)
        """, (edition_number, date_str, title, content_json))
        conn.commit()
        edition_id = cursor.lastrowid
        edition_data["id"] = edition_id
        edition_data["edition_number"] = edition_number
        return edition_id


def get_editions(limit=20):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, edition_number, date_str, title, created_at
            FROM editions
            ORDER BY id DESC
            LIMIT ?
        """, (limit,))
        return [dict(r) for r in cursor.fetchall()]


def get_edition_by_id(edition_id):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM editions WHERE id = ?", (edition_id,))
        row = cursor.fetchone()
        if not row:
            return None
        res = dict(row)
        res["content"] = json.loads(res["content_json"])
        return res


def get_latest_edition():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM editions ORDER BY id DESC LIMIT 1")
        row = cursor.fetchone()
        if not row:
            return None
        res = dict(row)
        res["content"] = json.loads(res["content_json"])
        return res


def delete_edition(edition_id):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM editions WHERE id = ?", (edition_id,))
        conn.commit()
        return cursor.rowcount > 0
