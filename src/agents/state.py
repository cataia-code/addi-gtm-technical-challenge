"""Shared state for the GTM graph."""

from __future__ import annotations

from typing import Any, TypedDict


class GTMState(TypedDict, total=False):
    brand_actual: dict[str, Any]
    tier: str
    ya_contactado: bool
    reply_recibido: str | None
    clasificacion: dict[str, Any] | None
    decision: str
    log_razonamiento: list[str]
    dry_run: bool
    email_destino: str | None
    whatsapp_destino: str | None


def append_log(state: GTMState, message: str) -> GTMState:
    log = list(state.get("log_razonamiento", []))
    log.append(message)
    state["log_razonamiento"] = log
    return state

