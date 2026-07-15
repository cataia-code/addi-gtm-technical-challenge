"""Repository helpers for the local demo database."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

from .models import connect


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def was_contacted_recently(brand_id: str, days: int = 14) -> bool:
    conn = connect()
    row = conn.execute("SELECT contacted_at FROM contact_log WHERE brand_id = ?", (brand_id,)).fetchone()
    conn.close()
    if not row:
        return False
    contacted_at = datetime.fromisoformat(row["contacted_at"])
    return contacted_at >= datetime.now(timezone.utc) - timedelta(days=days)


def mark_contacted(brand_id: str, channel: str) -> None:
    conn = connect()
    conn.execute(
        "INSERT OR REPLACE INTO contact_log (brand_id, contacted_at, channel) VALUES (?, ?, ?)",
        (brand_id, utc_now_iso(), channel),
    )
    conn.commit()
    conn.close()


def has_opt_in(brand_id: str, canal: str) -> bool:
    conn = connect()
    row = conn.execute(
        "SELECT 1 FROM opt_ins WHERE brand_id = ? AND canal = ?",
        (brand_id, canal),
    ).fetchone()
    conn.close()
    return row is not None


def grant_opt_in(brand_id: str, canal: str) -> None:
    conn = connect()
    conn.execute(
        "INSERT OR REPLACE INTO opt_ins (brand_id, canal, otorgado_en) VALUES (?, ?, ?)",
        (brand_id, canal, utc_now_iso()),
    )
    conn.commit()
    conn.close()


def save_reply(brand_id: str, reply_text: str, classification: dict | None = None) -> None:
    conn = connect()
    conn.execute(
        "INSERT INTO replies (brand_id, texto_reply, timestamp, clasificacion_json) VALUES (?, ?, ?, ?)",
        (
            brand_id,
            reply_text,
            utc_now_iso(),
            json.dumps(classification, ensure_ascii=False) if classification else None,
        ),
    )
    conn.commit()
    conn.close()

