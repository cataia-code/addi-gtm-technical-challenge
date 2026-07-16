"""Repository helpers for the local agent memory database."""

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
    save_agent_interaction(
        run_id=brand_id,
        source="email_listener",
        event_type="reply_guardado",
        brand_id=brand_id,
        content=reply_text,
        metadata=classification or {},
    )


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


def prospect_exists(*, contact_email: str | None, contact_phone: str | None = None, linkedin_url: str | None = None) -> bool:
    conn = connect()
    row = conn.execute(
        """
        SELECT 1
        FROM prospect_consultations
        WHERE (contact_email IS NOT NULL AND contact_email = ?)
           OR (contact_phone IS NOT NULL AND contact_phone = ?)
           OR (linkedin_url IS NOT NULL AND linkedin_url = ?)
        LIMIT 1
        """,
        (contact_email, contact_phone, linkedin_url),
    ).fetchone()
    conn.close()
    return row is not None


def save_prospect_consultation(prospect: dict[str, Any]) -> None:
    conn = connect()
    conn.execute(
        """
        INSERT OR IGNORE INTO prospect_consultations (
            company_name, domain, industry, country, city, contact_name,
            contact_title, contact_email, contact_phone, linkedin_url, consulted_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            prospect.get("name"),
            prospect.get("domain"),
            prospect.get("industry"),
            prospect.get("country"),
            prospect.get("city"),
            prospect.get("contact_name"),
            prospect.get("contact_title"),
            prospect.get("contact_email"),
            prospect.get("contact_phone"),
            prospect.get("linkedin_url"),
            utc_now_iso(),
        ),
    )
    conn.commit()
    conn.close()
    save_agent_interaction(
        run_id=str(prospect.get("contact_email") or prospect.get("domain") or prospect.get("name")),
        source="prospecting_graph",
        event_type="prospecto_exportado",
        prospect_email=prospect.get("contact_email"),
        content=prospect.get("draft_email") or prospect.get("profile") or "",
        metadata=prospect,
    )


def save_agent_interaction(
    *,
    run_id: str,
    source: str,
    event_type: str,
    content: str,
    metadata: dict[str, Any] | None = None,
    brand_id: str | None = None,
    prospect_email: str | None = None,
) -> None:
    """Guarda una interaccion del agente para auditoria y busqueda tipo RAG."""
    metadata = metadata or {}
    embedding_text = " | ".join(
        str(value)
        for value in [
            run_id,
            source,
            event_type,
            brand_id,
            prospect_email,
            content,
            json.dumps(metadata, ensure_ascii=False, sort_keys=True),
        ]
        if value
    )
    conn = connect()
    conn.execute(
        """
        INSERT INTO agent_interactions (
            run_id, source, event_type, brand_id, prospect_email,
            content, metadata_json, embedding_text, created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            run_id,
            source,
            event_type,
            brand_id,
            prospect_email,
            content,
            json.dumps(metadata, ensure_ascii=False),
            embedding_text,
            utc_now_iso(),
        ),
    )
    conn.commit()
    conn.close()


def list_agent_interactions(limit: int = 50) -> list[dict[str, Any]]:
    conn = connect()
    rows = conn.execute(
        "SELECT * FROM agent_interactions ORDER BY created_at DESC, id DESC LIMIT ?",
        (limit,),
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def search_agent_interactions(query: str, limit: int = 10) -> list[dict[str, Any]]:
    """Busqueda local simple sobre la memoria; queda lista para cambiar a vectores."""
    like_query = f"%{query}%"
    conn = connect()
    rows = conn.execute(
        """
        SELECT * FROM agent_interactions
        WHERE embedding_text LIKE ?
        ORDER BY created_at DESC, id DESC
        LIMIT ?
        """,
        (like_query, limit),
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]
