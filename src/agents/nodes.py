"""LangGraph nodes for the Hunter + SDR GTM motion."""

from __future__ import annotations

import os
from datetime import datetime

from src.db import repository
from src.handoff.slack_service import post_handoff
from src.outreach.email_service import send_email_d0
from src.outreach.whatsapp_service import send_whatsapp
from src.qualification.llm_qualifier import classify_reply

from .state import GTMState, append_log


def nodo_brief_hunter(state: GTMState) -> GTMState:
    brand = state["brand_data"]
    brief = (
        f"Brief Hunter Sr: {brand.get('brand_id')} | {brand.get('category')} | "
        f"GMV COP {brand.get('gmv_cop_millions_12m')} MM | {brand.get('why', '')}"
    )
    classification = {
        "intent_score": None,
        "suggested_action": "brief_hunter",
        "reasoning": "Tier A: cuenta de alto valor, requiere revisión manual antes de contactar.",
    }
    post_handoff(brand, classification, brief, state["log_razonamiento"])
    repository.save_agent_interaction(
        run_id=brand.get("brand_id", "tier_a"),
        source="langgraph",
        event_type="brief_hunter",
        brand_id=brand.get("brand_id"),
        content=brief,
        metadata={"classification": classification, "log": state["log_razonamiento"]},
    )
    state["decision"] = "brief_hunter"
    append_log(state, "nodo_brief_hunter: Tier A detectado; brief enviado/preparado en Slack.")
    append_log(state, "nodo_brief_hunter: no hay outreach automático para Tier A.")
    return state


def nodo_chequeo_duplicado(state: GTMState) -> GTMState:
    brand_id = state["brand_data"]["brand_id"]
    state["ya_contactado"] = repository.was_contacted_recently(brand_id)
    if state["ya_contactado"]:
        state["decision"] = "duplicado"
        append_log(state, "nodo_chequeo_duplicado: ya contactado, evitando duplicado.")
    else:
        append_log(state, "nodo_chequeo_duplicado: sin contacto reciente; continúa outreach.")
    return state


def nodo_enviar_email(state: GTMState) -> GTMState:
    brand = state["brand_data"]
    to_email = brand.get("contacto_email") or os.environ.get("DEMO_EMAIL_DESTINO") or "demo@example.com"
    result = send_email_d0(brand, to_email, reply_to=to_email)
    thread_id = result.get("id") or result.get("threadId") or result.get("subject")
    repository.upsert_lead(
        brand["brand_id"],
        category=brand.get("category"),
        gmv_cop_millions_12m=brand.get("gmv_cop_millions_12m"),
        tier=brand.get("tier"),
        contacto_email=to_email,
        thread_id=str(thread_id) if thread_id else None,
    )
    repository.mark_contacted(brand["brand_id"], thread_id=str(thread_id) if thread_id else None)
    repository.save_agent_interaction(
        run_id=brand["brand_id"],
        source="langgraph",
        event_type="email_d0_enviado",
        brand_id=brand["brand_id"],
        content=f"Email D0 a {to_email}",
        metadata={"thread_id": str(thread_id) if thread_id else None, "brand": brand},
    )
    append_log(state, f"nodo_enviar_email: email D0 preparado/enviado a {to_email}; contactado_en marcado en SQLite.")
    return state


def nodo_clasificar_reply(state: GTMState) -> GTMState:
    reply = state.get("reply_recibido")
    if not reply:
        state["decision"] = "pendiente_reply"
        append_log(state, "nodo_clasificar_reply: no hay reply; queda pendiente de listener.")
        return state

    if _is_opt_out(reply):
        classification = {
            "intent_score": 0,
            "is_decision_maker": False,
            "objection_type": None,
            "suggested_action": "descartar",
            "reasoning": "Opt-out explícito detectado antes de cualquier acción adicional.",
            "es_opt_out": True,
        }
    else:
        qualification = classify_reply(reply, state["brand_data"])
        classification = qualification.as_dict()
        classification["es_opt_out"] = False

    state["clasificacion"] = classification
    state["decision"] = classification["suggested_action"]
    repository.save_reply(state["brand_data"]["brand_id"], reply, classification)
    repository.save_agent_interaction(
        run_id=state["brand_data"]["brand_id"],
        source="langgraph",
        event_type="reply_clasificado",
        brand_id=state["brand_data"]["brand_id"],
        content=reply,
        metadata=classification,
    )
    append_log(
        state,
        f"nodo_clasificar_reply: suggested_action={state['decision']} | {classification.get('reasoning', '')}",
    )
    return state


def nodo_router(state: GTMState) -> GTMState:
    classification = state.get("clasificacion") or {}
    state["decision"] = str(classification.get("suggested_action") or state.get("decision") or "pendiente_reply")
    append_log(state, f"nodo_router: próxima rama={state['decision']}.")
    return state


def nodo_handoff_agendar(state: GTMState) -> GTMState:
    whatsapp_result = state.get("whatsapp_result") or {}
    post_handoff(
        state["brand_data"],
        state["clasificacion"] or {},
        state.get("reply_recibido") or "",
        state["log_razonamiento"],
        dry_run=_is_dry_run(state),
        action_taken=(
            f"WhatsApp {whatsapp_result.get('status', 'pendiente')} + handoff Slack"
            if whatsapp_result
            else "Handoff Slack agendar"
        ),
        timestamp=datetime.now().isoformat(timespec="seconds"),
    )
    append_log(state, "nodo_handoff_agendar: handoff Hunter preparado en Slack; SLA sugerido <24h.")
    repository.save_agent_interaction(
        run_id=state["brand_data"]["brand_id"],
        source="langgraph",
        event_type="handoff_agendar",
        brand_id=state["brand_data"]["brand_id"],
        content=state.get("reply_recibido") or "",
        metadata={"classification": state.get("clasificacion"), "whatsapp_result": state.get("whatsapp_result")},
    )
    return state


def nodo_handoff_nurture(state: GTMState) -> GTMState:
    post_handoff(
        state["brand_data"],
        state["clasificacion"] or {},
        state.get("reply_recibido") or "",
        state["log_razonamiento"],
        dry_run=_is_dry_run(state),
        action_taken="Nurture: Slack sin WhatsApp",
        timestamp=datetime.now().isoformat(timespec="seconds"),
    )
    append_log(state, "nodo_handoff_nurture: lead queda en nurture; no se genera WhatsApp.")
    repository.save_agent_interaction(
        run_id=state["brand_data"]["brand_id"],
        source="langgraph",
        event_type="handoff_nurture",
        brand_id=state["brand_data"]["brand_id"],
        content=state.get("reply_recibido") or "",
        metadata={"classification": state.get("clasificacion")},
    )
    return state


def nodo_handoff_descarte(state: GTMState) -> GTMState:
    classification = state.get("clasificacion") or {}
    is_opt_out = bool(classification.get("es_opt_out"))
    # GATE DE COMPLIANCE: si hay opt-out o suggested_action == descartar,
    # esta rama bloquea cualquier generación/envío de WhatsApp.
    if is_opt_out or classification.get("suggested_action") == "descartar":
        append_log(state, "nodo_handoff_descarte: GATE activo; WhatsApp bloqueado por opt-out/descarte.")
    post_handoff(
        state["brand_data"],
        classification,
        state.get("reply_recibido") or "",
        state["log_razonamiento"],
        dry_run=_is_dry_run(state),
        action_taken="Descarte/opt-out: WhatsApp bloqueado",
        timestamp=datetime.now().isoformat(timespec="seconds"),
    )
    append_log(state, "nodo_handoff_descarte: descarte documentado en Slack.")
    repository.save_agent_interaction(
        run_id=state["brand_data"]["brand_id"],
        source="langgraph",
        event_type="handoff_descarte",
        brand_id=state["brand_data"]["brand_id"],
        content=state.get("reply_recibido") or "",
        metadata={"classification": classification},
    )
    return state


def route_by_tier(state: GTMState) -> str:
    return "nodo_brief_hunter" if state["tier"] == "A" else "nodo_chequeo_duplicado"


def route_after_duplicate(state: GTMState) -> str:
    return "__end__" if state["ya_contactado"] else "nodo_enviar_email"


def route_after_router(state: GTMState) -> str:
    decision = state.get("decision")
    if decision == "agendar":
        return "nodo_handoff_agendar"
    if decision == "nurture":
        return "nodo_handoff_nurture"
    if decision == "descartar":
        return "nodo_handoff_descarte"
    return "__end__"


def nodo_enviar_whatsapp_agendar(state: GTMState) -> GTMState:
    classification = state.get("clasificacion") or {}
    brand = state["brand_data"]
    if classification.get("suggested_action") != "agendar":
        append_log(state, "nodo_enviar_whatsapp_agendar: no es agendar; WhatsApp omitido.")
        return state
    if bool(classification.get("es_opt_out")):
        append_log(state, "nodo_enviar_whatsapp_agendar: opt-out detectado; WhatsApp bloqueado.")
        state["whatsapp_result"] = {"sent": False, "status": "blocked_opt_out"}
        return state

    has_opt_in = repository.has_opt_in(brand["brand_id"], "whatsapp")
    if not has_opt_in:
        append_log(state, "nodo_enviar_whatsapp_agendar: sin opt_in; WhatsApp bloqueado.")
        state["whatsapp_result"] = {"sent": False, "status": "blocked_no_opt_in"}
        return state

    body = (
        "Hola, gracias por tu respuesta. Soy del equipo Addi Marketplace. "
        "Recibimos tu interes y un especialista te contactara para coordinar "
        "una llamada de 20 minutos."
    )
    result = send_whatsapp(
        brand["contacto_whatsapp"],
        body,
        has_opt_in=has_opt_in,
        dry_run=_is_dry_run(state),
    )
    provider = result.provider_response or {}
    state["whatsapp_result"] = {
        "sent": result.sent,
        "status": provider.get("status") or result.reason,
        "sid": provider.get("sid"),
        "error_code": provider.get("error_code"),
    }
    append_log(
        state,
        f"nodo_enviar_whatsapp_agendar: WhatsApp status={state['whatsapp_result']['status']} sid={state['whatsapp_result'].get('sid')}",
    )
    repository.save_agent_interaction(
        run_id=brand["brand_id"],
        source="langgraph",
        event_type="whatsapp_agendar",
        brand_id=brand["brand_id"],
        content=body,
        metadata=state["whatsapp_result"],
    )
    return state


def _is_dry_run(state: GTMState) -> bool:
    return bool(state.get("dry_run", True))


def _is_opt_out(reply: str) -> bool:
    normalized = reply.lower()
    tokens = ["no me escrib", "no contactar", "no me vuelvan", "unsubscribe", "opt-out"]
    return any(token in normalized for token in tokens)
