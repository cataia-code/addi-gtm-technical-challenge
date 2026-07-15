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
    final_score REAL,
    tier TEXT,
    contactado_en TEXT
);

CREATE TABLE IF NOT EXISTS replies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    brand_id TEXT NOT NULL,
    texto_reply TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    clasificacion_json TEXT
);

CREATE TABLE IF NOT EXISTS opt_ins (
    brand_id TEXT NOT NULL,
    canal TEXT NOT NULL,
    otorgado_en TEXT NOT NULL,
    PRIMARY KEY (brand_id, canal)
);

CREATE TABLE IF NOT EXISTS contact_log (
    brand_id TEXT PRIMARY KEY,
    contacted_at TEXT NOT NULL,
    channel TEXT NOT NULL
);
"""


def connect(db_path: Path = DEFAULT_DB_PATH) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    conn.commit()
    return conn

