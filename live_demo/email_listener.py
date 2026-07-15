"""Gmail polling listener for the live E2E demo."""

from __future__ import annotations

import base64
import re
import time
from html import unescape
from typing import Any

from src.agents.nodes import nodo_clasificar_reply, nodo_router
from src.agents.state import GTMState
from src.outreach.email_service import get_gmail_service


def wait_for_reply_and_classify(
    *,
    thread_id: str,
    brand_data: dict[str, Any],
    poll_seconds: int = 15,
    timeout_seconds: int = 900,
) -> GTMState:
    """Poll Gmail for an unread reply in a thread and classify it."""

    service = get_gmail_service()
    deadline = time.time() + timeout_seconds

    while time.time() < deadline:
        message = _find_unread_message_in_thread(service, thread_id)
        if message:
            reply_text = extract_message_text(message)
            state: GTMState = {
                "brand_data": brand_data,
                "tier": str(brand_data.get("tier", "")),
                "ya_contactado": True,
                "reply_recibido": reply_text,
                "clasificacion": None,
                "decision": "",
                "log_razonamiento": [],
            }
            nodo_clasificar_reply(state)
            nodo_router(state)
            return state
        time.sleep(poll_seconds)

    raise TimeoutError(f"No unread reply detected for Gmail thread_id={thread_id}")


def _find_unread_message_in_thread(service, thread_id: str) -> dict[str, Any] | None:
    """Try Gmail search first, then fall back to threads.get."""

    query = f"in:thread {thread_id} is:unread"
    try:
        listed = service.users().messages().list(userId="me", q=query).execute()
        for item in listed.get("messages", []):
            message = service.users().messages().get(userId="me", id=item["id"], format="full").execute()
            if message.get("threadId") == thread_id and "UNREAD" in message.get("labelIds", []):
                return message
    except Exception:
        # Gmail search syntax can vary; threads.get is the reliable fallback by thread_id.
        pass

    thread = service.users().threads().get(userId="me", id=thread_id, format="full").execute()
    for message in thread.get("messages", []):
        if "UNREAD" in message.get("labelIds", []):
            return message
    return None


def extract_message_text(message: dict[str, Any]) -> str:
    payload = message.get("payload", {})
    text = _walk_payload_for_mime(payload, "text/plain")
    if not text:
        text = _html_to_text(_walk_payload_for_mime(payload, "text/html"))
    return _clean_reply_text(text)


def _walk_payload_for_mime(payload: dict[str, Any], mime_type: str) -> str:
    if payload.get("mimeType") == mime_type and payload.get("body", {}).get("data"):
        return _decode_base64url(payload["body"]["data"])
    for part in payload.get("parts", []) or []:
        found = _walk_payload_for_mime(part, mime_type)
        if found:
            return found
    return ""


def _decode_base64url(data: str) -> str:
    padded = data + "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(padded.encode("utf-8")).decode("utf-8", errors="replace")


def _html_to_text(html: str) -> str:
    no_tags = re.sub(r"<[^>]+>", " ", html or "")
    return unescape(no_tags)


def _clean_reply_text(text: str) -> str:
    lines = []
    for line in (text or "").splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith(">"):
            continue
        if re.match(r"^On .+ wrote:$", stripped):
            break
        lines.append(stripped)
    return "\n".join(lines).strip()
