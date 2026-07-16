"""LangGraph assembly for Test 2 Apify prospecting."""

from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from .prospecting_nodes import (
    nodo_apify_buscar_leads,
    nodo_exportar_excel_y_registrar_db,
    nodo_filtrar_duplicados_db,
    nodo_investigar_y_redactar,
    nodo_validar_campos_completos,
)
from .prospecting_state import ProspectingState


def build_prospecting_graph():
    graph = StateGraph(ProspectingState)
    graph.add_node("nodo_apify_buscar_leads", nodo_apify_buscar_leads)
    graph.add_node("nodo_validar_campos_completos", nodo_validar_campos_completos)
    graph.add_node("nodo_filtrar_duplicados_db", nodo_filtrar_duplicados_db)
    graph.add_node("nodo_investigar_y_redactar", nodo_investigar_y_redactar)
    graph.add_node("nodo_exportar_excel_y_registrar_db", nodo_exportar_excel_y_registrar_db)

    graph.add_edge(START, "nodo_apify_buscar_leads")
    graph.add_edge("nodo_apify_buscar_leads", "nodo_validar_campos_completos")
    graph.add_edge("nodo_validar_campos_completos", "nodo_filtrar_duplicados_db")
    graph.add_edge("nodo_filtrar_duplicados_db", "nodo_investigar_y_redactar")
    graph.add_edge("nodo_investigar_y_redactar", "nodo_exportar_excel_y_registrar_db")
    graph.add_edge("nodo_exportar_excel_y_registrar_db", END)
    return graph.compile()


compiled_prospecting_graph = build_prospecting_graph()
