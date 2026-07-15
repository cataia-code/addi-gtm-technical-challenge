"""Slack Block Kit handoff messages."""

from __future__ import annotations

import os
from typing import Any

import requests


def build_handoff_blocks(
    brand: dict[str, Any],
    classification: dict[str, Any],
    reply_text: str,
    reasoning_log: list[str] | None = None,
) -> list[dict[str, Any]]:
    log_text = "\n".join(f"- {line}" for line in (reasoning_log or [])) or "- Sin log"
    return [
        {"type": "section", "text": {"type": "mrkdwn", "text": "*Lead calificado - Addi Marketplace*"}},
        {"type": "divider"},
        {
            "type": "section",
            "fields": [
                {"type": "mrkdwn", "text": f"*Brand:*\n{brand.get('brand_id')}"},
                {"type": "mrkdwn", "text": f"*Categoria:*\n{brand.get('category')}"},
                {"type": "mrkdwn", "text": f"*GMV 12m:*\nCOP {brand.get('gmv_cop_millions_12m')} MM"},
                {"type": "mrkdwn", "text": f"*Score:*\n{brand.get('final_score', 'N/A')}"},
            ],
        },
        {"type": "section", "text": {"type": "mrkdwn", "text": f"*Reply:*\n>{reply_text}"}},
        {
            "type": "section",
            "fields": [
                {"type": "mrkdwn", "text": f"*Intent:*\n{classification.get('intent_score')}/100"},
                {"type": "mrkdwn", "text": f"*Accion:*\n{classification.get('suggested_action')}"},
            ],
        },
        {"type": "section", "text": {"type": "mrkdwn", "text": f"*Razonamiento:*\n{log_text}"}},
    ]


def post_handoff(
    brand: dict[str, Any],
    classification: dict[str, Any],
    reply_text: str,
    reasoning_log: list[str] | None = None,
    *,
    webhook_url: str | None = None,
    dry_run: bool = True,
) -> dict[str, Any]:
    blocks = build_handoff_blocks(brand, classification, reply_text, reasoning_log)
    payload = {"text": "Lead calificado - Addi Marketplace", "blocks": blocks}
    if dry_run:
        return {"dry_run": True, "payload": payload}
    url = webhook_url or os.environ.get("SLACK_WEBHOOK_URL")
    if not url:
        raise RuntimeError("SLACK_WEBHOOK_URL is required for live Slack handoff")
    response = requests.post(url, json=payload, timeout=15)
    response.raise_for_status()
    return {"sent": True, "status_code": response.status_code}

