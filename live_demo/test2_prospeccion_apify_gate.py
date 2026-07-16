"""Test 2: Apify prospecting through LangGraph, saved to Excel only.

This script must never send Slack, email, or WhatsApp messages.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.agents.prospecting_graph import compiled_prospecting_graph
from src.enrichment.apify_apollo_scraper import hogar_colombia_input


REPORT_PATH = ROOT / "tests" / "test2_prospeccion_apify_gate.md"


def main() -> None:
    load_env()
    parser = argparse.ArgumentParser()
    parser.add_argument("--confirm-run", action="store_true", help="Actually call Apify and Groq.")
    parser.add_argument("--max-results", type=int, default=3)
    args = parser.parse_args()

    run_input = hogar_colombia_input()
    print("INPUT_APIFY_CONFIRMAR_ANTES_DE_EJECUTAR:")
    print(json.dumps(run_input, ensure_ascii=False, indent=2))
    if not args.confirm_run:
        print("No se ejecuto Apify. Reejecuta con --confirm-run para gastar UNA llamada real.")
        return

    require_env("APIFY_API_TOKEN", "GROQ_API_KEY")
    reset_report(run_input)
    state = compiled_prospecting_graph.invoke(
        {
            "run_input": run_input,
            "max_results": args.max_results,
            "log": [],
        }
    )
    for message in state.get("log", []):
        log_step(message)
    log_step(f"Excel generado: {state.get('output_path')}")
    log_step(f"Leads exportados: {len(state.get('enriched_rows', []))}")


def load_env() -> None:
    env_path = ROOT / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8-sig").splitlines():
        if not line or line.strip().startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


def require_env(*keys: str) -> None:
    missing = [key for key in keys if not os.environ.get(key)]
    if missing:
        raise RuntimeError(f"Missing required env vars: {', '.join(missing)}")


def reset_report(run_input: dict) -> None:
    REPORT_PATH.write_text(
        "# Test 2: prospeccion real LangGraph a Excel\n\n"
        "No se envia Slack, email ni WhatsApp. Los leads se validan, deduplican contra SQLite y se guardan en Excel.\n\n"
        "## Apify input\n\n"
        f"```json\n{json.dumps(run_input, ensure_ascii=False, indent=2)}\n```\n\n",
        encoding="utf-8",
    )


def log_step(message: str) -> None:
    ts = datetime.now().isoformat(timespec="seconds")
    with REPORT_PATH.open("a", encoding="utf-8") as handle:
        handle.write(f"- `{ts}` {message}\n")
    print(f"[{ts}] {message}")


if __name__ == "__main__":
    main()
