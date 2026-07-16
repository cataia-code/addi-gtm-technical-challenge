"""Live E2E test: scored lead -> email -> reply -> Groq -> WhatsApp/Slack."""

from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from live_demo.email_listener import wait_for_reply_and_classify  # noqa: E402
from src.db import repository  # noqa: E402
from src.outreach.email_service import send_email_d0  # noqa: E402


REPORT_PATH = ROOT / "tests" / "test_e2e_real.md"
DEFAULT_TIER = os.environ.get("DEMO_TIER", "B")


def main() -> None:
    # Paso 0: cargar credenciales locales. El archivo .env esta ignorado por git.
    load_env()
    require_env(
        "DEMO_EMAIL_DESTINO",
        "DEMO_WHATSAPP_NUMBER",
        "GROQ_API_KEY",
        "SLACK_WEBHOOK_URL",
        "TWILIO_ACCOUNT_SID",
        "TWILIO_AUTH_TOKEN",
        "TWILIO_WHATSAPP_FROM",
    )

    reset_report()
    log_step("Inicio E2E real controlado desde analysis/top50.csv.")

    # Paso 1: leer el ranking oficial desde analysis/top50.csv.
    # Si DEMO_BRAND_ID no esta definido, se toma el mejor Tier B por score.
    brand = load_demo_brand()

    # Paso 2: persistir el lead de demo y registrar opt-in para que el gate
    # de WhatsApp del agente permita enviar solo en la rama "agendar".
    repository.upsert_lead(
        brand["brand_id"],
        category=brand.get("category"),
        gmv_cop_millions_12m=brand.get("gmv_cop_millions_12m"),
        tier=brand.get("tier"),
        contacto_email=brand["contacto_email"],
        contacto_whatsapp=brand["contacto_whatsapp"],
    )
    repository.grant_opt_in(brand["brand_id"], "whatsapp")
    log_step("Lead insertado en SQLite y opt_in WhatsApp registrado.")

    # Paso 3: enviar email D0 real por Gmail con plantilla HTML.
    # Guardamos este timestamp para que el listener ignore mensajes viejos.
    sent_after_epoch_ms = int(time.time() * 1000)
    email_result = send_email_d0(
        brand,
        brand["contacto_email"],
        reply_to=os.environ.get("DEMO_REPLY_TO_EMAIL"),
        dry_run=False,
    )
    thread_id = email_result["threadId"]
    repository.upsert_lead(brand["brand_id"], thread_id=thread_id)
    repository.mark_contacted(brand["brand_id"], thread_id=thread_id)
    log_step(f"Email D0 HTML enviado por Gmail. message_id={email_result.get('id')} thread_id={thread_id}")

    # Paso 4: esperar respuesta real en el mismo thread.
    # Importante: process_with_langgraph=True obliga a ejecutar compiled_reply_graph.
    log_step("Iniciando listener Gmail: polling cada 15 segundos esperando reply unread en el thread.")
    state = wait_for_reply_and_classify(
        thread_id=thread_id,
        brand_data=brand,
        poll_seconds=15,
        after_epoch_ms=sent_after_epoch_ms,
        allow_sent_demo_fallback=True,
        process_with_langgraph=True,
        dry_run=False,
    )

    # Paso 5: el estado devuelto ya paso por nodos LangGraph:
    # nodo_clasificar_reply -> nodo_router -> nodo_enviar_whatsapp_agendar
    # o nodo_handoff_nurture/nodo_handoff_descarte segun suggested_action.
    classification = state.get("clasificacion") or {}
    decision = state.get("decision")
    whatsapp_result = state.get("whatsapp_result") or {}
    log_step(
        "Reply detectado y procesado por LangGraph. "
        f"decision={decision} classification={json.dumps(classification, ensure_ascii=False)}"
    )
    log_step(f"LangGraph whatsapp_result={json.dumps(whatsapp_result, ensure_ascii=False)}")
    log_step("LangGraph Slack handoff ejecutado por nodo_handoff_*.")
    log_step("E2E real con LangGraph completado.")


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


def load_demo_brand() -> dict[str, Any]:
    top50 = pd.read_csv(ROOT / "analysis" / "top50.csv")
    brand_id = os.environ.get("DEMO_BRAND_ID")
    if brand_id:
        row = top50[top50["brand_id"].eq(brand_id)]
    else:
        tier_rows = top50[top50["tier"].eq(DEFAULT_TIER)].copy()
        if tier_rows.empty:
            raise RuntimeError(f"No rows found for DEMO_TIER={DEFAULT_TIER} in analysis/top50.csv")
        row = tier_rows.sort_values(["final_score", "gmv_cop_millions_12m"], ascending=False).head(1)
    if row.empty:
        raise RuntimeError(f"DEMO_BRAND_ID={brand_id} not found in analysis/top50.csv")
    brand = row.iloc[0].dropna().to_dict()
    brand["contacto_email"] = os.environ["DEMO_EMAIL_DESTINO"]
    brand["contacto_whatsapp"] = os.environ["DEMO_WHATSAPP_NUMBER"]
    return brand


def reset_report() -> None:
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text("# Test E2E real\n\n", encoding="utf-8")


def log_step(message: str) -> None:
    ts = datetime.now().isoformat(timespec="seconds")
    with REPORT_PATH.open("a", encoding="utf-8") as handle:
        handle.write(f"- `{ts}` {message}\n")
    print(f"[{ts}] {message}")


if __name__ == "__main__":
    main()
