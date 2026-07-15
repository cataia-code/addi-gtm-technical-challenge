"""Twilio WhatsApp service with explicit opt-in gate."""

from __future__ import annotations

import os
import json
from dataclasses import dataclass

import requests


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

    to_whatsapp = to_number if to_number.startswith("whatsapp:") else f"whatsapp:{to_number}"
    url = f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json"
    response = requests.post(
        url,
        data={
            "From": from_number,
            "To": to_whatsapp,
            "ContentSid": content_sid,
            "ContentVariables": json.dumps(content_variables, separators=(",", ":")),
        },
        auth=(account_sid, auth_token),
        timeout=20,
    )
    if not response.ok:
        raise RuntimeError(f"Twilio WhatsApp error {response.status_code}: {response.text}")
    return WhatsAppResult(sent=True, reason="sent", provider_response=response.json())
