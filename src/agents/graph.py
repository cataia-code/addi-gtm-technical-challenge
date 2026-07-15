"""LangGraph assembly for the GTM agent."""

from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from .nodes import (
    nodo_brief_hunter,
    nodo_chequeo_duplicado,
    nodo_clasificar_reply,
    nodo_enviar_email,
    nodo_handoff_agendar,
    nodo_handoff_descarte,
    nodo_handoff_nurture,
    nodo_router,
    route_after_duplicate,
    route_after_router,
    route_by_tier,
)
from .state import GTMState


def build_graph():
    graph = StateGraph(GTMState)
    graph.add_node("nodo_brief_hunter", nodo_brief_hunter)
    graph.add_node("nodo_chequeo_duplicado", nodo_chequeo_duplicado)
    graph.add_node("nodo_enviar_email", nodo_enviar_email)
    graph.add_node("nodo_clasificar_reply", nodo_clasificar_reply)
    graph.add_node("nodo_router", nodo_router)
    graph.add_node("nodo_handoff_agendar", nodo_handoff_agendar)
    graph.add_node("nodo_handoff_nurture", nodo_handoff_nurture)
    graph.add_node("nodo_handoff_descarte", nodo_handoff_descarte)

    graph.add_conditional_edges(
        START,
        route_by_tier,
        {
            "nodo_brief_hunter": "nodo_brief_hunter",
            "nodo_chequeo_duplicado": "nodo_chequeo_duplicado",
        },
    )
    graph.add_edge("nodo_brief_hunter", END)
    graph.add_conditional_edges(
        "nodo_chequeo_duplicado",
        route_after_duplicate,
        {"nodo_enviar_email": "nodo_enviar_email", "__end__": END},
    )
    graph.add_edge("nodo_enviar_email", "nodo_clasificar_reply")
    graph.add_edge("nodo_clasificar_reply", "nodo_router")
    graph.add_conditional_edges(
        "nodo_router",
        route_after_router,
        {
            "nodo_handoff_agendar": "nodo_handoff_agendar",
            "nodo_handoff_nurture": "nodo_handoff_nurture",
            "nodo_handoff_descarte": "nodo_handoff_descarte",
            "__end__": END,
        },
    )
    graph.add_edge("nodo_handoff_agendar", END)
    graph.add_edge("nodo_handoff_nurture", END)
    graph.add_edge("nodo_handoff_descarte", END)
    return graph.compile()


compiled_graph = build_graph()

