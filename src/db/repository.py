"""Repository helpers for the local demo database."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from typing import Any

from .models import connect


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def upsert_lead(
    brand_id: str,
    *,
    category: str | None = None,
    gmv_cop_millions_12m: float | None = None,
    tier: str | None = None,
    contacto_email: str | None = None,
    contacto_whatsapp: str | None = None,
    thread_id: str | None = None,
    contactado_en: str | None = None,
) -> None:
    conn = connect()
    conn.execute(
        """
        INSERT INTO leads (
            brand_id, category, gmv_cop_millions_12m, tier, contacto_email,
            contacto_whatsapp, thread_id, contactado_en
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(brand_id) DO UPDATE SET
            category=COALESCE(excluded.category, leads.category),
            gmv_cop_millions_12m=COALESCE(excluded.gmv_cop_millions_12m, leads.gmv_cop_millions_12m),
            tier=COALESCE(excluded.tier, leads.tier),
            contacto_email=COALESCE(excluded.contacto_email, leads.contacto_email),
            contacto_whatsapp=COALESCE(excluded.contacto_whatsapp, leads.contacto_whatsapp),
            thread_id=COALESCE(excluded.thread_id, leads.thread_id),
            contactado_en=COALESCE(excluded.contactado_en, leads.contactado_en)
        """,
        (
            brand_id,
            category,
            gmv_cop_millions_12m,
            tier,
            contacto_email,
            contacto_whatsapp,
            thread_id,
            contactado_en,
        ),
    )
    conn.commit()
    conn.close()


def get_lead(brand_id: str) -> dict[str, Any] | None:
    conn = connect()
    row = conn.execute("SELECT * FROM leads WHERE brand_id = ?", (brand_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def was_contacted_recently(brand_id: str, days: int = 14) -> bool:
    lead = get_lead(brand_id)
    if not lead or not lead.get("contactado_en"):
        return False
    contacted_at = datetime.fromisoformat(lead["contactado_en"])
    return contacted_at >= datetime.now(timezone.utc) - timedelta(days=days)


def mark_contacted(brand_id: str, channel: str = "email", thread_id: str | None = None) -> None:
    del channel
    upsert_lead(brand_id, thread_id=thread_id, contactado_en=utc_now_iso())


def save_reply(brand_id: str, reply_text: str, classification: dict | None = None) -> None:
    conn = connect()
    conn.execute(
        """
        INSERT INTO replies (brand_id, texto_reply, timestamp, clasificacion_json)
        VALUES (?, ?, ?, ?)
        """,
        (
            brand_id,
            reply_text,
            utc_now_iso(),
            json.dumps(classification, ensure_ascii=False) if classification else None,
        ),
    )
    conn.commit()
    conn.close()


def list_replies(brand_id: str) -> list[dict[str, Any]]:
    conn = connect()
    rows = conn.execute(
        "SELECT * FROM replies WHERE brand_id = ? ORDER BY timestamp",
        (brand_id,),
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def grant_opt_in(brand_id: str, canal: str, otorgado_en: str | None = None) -> None:
    conn = connect()
    conn.execute(
        "INSERT INTO opt_ins (brand_id, canal, otorgado_en) VALUES (?, ?, ?)",
        (brand_id, canal, otorgado_en or utc_now_iso()),
    )
    conn.commit()
    conn.close()


def revoke_opt_in(brand_id: str, canal: str) -> None:
    conn = connect()
    conn.execute("DELETE FROM opt_ins WHERE brand_id = ? AND canal = ?", (brand_id, canal))
    conn.commit()
    conn.close()


def has_opt_in(brand_id: str, canal: str) -> bool:
    conn = connect()
    row = conn.execute(
        "SELECT 1 FROM opt_ins WHERE brand_id = ? AND canal = ? LIMIT 1",
        (brand_id, canal),
    ).fetchone()
    conn.close()
    return row is not None
