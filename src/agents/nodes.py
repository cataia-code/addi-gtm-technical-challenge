"""Nodes for the Hunter + SDR GTM flow."""

from __future__ import annotations

from typing import Any

from src.db import repository
from src.handoff.slack_service import post_handoff
from src.outreach.email_service import send_email_d0
from src.outreach.whatsapp_service import send_whatsapp
from src.qualification.llm_qualifier import classify_reply

from .state import GTMState, append_log


def brief_hunter(state: GTMState) -> GTMState:
    brand = state["brand_actual"]
    append_log(
        state,
        "Tier A: se genera brief para Hunter Sr; no se ejecuta outreach automatico.",
    )
    classification = {
        "intent_score": None,
        "suggested_action": "brief_hunter",
        "reasoning": "Cuenta Tier A requiere criterio comercial alto-touch.",
    }
    post_handoff(
        brand,
        classification,
        "Brief proactivo sin reply: revisar antes de contactar.",
        state.get("log_razonamiento", []),
        dry_run=state.get("dry_run", True),
    )
    state["decision"] = "brief_hunter"
    return state


def chequeo_duplicado(state: GTMState) -> GTMState:
    brand_id = state["brand_actual"]["brand_id"]
    if state.get("dry_run", True):
        state["ya_contactado"] = False
        append_log(state, "Dry-run: duplicate check simulado sin escribir contact_log.")
        return state
    contacted = repository.was_contacted_recently(brand_id)
    state["ya_contactado"] = contacted
    if contacted:
        state["decision"] = "duplicado"
        append_log(state, "Ya contactado en los ultimos 14 dias; se evita duplicado.")
    else:
        repository.mark_contacted(brand_id, "email")
        append_log(state, "Sin contacto reciente; se registra contacto por email.")
    return state


def agente_sdr_outreach(state: GTMState) -> GTMState:
    if state.get("ya_contactado"):
        return state
    brand = state["brand_actual"]
    to_email = state.get("email_destino")
    if not to_email:
        append_log(state, "Sin email destino; se omite envio D0.")
        return state
    send_email_d0(
        brand,
        to_email,
        reply_to=to_email,
        dry_run=state.get("dry_run", True),
    )
    append_log(state, f"Email D0 preparado para {to_email} usando GMV, categoria y score.")
    return state


def agente_sdr_clasificacion(state: GTMState) -> GTMState:
    reply = state.get("reply_recibido")
    if not reply:
        append_log(state, "Sin reply recibido; queda pendiente de listener.")
        state["decision"] = "pendiente_reply"
        return state
    if _is_opt_out(reply):
        classification = {
            "intent_score": 0,
            "is_decision_maker": False,
            "objection_type": None,
            "suggested_action": "descartar",
            "reasoning": "Opt-out explicito detectado antes del LLM.",
        }
    else:
        if state.get("dry_run", True):
            classification = _classify_reply_stub(reply)
        else:
            qualification = classify_reply(reply, state["brand_actual"])
            classification = qualification.as_dict()
    state["clasificacion"] = classification
    state["decision"] = classification["suggested_action"]
    if not state.get("dry_run", True):
        repository.save_reply(state["brand_actual"]["brand_id"], reply, classification)
    append_log(state, f"Reply clasificado como {state['decision']}: {classification['reasoning']}")
    return state


def handoff_hunter(state: GTMState) -> GTMState:
    brand = state["brand_actual"]
    classification = state["clasificacion"] or {}
    has_opt_in = repository.has_opt_in(brand["brand_id"], "whatsapp")
    if state.get("whatsapp_destino"):
        wa_result = send_whatsapp(
            state["whatsapp_destino"],
            "Gracias por tu respuesta. Un especialista de Addi Marketplace te contactara para coordinar la llamada.",
            has_opt_in=has_opt_in,
            dry_run=state.get("dry_run", True),
        )
        append_log(state, f"WhatsApp gate result: {wa_result.reason}.")
    post_handoff(
        brand,
        classification,
        state.get("reply_recibido") or "",
        state.get("log_razonamiento", []),
        dry_run=state.get("dry_run", True),
    )
    append_log(state, "Handoff enviado/preparado para Hunter.")
    return state


def handoff_nurture(state: GTMState) -> GTMState:
    append_log(state, "Lead queda en nurture; no se envia WhatsApp.")
    post_handoff(
        state["brand_actual"],
        state["clasificacion"] or {},
        state.get("reply_recibido") or "",
        state.get("log_razonamiento", []),
        dry_run=state.get("dry_run", True),
    )
    return state


def handoff_descarte(state: GTMState) -> GTMState:
    append_log(state, "Lead descartado u opt-out; WhatsApp bloqueado por compliance.")
    post_handoff(
        state["brand_actual"],
        state["clasificacion"] or {},
        state.get("reply_recibido") or "",
        state.get("log_razonamiento", []),
        dry_run=state.get("dry_run", True),
    )
    return state


def route_after_tier(state: GTMState) -> str:
    return "brief_hunter" if state.get("tier") == "A" else "chequeo_duplicado"


def route_after_duplicate(state: GTMState) -> str:
    return "end" if state.get("ya_contactado") else "agente_sdr_outreach"


def route_after_classification(state: GTMState) -> str:
    decision = state.get("decision")
    if decision == "agendar":
        return "handoff_hunter"
    if decision == "nurture":
        return "handoff_nurture"
    if decision == "descartar":
        return "handoff_descarte"
    return "end"


def _is_opt_out(reply: str) -> bool:
    normalized = reply.lower()
    tokens = ["no me escrib", "no contactar", "no me vuelvan", "unsubscribe", "opt-out"]
    return any(token in normalized for token in tokens)


def _classify_reply_stub(reply: str) -> dict[str, Any]:
    normalized = reply.lower()
    if any(token in normalized for token in ["interesa", "agendar", "llamada", "reunion", "reunión"]):
        return {
            "intent_score": 85,
            "is_decision_maker": True,
            "objection_type": None,
            "suggested_action": "agendar",
            "reasoning": "Dry-run: reply expresa interes claro y disponibilidad.",
        }
    if any(token in normalized for token in ["caro", "comision", "precio", "despues", "después"]):
        return {
            "intent_score": 55,
            "is_decision_maker": False,
            "objection_type": "precio",
            "suggested_action": "nurture",
            "reasoning": "Dry-run: reply muestra objecion antes de agendar.",
        }
    return {
        "intent_score": 25,
        "is_decision_maker": False,
        "objection_type": None,
        "suggested_action": "descartar",
        "reasoning": "Dry-run: no hay senal suficiente de interes.",
    }
