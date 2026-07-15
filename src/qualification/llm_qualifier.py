"""Groq-backed reply classifier with strict action normalization."""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import requests


LOGGER = logging.getLogger(__name__)
ALLOWED_ACTIONS = {"agendar", "nurture", "descartar"}
PROMPT_PATH = Path(__file__).resolve().parent / "qualifier_prompt.md"


@dataclass(frozen=True)
class Qualification:
    intent_score: int
    is_decision_maker: bool
    objection_type: str | None
    suggested_action: str
    reasoning: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "intent_score": self.intent_score,
            "is_decision_maker": self.is_decision_maker,
            "objection_type": self.objection_type,
            "suggested_action": self.suggested_action,
            "reasoning": self.reasoning,
        }


def load_prompt(prompt_path: Path = PROMPT_PATH) -> str:
    return prompt_path.read_text(encoding="utf-8")


def normalize_action(raw_action: str | None, intent_score: int) -> str:
    if raw_action:
        action = raw_action.strip().lower()
        if action in ALLOWED_ACTIONS:
            return action
    if intent_score >= 70:
        return "agendar"
    if intent_score >= 40:
        return "nurture"
    return "descartar"


def parse_qualification(raw_json: str) -> Qualification:
    clean = raw_json.replace("```json", "").replace("```", "").strip()
    try:
        payload = json.loads(clean)
    except json.JSONDecodeError:
        LOGGER.exception("Groq response was not valid JSON. raw=%r", raw_json)
        raise

    intent_score = int(max(0, min(100, payload.get("intent_score", 0))))
    action = normalize_action(payload.get("suggested_action"), intent_score)
    return Qualification(
        intent_score=intent_score,
        is_decision_maker=bool(payload.get("is_decision_maker", False)),
        objection_type=payload.get("objection_type"),
        suggested_action=action,
        reasoning=str(payload.get("reasoning", ""))[:500],
    )


def classify_reply(
    reply_text: str,
    merchant_context: dict[str, Any] | None = None,
    *,
    api_key: str | None = None,
    model: str = "llama-3.3-70b-versatile",
    timeout: int = 20,
) -> Qualification:
    key = api_key or os.environ.get("GROQ_API_KEY")
    if not key:
        raise RuntimeError("GROQ_API_KEY is required for live classification")

    context = json.dumps(merchant_context or {}, ensure_ascii=False)
    response = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        json={
            "model": model,
            "messages": [
                {"role": "system", "content": load_prompt()},
                {"role": "user", "content": f"Contexto:\n{context}\n\nReply recibido:\n{reply_text}"},
            ],
            "temperature": 0,
            "max_tokens": 250,
        },
        timeout=timeout,
    )
    response.raise_for_status()
    raw = response.json()["choices"][0]["message"]["content"]
    return parse_qualification(raw)

