"""Gmail API email service."""

from __future__ import annotations

import base64
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Any

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build


ROOT = Path(__file__).resolve().parents[2]
SCOPES = ["https://www.googleapis.com/auth/gmail.send", "https://www.googleapis.com/auth/gmail.readonly"]
TEMPLATE_PATH = Path(__file__).resolve().parent / "templates" / "email_d0.html"


def render_template(template: str, values: dict[str, Any]) -> str:
    rendered = template
    for key, value in values.items():
        rendered = rendered.replace("{{ " + key + " }}", str(value))
    return rendered


def build_email_html(brand: dict[str, Any], reply_to: str) -> str:
    template = TEMPLATE_PATH.read_text(encoding="utf-8")
    values = {**brand, "reply_to": reply_to}
    return render_template(template, values)


def get_gmail_service(
    credentials_path: Path = ROOT / "credentials.json",
    token_path: Path = ROOT / "token.json",
):
    creds = None
    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(str(credentials_path), SCOPES)
            creds = flow.run_local_server(port=0)
        token_path.write_text(creds.to_json(), encoding="utf-8")
    return build("gmail", "v1", credentials=creds)


def create_message(to_email: str, subject: str, html_body: str, text_body: str | None = None) -> dict[str, str]:
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = "me"
    msg["To"] = to_email
    if text_body:
        msg.attach(MIMEText(text_body, "plain", "utf-8"))
    msg.attach(MIMEText(html_body, "html", "utf-8"))
    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode("utf-8")
    return {"raw": raw}


def send_email_d0(
    brand: dict[str, Any],
    to_email: str,
    *,
    reply_to: str,
    dry_run: bool = True,
) -> dict[str, Any]:
    html = build_email_html(brand, reply_to=reply_to)
    subject = f"Addi Marketplace: oportunidad para {brand.get('category', 'tu categoria')}"
    message = create_message(to_email, subject, html)
    if dry_run:
        return {"dry_run": True, "subject": subject, "to": to_email, "html": html}
    service = get_gmail_service()
    return service.users().messages().send(userId="me", body=message).execute()

