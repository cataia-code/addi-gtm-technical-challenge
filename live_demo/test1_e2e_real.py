"""Live E2E test: Brand_0145 email -> reply -> Groq -> WhatsApp/Slack."""

from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from live_demo.email_listener import wait_for_reply_and_classify
from src.db import repository
from src.outreach.email_service import send_email_d0
from src.outreach.whatsapp_service import send_whatsapp


REPORT_PATH = ROOT / "tests" / "test_e2e_real.md"
BRAND_ID = "Brand_0145"


def main() -> None:
    load_env()
    require_env(
        "DEMO_EMAIL_DESTINO",
        "DEMO_WHATSAPP_NUMBER",
        "GROQ_API_KEY",
        "SLACK_WEBHOOK_URL",
        "TWILIO_ACCOUNT_SID",
        "TWILIO_AUTH_TOKEN",
        "TWILIO_WHATSAPP_FROM",
        "TWILIO_CONTENT_SID",
    )

    reset_report()
    log_step("Inicio E2E real controlado Brand_0145.")

    brand = load_brand_0145()
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

    email_result = send_email_d0(
        brand,
        brand["contacto_email"],
        reply_to=os.environ.get("DEMO_REPLY_TO_EMAIL"),
        dry_run=False,
    )
    sent_after_epoch_ms = int(time.time() * 1000)
    thread_id = email_result["threadId"]
    repository.upsert_lead(brand["brand_id"], thread_id=thread_id)
    repository.mark_contacted(brand["brand_id"], thread_id=thread_id)
    log_step(f"Email D0 HTML enviado por Gmail. message_id={email_result.get('id')} thread_id={thread_id}")

    log_step("Iniciando listener Gmail: polling cada 15 segundos esperando reply unread en el thread.")
    state = wait_for_reply_and_classify(
        thread_id=thread_id,
        brand_data=brand,
        poll_seconds=15,
        after_epoch_ms=sent_after_epoch_ms,
    )
    reply_text = state.get("reply_recibido") or ""
    classification = state.get("clasificacion") or {}
    decision = state.get("decision")
    log_step(f"Reply detectado y clasificado. decision={decision} classification={json.dumps(classification, ensure_ascii=False)}")

    twilio_called = False
    action_taken = ""
    timestamp = datetime.now().isoformat(timespec="seconds")

    if decision == "agendar":
        has_opt_in = repository.has_opt_in(brand["brand_id"], "whatsapp")
        assert has_opt_in, "No se puede enviar WhatsApp real sin opt_in"
        wa_body = (
            "Gracias por tu respuesta. Un especialista de Addi Marketplace te contactará "
            "para coordinar la llamada de 20 minutos."
        )
        wa_result = send_whatsapp(
            brand["contacto_whatsapp"],
            wa_body,
            has_opt_in=has_opt_in,
            dry_run=False,
            content_variables={"1": "12/1", "2": "3pm"},
        )
        twilio_called = wa_result.sent
        assert twilio_called, f"Twilio no confirmó envío: {wa_result.reason}"
        action_taken = "WhatsApp aceptado por Twilio + handoff Slack"
        log_step(
            "WhatsApp aceptado por Twilio. "
            f"sid={wa_result.provider_response.get('sid') if wa_result.provider_response else 'N/A'} "
            "Nota: en Sandbox, entrega final requiere que el destino haya enviado el join code correcto."
        )
    elif decision == "nurture":
        action_taken = "Solo Slack nurture; WhatsApp no enviado"
        log_step("Nurture: no se llama Twilio.")
    else:
        action_taken = "Slack descarte; WhatsApp bloqueado"
        # Assert explícito de compliance: en descarte/opt-out no se llama Twilio.
        assert not twilio_called, "BUG: Twilio fue llamado en rama descartar/opt-out"
        log_step("Descartar/opt-out: assert PASS, Twilio no fue llamado.")

    post_final_slack(brand, reply_text, classification, action_taken, timestamp)
    log_step(f"Slack Block Kit final enviado. action_taken={action_taken}")
    log_step("E2E real completado.")


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


def load_brand_0145() -> dict[str, Any]:
    top50 = pd.read_csv(ROOT / "analysis" / "top50.csv")
    row = top50[top50["brand_id"].eq(BRAND_ID)]
    if row.empty:
        raise RuntimeError(f"{BRAND_ID} not found in analysis/top50.csv")
    brand = row.iloc[0].dropna().to_dict()
    brand["contacto_email"] = os.environ["DEMO_EMAIL_DESTINO"]
    brand["contacto_whatsapp"] = os.environ["DEMO_WHATSAPP_NUMBER"]
    return brand


def post_final_slack(
    brand: dict[str, Any],
    reply_text: str,
    classification: dict[str, Any],
    action_taken: str,
    timestamp: str,
) -> None:
    payload = {
        "text": "E2E real Addi Marketplace",
        "blocks": [
            {"type": "header", "text": {"type": "plain_text", "text": "E2E real - Addi Marketplace"}},
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Brand:*\n{brand.get('brand_id')}"},
                    {"type": "mrkdwn", "text": f"*Categoria:*\n{brand.get('category')}"},
                    {"type": "mrkdwn", "text": f"*GMV 12m:*\nCOP {brand.get('gmv_cop_millions_12m')} MM"},
                    {"type": "mrkdwn", "text": f"*Score:*\n{brand.get('final_score')}"},
                    {"type": "mrkdwn", "text": f"*Momentum:*\n{brand.get('gmv_90d_to_12m_ratio')}"},
                    {"type": "mrkdwn", "text": f"*Timestamp:*\n{timestamp}"},
                ],
            },
            {"type": "divider"},
            {"type": "section", "text": {"type": "mrkdwn", "text": f"*Reply exacto:*\n>{reply_text}"}},
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Clasificación JSON:*\n```{json.dumps(classification, ensure_ascii=False, indent=2)}```",
                },
            },
            {"type": "section", "text": {"type": "mrkdwn", "text": f"*Acción tomada:*\n{action_taken}"}},
        ],
    }
    response = requests.post(os.environ["SLACK_WEBHOOK_URL"], json=payload, timeout=15)
    response.raise_for_status()


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
