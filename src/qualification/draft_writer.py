"""Draft outreach copy for human review only.

This module intentionally does not import email, WhatsApp, or any live outreach
service. It can only draft text.
"""

from __future__ import annotations

import json
import os
from typing import Any

import requests


def draft_outreach_email(
    company_fields: dict[str, Any],
    company_profile: str,
    *,
    api_key: str | None = None,
    model: str = "llama-3.3-70b-versatile",
    timeout: int = 30,
) -> str:
    key = api_key or os.environ.get("GROQ_API_KEY")
    if not key:
        raise RuntimeError("GROQ_API_KEY is required")

    context = {
        "company": company_fields,
        "profile": company_profile,
        "addi_context": (
            "Addi Marketplace busca marcas en categorias con oportunidad para llevar demanda "
            "BNPL existente hacia Marketplace. Tono: directo, consultivo, breve, sin prometer resultados."
        ),
    }
    response = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        json={
            "model": model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "Redacta un borrador de email comercial en espanol para revision humana. "
                        "No incluyas placeholders de envio automatico. No afirmes datos no presentes."
                    ),
                },
                {"role": "user", "content": json.dumps(context, ensure_ascii=False, indent=2)},
            ],
            "temperature": 0.35,
            "max_tokens": 420,
        },
        timeout=timeout,
    )
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"].strip()
