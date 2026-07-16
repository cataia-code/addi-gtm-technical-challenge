"""Shared state for the Test 2 prospecting graph."""

from __future__ import annotations

from typing import Any, TypedDict


class ProspectingState(TypedDict, total=False):
    run_input: dict[str, Any]
    max_results: int
    raw_prospects: list[Any]
    valid_prospects: list[dict[str, Any]]
    new_prospects: list[dict[str, Any]]
    enriched_rows: list[dict[str, Any]]
    output_path: str
    log: list[str]


def append_log(state: ProspectingState, message: str) -> ProspectingState:
    state["log"] = [*state.get("log", []), message]
    return state
