"""Groq-backed reply classifier with strict action normalization."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any

import requests


ALLOWED_ACTIONS = {"agendar", "nurture", "descartar"}


QUALIFIER_PROMPT = """Eres el clasificador de leads de Addi Marketplace.
Responde SOLO JSON puro con este schema:
{
  "intent_score": <0-100>,
  "is_decision_maker": <true|false>,
  "objection_type": <"precio"|"integracion"|"tiempo"|"competidor"|null>,
  "suggested_action": <"agendar"|"nurture"|"descartar">,
  "reasoning": "<una frase corta>"
}

Reglas:
- 70-100: interes claro, suggested_action="agendar"
- 40-69: interes parcial u objecion, suggested_action="nurture"
- 0-39: rechazo u opt-out, suggested_action="descartar"
- Si el merchant pide no ser contactado, suggested_action="descartar"
"""


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
    payload = json.loads(clean)
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
                {"role": "system", "content": QUALIFIER_PROMPT},
                {"role": "user", "content": f"Contexto: {context}\nReply: {reply_text}"},
            ],
            "temperature": 0,
            "max_tokens": 250,
        },
        timeout=timeout,
    )
    response.raise_for_status()
    raw = response.json()["choices"][0]["message"]["content"]
    return parse_qualification(raw)

