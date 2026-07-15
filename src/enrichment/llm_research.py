"""LLM synthesis over Apify-provided company fields only."""

from __future__ import annotations

import json
import os
from typing import Any

import requests


def synthesize_company_profile(
    company_fields: dict[str, Any],
    *,
    api_key: str | None = None,
    model: str = "llama-3.3-70b-versatile",
    timeout: int = 30,
) -> str:
    key = api_key or os.environ.get("GROQ_API_KEY")
    if not key:
        raise RuntimeError("GROQ_API_KEY is required")

    response = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        json={
            "model": model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "Eres analista GTM. Sintetiza un perfil de empresa en 3-4 lineas. "
                        "Usa SOLO los campos JSON entregados. No inventes datos, no uses web."
                    ),
                },
                {"role": "user", "content": json.dumps(company_fields, ensure_ascii=False, indent=2)},
            ],
            "temperature": 0.2,
            "max_tokens": 220,
        },
        timeout=timeout,
    )
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"].strip()
