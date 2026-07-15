"""Slack Block Kit handoff messages."""

from __future__ import annotations

import os
import re
from typing import Any

import requests


def build_handoff_blocks(
    brand: dict[str, Any],
    classification: dict[str, Any],
    reply_text: str,
    reasoning_log: list[str] | None = None,
    *,
    action_taken: str | None = None,
    timestamp: str | None = None,
) -> list[dict[str, Any]]:
    log_text = "\n".join(f"- {line}" for line in (reasoning_log or [])) or "- Sin log"
    meeting_times = extract_meeting_times(reply_text)
    meeting_text = "\n".join(f"- {item}" for item in meeting_times) if meeting_times else "_No se detectaron horarios concretos._"

    return [
        {"type": "header", "text": {"type": "plain_text", "text": "Lead calificado - Addi Marketplace"}},
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": (
                    f"*Accion recomendada:* `{classification.get('suggested_action', 'N/A')}`  |  "
                    f"*Intent:* `{classification.get('intent_score', 'N/A')}`"
                ),
            },
        },
        {
            "type": "section",
            "fields": [
                {"type": "mrkdwn", "text": f"*Brand:*\n{brand.get('brand_id', '')}"},
                {"type": "mrkdwn", "text": f"*Categoria:*\n{brand.get('category', '')}"},
                {"type": "mrkdwn", "text": f"*Correo:*\n{brand.get('contacto_email', 'N/A')}"},
                {"type": "mrkdwn", "text": f"*WhatsApp:*\n{brand.get('contacto_whatsapp', 'N/A')}"},
                {"type": "mrkdwn", "text": f"*GMV 12m:*\nCOP {brand.get('gmv_cop_millions_12m', '')} MM"},
                {"type": "mrkdwn", "text": f"*Tier:*\n{brand.get('tier', '')}"},
                {"type": "mrkdwn", "text": f"*Score:*\n{brand.get('final_score', 'N/A')}"},
                {"type": "mrkdwn", "text": f"*Momentum:*\n{brand.get('gmv_90d_to_12m_ratio', 'N/A')}"},
            ],
        },
        {"type": "divider"},
        {"type": "section", "text": {"type": "mrkdwn", "text": f"*Horarios / disponibilidad detectada:*\n{meeting_text}"}},
        {"type": "section", "text": {"type": "mrkdwn", "text": f"*Reply completo del cliente:*\n>{reply_text}"}},
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": f"*Razonamiento LLM:*\n{classification.get('reasoning', '')}"},
        },
        {
            "type": "section",
            "fields": [
                {"type": "mrkdwn", "text": f"*Accion tomada:*\n{action_taken or 'N/A'}"},
                {"type": "mrkdwn", "text": f"*Timestamp:*\n{timestamp or 'N/A'}"},
            ],
        },
        {"type": "context", "elements": [{"type": "mrkdwn", "text": f"*Log:*\n{log_text}"}]},
    ]


def extract_meeting_times(reply_text: str) -> list[str]:
    lines = [line.strip("-* \t") for line in (reply_text or "").splitlines() if line.strip()]
    option_lines = [
        line
        for line in lines
        if re.search(
            r"\b(opcion|option|horario|horarios|agenda|agendar|lunes|martes|miercoles|jueves|viernes|sabado|domingo)\b",
            line,
            re.I,
        )
    ]
    if option_lines:
        return option_lines[:6]

    matches = re.findall(
        r"\b(?:\d{1,2}(?::\d{2})?\s*(?:am|pm|a\.m\.|p\.m\.)?|manana|tarde|lunes|martes|miercoles|jueves|viernes|sabado|domingo)\b",
        reply_text or "",
        flags=re.I,
    )
    return matches[:6]


def post_handoff(
    brand: dict[str, Any],
    classification: dict[str, Any],
    reply_text: str,
    reasoning_log: list[str] | None = None,
    *,
    webhook_url: str | None = None,
    dry_run: bool = True,
    action_taken: str | None = None,
    timestamp: str | None = None,
) -> dict[str, Any]:
    payload = {
        "text": "Lead calificado - Addi Marketplace",
        "blocks": build_handoff_blocks(
            brand,
            classification,
            reply_text,
            reasoning_log,
            action_taken=action_taken,
            timestamp=timestamp,
        ),
    }
    if dry_run:
        return {"dry_run": True, "payload": payload}

    url = webhook_url or os.environ.get("SLACK_WEBHOOK_URL")
    if not url:
        raise RuntimeError("SLACK_WEBHOOK_URL is required for live Slack handoff")
    response = requests.post(url, json=payload, timeout=15)
    response.raise_for_status()
    return {"sent": True, "status_code": response.status_code}
