"""Controlled dry-run demo over real top50 rows.

By default this does not send email, WhatsApp or Slack. Set dry_run=False from
an explicit caller once credentials and opt-in are ready.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.agents.graph import build_graph  # noqa: E402


def load_brand(brand_id: str) -> dict:
    top50 = pd.read_csv(ROOT / "analysis" / "top50.csv")
    row = top50[top50["brand_id"] == brand_id]
    if row.empty:
        raise ValueError(f"Brand not found in top50.csv: {brand_id}")
    return row.iloc[0].dropna().to_dict()


def run_demo(brand_id: str, reply: str | None = None, dry_run: bool = True) -> dict:
    brand = load_brand(brand_id)
    state = {
        "brand_data": brand,
        "tier": brand["tier"],
        "ya_contactado": False,
        "reply_recibido": reply,
        "clasificacion": None,
        "decision": "",
        "dry_run": dry_run,
        "log_razonamiento": [],
    }
    if os.environ.get("DEMO_EMAIL_DESTINO"):
        brand["contacto_email"] = os.environ["DEMO_EMAIL_DESTINO"]
    if os.environ.get("DEMO_WHATSAPP_NUMBER"):
        brand["contacto_whatsapp"] = os.environ["DEMO_WHATSAPP_NUMBER"]
    graph = build_graph()
    return graph.invoke(state)


if __name__ == "__main__":
    for brand_id, reply in [
        ("Brand_0002", None),
        ("Brand_0145", "Si me interesa, podemos agendar una llamada esta semana."),
        ("Brand_0826", "Por favor no me vuelvan a escribir."),
    ]:
        result = run_demo(brand_id, reply=reply, dry_run=True)
        print(f"\n=== {brand_id} ===")
        for line in result.get("log_razonamiento", []):
            print(f"- {line}")
