"""SQLite schema management."""

from __future__ import annotations

import sqlite3
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DB_PATH = ROOT / "live_demo" / "gtm_demo.sqlite3"


SCHEMA = """
CREATE TABLE IF NOT EXISTS leads (
    brand_id TEXT PRIMARY KEY,
    category TEXT,
    gmv_cop_millions_12m REAL,
    tier TEXT,
    contacto_email TEXT,
    contacto_whatsapp TEXT,
    thread_id TEXT,
    contactado_en TEXT
);

CREATE TABLE IF NOT EXISTS replies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    brand_id TEXT,
    texto_reply TEXT,
    timestamp TEXT,
    clasificacion_json TEXT
);

CREATE TABLE IF NOT EXISTS opt_ins (
    brand_id TEXT,
    canal TEXT,
    otorgado_en TEXT
);
"""


def connect(db_path: Path = DEFAULT_DB_PATH) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    conn.commit()
    return conn

