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
    after_epoch_ms: int | None = None,
    allow_sent_demo_fallback: bool = False,
    process_with_langgraph: bool = False,
    dry_run: bool = True,
) -> GTMState:
    """Poll Gmail for an unread reply in a thread and classify it."""

    service = get_gmail_service()
    deadline = time.time() + timeout_seconds

    while time.time() < deadline:
        message = _find_unread_message_in_thread(service, thread_id, after_epoch_ms=after_epoch_ms)
        if not message and allow_sent_demo_fallback:
            message = _find_recent_demo_reply(service, brand_data, after_epoch_ms=after_epoch_ms)
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
                "dry_run": dry_run,
                "whatsapp_result": None,
            }
            if process_with_langgraph:
                from src.agents.graph import compiled_reply_graph

                return compiled_reply_graph.invoke(state)
            nodo_clasificar_reply(state)
            nodo_router(state)
            return state
        time.sleep(poll_seconds)

    raise TimeoutError(f"No unread reply detected for Gmail thread_id={thread_id}")


def _find_unread_message_in_thread(
    service,
    thread_id: str,
    *,
    after_epoch_ms: int | None = None,
) -> dict[str, Any] | None:
    """Try Gmail search first, then fall back to threads.get."""

    query = f"is:unread -from:me"
    try:
        listed = service.users().messages().list(userId="me", q=query).execute()
        for item in listed.get("messages", []):
            message = service.users().messages().get(userId="me", id=item["id"], format="full").execute()
            if _is_target_reply(message, thread_id, after_epoch_ms=after_epoch_ms):
                return message
    except Exception:
        # Gmail search syntax can vary; threads.get is the reliable fallback by thread_id.
        pass

    thread = service.users().threads().get(userId="me", id=thread_id, format="full").execute()
    for message in thread.get("messages", []):
        if _is_target_reply(message, thread_id, after_epoch_ms=after_epoch_ms):
            return message
    return None


def _find_recent_demo_reply(
    service,
    brand_data: dict[str, Any],
    *,
    after_epoch_ms: int | None = None,
) -> dict[str, Any] | None:
    """Self-test fallback: Gmail Compose can create a sent message in a new thread."""

    brand_id = str(brand_data.get("brand_id", ""))
    query = f'newer_than:1d "{brand_id}"'
    listed = service.users().messages().list(userId="me", q=query, maxResults=10).execute()
    candidates = []
    for item in listed.get("messages", []):
        message = service.users().messages().get(userId="me", id=item["id"], format="full").execute()
        if _looks_like_demo_reply(message, brand_id, after_epoch_ms=after_epoch_ms):
            candidates.append(message)
    if not candidates:
        return None
    return max(candidates, key=lambda msg: int(msg.get("internalDate", "0")))


def _looks_like_demo_reply(
    message: dict[str, Any],
    brand_id: str,
    *,
    after_epoch_ms: int | None = None,
) -> bool:
    if after_epoch_ms is not None and int(message.get("internalDate", "0")) < after_epoch_ms:
        return False
    text = extract_message_text(message)
    normalized = text.lower()
    if brand_id.lower() not in normalized:
        return False
    if "notamos que" in normalized and "tus clientes ya usan" in normalized:
        return False
    return any(token in normalized for token in ["si me interesa", "sí me interesa", "agendar", "opcion", "opción"])


def _is_target_reply(message: dict[str, Any], thread_id: str, *, after_epoch_ms: int | None = None) -> bool:
    labels = set(message.get("labelIds", []))
    if message.get("threadId") != thread_id:
        return False
    if "UNREAD" not in labels or "SENT" in labels:
        return False
    if after_epoch_ms is not None and int(message.get("internalDate", "0")) < after_epoch_ms:
        return False
    return True


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
