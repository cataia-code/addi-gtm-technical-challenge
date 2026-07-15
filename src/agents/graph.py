"""LangGraph assembly with a local fallback runner."""

from __future__ import annotations

from .nodes import (
    agente_sdr_clasificacion,
    agente_sdr_outreach,
    brief_hunter,
    chequeo_duplicado,
    handoff_descarte,
    handoff_hunter,
    handoff_nurture,
    route_after_classification,
    route_after_duplicate,
    route_after_tier,
)
from .state import GTMState


def build_graph():
    try:
        from langgraph.graph import END, StateGraph
    except ImportError:
        return None

    graph = StateGraph(GTMState)
    graph.add_node("brief_hunter", brief_hunter)
    graph.add_node("chequeo_duplicado", chequeo_duplicado)
    graph.add_node("agente_sdr_outreach", agente_sdr_outreach)
    graph.add_node("agente_sdr_clasificacion", agente_sdr_clasificacion)
    graph.add_node("handoff_hunter", handoff_hunter)
    graph.add_node("handoff_nurture", handoff_nurture)
    graph.add_node("handoff_descarte", handoff_descarte)

    graph.set_conditional_entry_point(
        route_after_tier,
        {"brief_hunter": "brief_hunter", "chequeo_duplicado": "chequeo_duplicado"},
    )
    graph.add_conditional_edges(
        "chequeo_duplicado",
        route_after_duplicate,
        {"agente_sdr_outreach": "agente_sdr_outreach", "end": END},
    )
    graph.add_edge("agente_sdr_outreach", "agente_sdr_clasificacion")
    graph.add_conditional_edges(
        "agente_sdr_clasificacion",
        route_after_classification,
        {
            "handoff_hunter": "handoff_hunter",
            "handoff_nurture": "handoff_nurture",
            "handoff_descarte": "handoff_descarte",
            "end": END,
        },
    )
    graph.add_edge("brief_hunter", END)
    graph.add_edge("handoff_hunter", END)
    graph.add_edge("handoff_nurture", END)
    graph.add_edge("handoff_descarte", END)
    return graph.compile()


def run_local(state: GTMState) -> GTMState:
    if route_after_tier(state) == "brief_hunter":
        return brief_hunter(state)
    chequeo_duplicado(state)
    if route_after_duplicate(state) == "end":
        return state
    agente_sdr_outreach(state)
    agente_sdr_clasificacion(state)
    next_node = route_after_classification(state)
    if next_node == "handoff_hunter":
        return handoff_hunter(state)
    if next_node == "handoff_nurture":
        return handoff_nurture(state)
    if next_node == "handoff_descarte":
        return handoff_descarte(state)
    return state

