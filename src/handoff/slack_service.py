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
    return [
        {"type": "header", "text": {"type": "plain_text", "text": "Lead calificado - Addi Marketplace"}},
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": (
                    f"*Accion:* `{classification.get('suggested_action', 'N/A')}`  |  "
                    f"*Intent:* `{classification.get('intent_score', 'N/A')}`  |  "
                    f"*Tier:* `{brand.get('tier', 'N/A')}`"
                ),
            },
        },
        {
            "type": "section",
            "fields": [
                {"type": "mrkdwn", "text": f"*Brand:*\n{brand.get('brand_id', 'N/A')}"},
                {"type": "mrkdwn", "text": f"*Correo:*\n{brand.get('contacto_email', 'N/A')}"},
                {"type": "mrkdwn", "text": f"*WhatsApp:*\n{brand.get('contacto_whatsapp', 'N/A')}"},
                {"type": "mrkdwn", "text": f"*Categoria:*\n{brand.get('category', 'N/A')}"},
            ],
        },
        {"type": "section", "text": {"type": "mrkdwn", "text": f"*Reply:*\n```{format_reply_for_slack(reply_text)}```"}},
        {
            "type": "context",
            "elements": [{"type": "mrkdwn", "text": f"{action_taken or 'Handoff generado'} - {timestamp or 'sin timestamp'}"}],
        },
    ]


def format_reply_for_slack(reply_text: str, limit: int = 2500) -> str:
    safe_text = (reply_text or "").replace("```", "'''").strip()
    if len(safe_text) <= limit:
        return safe_text
    return safe_text[: limit - 30].rstrip() + "\n...[reply truncado]"


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
