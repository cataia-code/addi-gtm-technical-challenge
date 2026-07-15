"""Twilio WhatsApp inbound webhook for the live demo.

Run locally with:
    python live_demo/whatsapp_listener.py

Expose it with a tunnel and configure Twilio Sandbox "When a message comes in"
to POST to:
    https://<public-tunnel>/twilio/whatsapp
"""

from __future__ import annotations

import os
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.agents.nodes import nodo_clasificar_reply, nodo_router
from src.agents.state import GTMState
from src.db import repository
from src.handoff.slack_service import post_handoff

BRAND_ID = os.environ.get("DEMO_BRAND_ID", "Brand_0145")


def handle_inbound_whatsapp(form: dict[str, str], brand_data: dict[str, Any]) -> GTMState:
    reply_text = form.get("Body", "").strip()
    from_number = form.get("From", "")
    message_sid = form.get("MessageSid", "")
    if not reply_text:
        raise ValueError("Twilio inbound webhook did not include Body")

    state: GTMState = {
        "brand_data": brand_data,
        "tier": str(brand_data.get("tier", "")),
        "ya_contactado": True,
        "reply_recibido": reply_text,
        "clasificacion": None,
        "decision": "",
        "log_razonamiento": [
            f"whatsapp_listener: inbound From={from_number} MessageSid={message_sid}",
        ],
    }
    nodo_clasificar_reply(state)
    nodo_router(state)
    if state["decision"] == "descartar":
        state["log_razonamiento"].append("whatsapp_listener: descarte/opt-out; Twilio outbound bloqueado.")
    post_handoff(
        state["brand_data"],
        state["clasificacion"] or {},
        state.get("reply_recibido") or "",
        state["log_razonamiento"],
        dry_run=not bool(os.environ.get("SLACK_WEBHOOK_URL")),
    )
    state["log_razonamiento"].append("whatsapp_listener: handoff Slack emitido o preparado.")
    return state


def load_brand(brand_id: str = BRAND_ID) -> dict[str, Any]:
    top50 = pd.read_csv(ROOT / "analysis" / "top50.csv")
    row = top50[top50["brand_id"].eq(brand_id)]
    if row.empty:
        raise RuntimeError(f"{brand_id} not found in analysis/top50.csv")
    brand = row.iloc[0].dropna().to_dict()
    if os.environ.get("DEMO_EMAIL_DESTINO"):
        brand["contacto_email"] = os.environ["DEMO_EMAIL_DESTINO"]
    if os.environ.get("DEMO_WHATSAPP_NUMBER"):
        brand["contacto_whatsapp"] = os.environ["DEMO_WHATSAPP_NUMBER"]
    return brand


class TwilioWhatsAppHandler(BaseHTTPRequestHandler):
    def do_POST(self) -> None:
        if self.path != "/twilio/whatsapp":
            self.send_response(404)
            self.end_headers()
            return

        length = int(self.headers.get("Content-Length", "0"))
        raw_body = self.rfile.read(length).decode("utf-8", errors="replace")
        form = {key: values[0] for key, values in parse_qs(raw_body).items()}
        try:
            state = handle_inbound_whatsapp(form, load_brand())
            response = (
                "<Response><Message>"
                f"Recibido. Accion: {state.get('decision', 'pendiente')}"
                "</Message></Response>"
            )
            self.send_response(200)
        except Exception as exc:
            response = f"<Response><Message>Error procesando reply: {exc}</Message></Response>"
            self.send_response(500)

        self.send_header("Content-Type", "text/xml; charset=utf-8")
        self.end_headers()
        self.wfile.write(response.encode("utf-8"))


def run_server(host: str = "0.0.0.0", port: int = 8787) -> None:
    repository.init_db()
    server = HTTPServer((host, port), TwilioWhatsAppHandler)
    print(f"Twilio WhatsApp listener running on http://{host}:{port}/twilio/whatsapp")
    server.serve_forever()


if __name__ == "__main__":
    run_server(port=int(os.environ.get("WHATSAPP_LISTENER_PORT", "8787")))
