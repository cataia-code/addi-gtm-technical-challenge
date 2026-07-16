"""Recover an E2E run when Gmail self-test reply lands in a new sent thread."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from live_demo.email_listener import wait_for_reply_and_classify  # noqa: E402
from live_demo.test1_e2e_real import REPORT_PATH, load_demo_brand, load_env, log_step  # noqa: E402
from src.db import repository  # noqa: E402
from src.outreach.email_service import get_gmail_service  # noqa: E402


def main() -> None:
    # Recupera el ultimo thread_id del reporte y vuelve a procesar el reply.
    # La recuperacion tambien usa LangGraph: compiled_reply_graph se invoca
    # desde wait_for_reply_and_classify(process_with_langgraph=True).
    load_env()
    thread_id = _latest_thread_id_from_report()
    brand = load_demo_brand()
    repository.grant_opt_in(brand["brand_id"], "whatsapp")

    after_epoch_ms = _thread_first_message_epoch_ms(thread_id)
    log_step(f"Recuperacion E2E: thread_id={thread_id} after_epoch_ms={after_epoch_ms}.")
    state = wait_for_reply_and_classify(
        thread_id=thread_id,
        brand_data=brand,
        poll_seconds=1,
        timeout_seconds=30,
        after_epoch_ms=after_epoch_ms,
        allow_sent_demo_fallback=True,
        process_with_langgraph=True,
        dry_run=False,
    )
    log_step(
        "Reply recuperado y procesado por LangGraph. "
        f"decision={state.get('decision')} "
        f"classification={json.dumps(state.get('clasificacion') or {}, ensure_ascii=False)} "
        f"whatsapp_result={json.dumps(state.get('whatsapp_result') or {}, ensure_ascii=False)}"
    )


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
