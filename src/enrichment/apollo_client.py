"""Apollo enrichment client.

This module is intentionally read-only: it can search and draft, but it does
not send outreach. Human approval belongs in the outreach layer.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

import requests


@dataclass(frozen=True)
class Prospect:
    name: str | None
    title: str | None
    email: str | None
    phone: str | None
    organization: str | None
    source: str = "apollo"


def search_people(
    *,
    organization_domains: list[str] | None = None,
    titles: list[str] | None = None,
    per_page: int = 5,
    api_key: str | None = None,
) -> list[Prospect]:
    key = api_key or os.environ.get("APOLLO_API_KEY")
    if not key:
        raise RuntimeError("APOLLO_API_KEY is required for Apollo enrichment")

    payload: dict[str, Any] = {"page": 1, "per_page": per_page}
    if organization_domains:
        payload["q_organization_domains"] = organization_domains
    if titles:
        payload["person_titles"] = titles

    response = requests.post(
        "https://api.apollo.io/v1/mixed_people/search",
        headers={"Cache-Control": "no-cache", "Content-Type": "application/json", "X-Api-Key": key},
        json=payload,
        timeout=25,
    )
    response.raise_for_status()
    people = response.json().get("people", [])
    return [
        Prospect(
            name=person.get("name"),
            title=person.get("title"),
            email=person.get("email"),
            phone=person.get("phone_numbers", [{}])[0].get("raw_number")
            if person.get("phone_numbers")
            else None,
            organization=(person.get("organization") or {}).get("name"),
        )
        for person in people
    ]


def draft_message(brand_context: dict[str, Any], prospect: Prospect) -> str:
    organization = prospect.organization or brand_context.get("brand_id", "tu compania")
    category = brand_context.get("category", "tu categoria")
    gmv = brand_context.get("gmv_cop_millions_12m", "N/A")
    return (
        f"Hola {prospect.name or ''},\n\n"
        f"Estoy revisando oportunidades para marcas de {category} que ya tienen traccion "
        f"con Addi BNPL. {organization} aparece como una cuenta interesante por su volumen "
        f"historico aproximado de COP {gmv} MM.\n\n"
        "Antes de enviar cualquier propuesta comercial, queria validar si tu eres la persona "
        "correcta para conversar sobre Marketplace o si deberia hablar con alguien del equipo "
        "de ecommerce/alianzas.\n\n"
        "Saludos,\nEquipo GTM Addi Marketplace"
    )

