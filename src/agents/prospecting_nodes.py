"""LangGraph nodes for read-only Apify prospecting."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from src.db import repository
from src.enrichment.apify_apollo_scraper import run_apollo_organizations_scraper
from src.enrichment.llm_research import synthesize_company_profile
from src.qualification.draft_writer import draft_outreach_email

from .prospecting_state import ProspectingState, append_log


ROOT = Path(__file__).resolve().parents[2]
REQUIRED_FIELDS = [
    "name",
    "domain",
    "industry",
    "country",
    "city",
    "contact_name",
    "contact_title",
    "contact_email",
    "contact_phone",
    "linkedin_url",
]


def nodo_apify_buscar_leads(state: ProspectingState) -> ProspectingState:
    prospects = run_apollo_organizations_scraper(
        state["run_input"],
        max_results=int(state.get("max_results", 3)),
    )
    state["raw_prospects"] = prospects
    append_log(state, f"nodo_apify_buscar_leads: {len(prospects)} leads recibidos desde Apify.")
    return state


def nodo_validar_campos_completos(state: ProspectingState) -> ProspectingState:
    valid = []
    for prospect in state.get("raw_prospects", []):
        payload = prospect.as_llm_context() if hasattr(prospect, "as_llm_context") else dict(prospect)
        missing = [field for field in REQUIRED_FIELDS if not payload.get(field)]
        if missing:
            append_log(state, f"nodo_validar_campos_completos: descartado {payload.get('name')} faltan={missing}.")
            continue
        valid.append(payload)
    state["valid_prospects"] = valid
    append_log(state, f"nodo_validar_campos_completos: {len(valid)} leads con campos completos.")
    return state


def nodo_filtrar_duplicados_db(state: ProspectingState) -> ProspectingState:
    new_prospects = []
    for prospect in state.get("valid_prospects", []):
        exists = repository.prospect_exists(
            contact_email=prospect.get("contact_email"),
            contact_phone=prospect.get("contact_phone"),
            linkedin_url=prospect.get("linkedin_url"),
        )
        if exists:
            append_log(state, f"nodo_filtrar_duplicados_db: duplicado omitido {prospect.get('contact_email')}.")
            continue
        new_prospects.append(prospect)
    state["new_prospects"] = new_prospects
    append_log(state, f"nodo_filtrar_duplicados_db: {len(new_prospects)} leads nuevos.")
    return state


def nodo_investigar_y_redactar(state: ProspectingState) -> ProspectingState:
    rows: list[dict[str, Any]] = []
    for prospect in state.get("new_prospects", []):
        profile = synthesize_company_profile(prospect)
        draft = draft_outreach_email(prospect, profile)
        rows.append({**prospect, "profile": profile, "draft_email": draft})
    state["enriched_rows"] = rows
    append_log(state, f"nodo_investigar_y_redactar: {len(rows)} perfiles y borradores creados.")
    return state


def nodo_exportar_excel_y_registrar_db(state: ProspectingState) -> ProspectingState:
    output_path = ROOT / "data" / "test2_prospectos_apify.xlsx"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    rows = state.get("enriched_rows", [])
    pd.DataFrame(rows).to_excel(output_path, index=False)
    for row in rows:
        repository.save_prospect_consultation(row)
    state["output_path"] = str(output_path)
    append_log(state, f"nodo_exportar_excel_y_registrar_db: Excel guardado en {output_path}.")
    append_log(state, f"nodo_exportar_excel_y_registrar_db: {len(rows)} leads registrados en SQLite.")
    return state
