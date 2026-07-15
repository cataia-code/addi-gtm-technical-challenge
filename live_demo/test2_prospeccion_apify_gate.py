"""Test 2: Apify prospecting with Slack approval gate only.

This script must never send email or WhatsApp to scraped prospects.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import requests

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.enrichment.apify_apollo_scraper import hogar_colombia_input, run_apollo_organizations_scraper
from src.enrichment.llm_research import synthesize_company_profile
from src.qualification.draft_writer import draft_outreach_email


REPORT_PATH = ROOT / "tests" / "test2_prospeccion_apify_gate.md"


def main() -> None:
    load_env()
    parser = argparse.ArgumentParser()
    parser.add_argument("--confirm-run", action="store_true", help="Actually call Apify and Groq.")
    parser.add_argument("--max-results", type=int, default=3)
    args = parser.parse_args()

    run_input = hogar_colombia_input()
    print("INPUT_APIFY_CONFIRMAR_ANTES_DE_EJECUTAR:")
    print(json.dumps(run_input, ensure_ascii=False, indent=2))
    if not args.confirm_run:
        print("No se ejecuto Apify. Reejecuta con --confirm-run para gastar UNA llamada real.")
        return

    require_env("APIFY_API_TOKEN", "GROQ_API_KEY", "SLACK_WEBHOOK_URL")
    reset_report(run_input)
    companies = run_apollo_organizations_scraper(run_input, max_results=args.max_results)
    log_step(f"Apify devolvio {len(companies)} empresas normalizadas.")

    for company in companies:
        profile = synthesize_company_profile(company.as_llm_context())
        draft = draft_outreach_email(company.as_llm_context(), profile)
        post_draft_to_slack(company.as_llm_context(), profile, draft)
        log_step(f"Slack gate enviado para {company.name} | domain={company.domain} | industry={company.industry}")
        append_result(company.as_llm_context(), profile, draft)


def post_draft_to_slack(company: dict[str, Any], profile: str, draft: str) -> None:
    payload = {
        "text": "BORRADOR PARA REVISION - NO SE HA ENVIADO NADA A ESTE CONTACTO",
        "blocks": [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "BORRADOR PARA REVISION - NO SE HA ENVIADO NADA A ESTE CONTACTO",
                },
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Empresa:*\n{company.get('name') or 'N/A'}"},
                    {"type": "mrkdwn", "text": f"*Dominio:*\n{company.get('domain') or 'N/A'}"},
                    {"type": "mrkdwn", "text": f"*Contacto:*\n{company.get('contact_name') or 'N/A'}"},
                    {"type": "mrkdwn", "text": f"*Cargo:*\n{company.get('contact_title') or 'N/A'}"},
                    {"type": "mrkdwn", "text": f"*Email:*\n{company.get('contact_email') or 'N/A'}"},
                    {"type": "mrkdwn", "text": f"*Telefono:*\n{company.get('contact_phone') or 'N/A'}"},
                    {"type": "mrkdwn", "text": f"*Industria:*\n{company.get('industry') or 'N/A'}"},
                    {"type": "mrkdwn", "text": f"*Ubicacion:*\n{company.get('city') or 'N/A'}, {company.get('country') or 'N/A'}"},
                ],
            },
            {"type": "section", "text": {"type": "mrkdwn", "text": f"*Perfil investigado:*\n```{safe_code(profile)}```"}},
            {"type": "section", "text": {"type": "mrkdwn", "text": f"*Borrador email:*\n```{safe_code(draft, 2500)}```"}},
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"Gate humano obligatorio - {datetime.now().isoformat(timespec='seconds')}",
                    }
                ],
            },
        ],
    }
    response = requests.post(os.environ["SLACK_WEBHOOK_URL"], json=payload, timeout=20)
    response.raise_for_status()


def safe_code(text: str, limit: int = 1800) -> str:
    clean = (text or "").replace("```", "'''").strip()
    if len(clean) <= limit:
        return clean
    return clean[: limit - 30].rstrip() + "\n...[truncado]"


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


def reset_report(run_input: dict[str, Any]) -> None:
    REPORT_PATH.write_text(
        "# Test 2: prospeccion real con gate de aprobacion\n\n"
        "## Apify input\n\n"
        f"```json\n{json.dumps(run_input, ensure_ascii=False, indent=2)}\n```\n\n",
        encoding="utf-8",
    )


def log_step(message: str) -> None:
    ts = datetime.now().isoformat(timespec="seconds")
    with REPORT_PATH.open("a", encoding="utf-8") as handle:
        handle.write(f"- `{ts}` {message}\n")
    print(f"[{ts}] {message}")


def append_result(company: dict[str, Any], profile: str, draft: str) -> None:
    with REPORT_PATH.open("a", encoding="utf-8") as handle:
        handle.write("\n## Prospecto\n\n")
        handle.write(f"- Empresa: {company.get('name')}\n")
        handle.write(f"- Dominio: {company.get('domain')}\n")
        handle.write(f"- Contacto: {company.get('contact_name')}\n")
        handle.write(f"- Cargo: {company.get('contact_title')}\n")
        handle.write(f"- Email: {company.get('contact_email')}\n")
        handle.write(f"- Telefono: {company.get('contact_phone')}\n")
        handle.write(f"- LinkedIn: {company.get('linkedin_url')}\n")
        handle.write(f"- Industria: {company.get('industry')}\n")
        handle.write(f"- Ubicacion: {company.get('city')}, {company.get('country')}\n\n")
        handle.write("### Perfil\n\n")
        handle.write(profile + "\n\n")
        handle.write("### Borrador\n\n")
        handle.write(draft + "\n")


if __name__ == "__main__":
    main()
