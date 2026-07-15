"""Shared state for the LangGraph GTM agent."""

from __future__ import annotations

from typing import Any, TypedDict


class GTMState(TypedDict, total=False):
    brand_data: dict[str, Any]
    tier: str
    ya_contactado: bool
    reply_recibido: str | None
    clasificacion: dict[str, Any] | None
    decision: str
    log_razonamiento: list[str]
    dry_run: bool
    whatsapp_result: dict[str, Any] | None


def append_log(state: GTMState, message: str) -> GTMState:
    state["log_razonamiento"] = [*state.get("log_razonamiento", []), message]
    return state
