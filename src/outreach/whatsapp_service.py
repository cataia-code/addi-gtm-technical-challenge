"""Twilio WhatsApp service with explicit opt-in gate."""

from __future__ import annotations

import os
import json
from dataclasses import dataclass

try:
    from twilio.rest import Client
except ImportError:  # pragma: no cover - exercised only when dependency is missing.
    Client = None


@dataclass(frozen=True)
class WhatsAppResult:
    sent: bool
    reason: str
    provider_response: dict | None = None


def send_whatsapp(
    to_number: str,
    body: str,
    *,
    has_opt_in: bool,
    dry_run: bool = True,
    content_sid: str | None = None,
    content_variables: dict[str, str] | None = None,
) -> WhatsAppResult:
    if not has_opt_in:
        return WhatsAppResult(sent=False, reason="blocked_no_opt_in")
    if dry_run:
        return WhatsAppResult(sent=False, reason="dry_run")

    account_sid = os.environ.get("TWILIO_ACCOUNT_SID")
    auth_token = os.environ.get("TWILIO_AUTH_TOKEN")
    from_number = os.environ.get("TWILIO_WHATSAPP_FROM")
    content_sid = content_sid or os.environ.get("TWILIO_CONTENT_SID")
    content_variables = content_variables or {"1": "12/1", "2": "3pm"}
    if not all([account_sid, auth_token, from_number, content_sid]):
        raise RuntimeError("Twilio env vars are required for live WhatsApp")
    if Client is None:
        raise RuntimeError("Install the Twilio SDK before sending WhatsApp: pip install twilio")

    to_whatsapp = to_number if to_number.startswith("whatsapp:") else f"whatsapp:{to_number}"
    client = Client(account_sid, auth_token)
    message = client.messages.create(
        from_=from_number,
        content_sid=content_sid,
        content_variables=json.dumps(content_variables, separators=(",", ":")),
        to=to_whatsapp,
    )
    return WhatsAppResult(sent=True, reason="sent", provider_response=_message_to_dict(message))


def _message_to_dict(message) -> dict:
    return {
        "sid": getattr(message, "sid", None),
        "status": getattr(message, "status", None),
        "error_code": getattr(message, "error_code", None),
        "error_message": getattr(message, "error_message", None),
        "to": getattr(message, "to", None),
        "from": getattr(message, "from_", None) or getattr(message, "from", None),
        "body": getattr(message, "body", None),
    }
