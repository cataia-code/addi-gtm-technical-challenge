"""Recover an E2E run when Gmail self-test reply lands in a new sent thread."""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from live_demo.email_listener import wait_for_reply_and_classify
from live_demo.test1_e2e_real import REPORT_PATH, load_brand_0145, load_env, log_step, post_final_slack
from src.db import repository
from src.outreach.email_service import get_gmail_service
from src.outreach.whatsapp_service import send_whatsapp


def main() -> None:
    load_env()
    thread_id = _latest_thread_id_from_report()
    brand = load_brand_0145()
    repository.grant_opt_in(brand["brand_id"], "whatsapp")

    after_epoch_ms = _thread_first_message_epoch_ms(thread_id)
    log_step(f"Recuperacion E2E: buscando reply demo desde thread_id={thread_id} after_epoch_ms={after_epoch_ms}.")
    state = wait_for_reply_and_classify(
        thread_id=thread_id,
        brand_data=brand,
        poll_seconds=1,
        timeout_seconds=30,
        after_epoch_ms=after_epoch_ms,
        allow_sent_demo_fallback=True,
    )
    reply_text = state.get("reply_recibido") or ""
    classification = state.get("clasificacion") or {}
    decision = state.get("decision")
    log_step(f"Reply recuperado y clasificado. decision={decision} classification={json.dumps(classification, ensure_ascii=False)}")

    action_taken = ""
    if decision == "agendar":
        has_opt_in = repository.has_opt_in(brand["brand_id"], "whatsapp")
        assert has_opt_in, "No se puede enviar WhatsApp real sin opt_in"
        wa_body = (
            "Hola, gracias por tu respuesta. Soy del equipo Addi Marketplace. "
            "Recibimos tu interes y un especialista te contactara para coordinar "
            "una llamada de 20 minutos."
        )
        wa_result = send_whatsapp(
            brand["contacto_whatsapp"],
            wa_body,
            has_opt_in=has_opt_in,
            dry_run=False,
        )
        action_taken = "WhatsApp en espanol enviado via Twilio SDK + handoff Slack"
        log_step(
            "WhatsApp enviado via Twilio SDK. "
            f"sid={wa_result.provider_response.get('sid') if wa_result.provider_response else 'N/A'} "
            f"status={wa_result.provider_response.get('status') if wa_result.provider_response else 'N/A'}"
        )
    elif decision == "nurture":
        action_taken = "Solo Slack nurture; WhatsApp no enviado"
        log_step("Nurture: no se llama Twilio.")
    else:
        action_taken = "Slack descarte; WhatsApp bloqueado"
        log_step("Descartar/opt-out: Twilio no fue llamado.")

    post_final_slack(brand, reply_text, classification, action_taken, datetime.now().isoformat(timespec="seconds"))
    log_step(f"Slack Block Kit final enviado. action_taken={action_taken}")
    log_step("Recuperacion E2E completada.")


def _latest_thread_id_from_report() -> str:
    text = REPORT_PATH.read_text(encoding="utf-8")
    matches = re.findall(r"thread_id=([a-zA-Z0-9_-]+)", text)
    if not matches:
        raise RuntimeError(f"No thread_id found in {REPORT_PATH}")
    return matches[-1]


def _thread_first_message_epoch_ms(thread_id: str) -> int:
    service = get_gmail_service()
    thread = service.users().threads().get(userId="me", id=thread_id, format="metadata").execute()
    dates = [int(message.get("internalDate", "0")) for message in thread.get("messages", [])]
    if not dates:
        raise RuntimeError(f"No messages found for thread_id={thread_id}")
    return min(dates)


if __name__ == "__main__":
    main()
