import os
import unittest
from unittest.mock import patch

from src.outreach.whatsapp_service import send_whatsapp


class _TwilioMessage:
    sid = "MM_test"
    status = "queued"
    error_code = None
    error_message = None
    to = "whatsapp:+573228250742"
    from_ = "whatsapp:+14155238886"
    body = "Your appointment is coming up on 12/1 at 3pm"


class _Messages:
    def __init__(self, captured):
        self.captured = captured

    def create(self, **kwargs):
        self.captured.update(kwargs)
        return _TwilioMessage()


class _Client:
    def __init__(self, account_sid, auth_token):
        self.account_sid = account_sid
        self.auth_token = auth_token
        self.messages = _Messages(self.__class__.captured)

    captured = {}


class WhatsAppServiceTest(unittest.TestCase):
    def test_send_whatsapp_uses_body_by_default(self):
        env = {
            "TWILIO_ACCOUNT_SID": "AC_test",
            "TWILIO_AUTH_TOKEN": "token",
            "TWILIO_WHATSAPP_FROM": "whatsapp:+14155238886",
        }
        _Client.captured = {}

        with patch.dict(os.environ, env), patch("src.outreach.whatsapp_service.Client", _Client):
            result = send_whatsapp(
                "+573228250742",
                "Hola, gracias por tu respuesta.",
                has_opt_in=True,
                dry_run=False,
            )

        self.assertTrue(result.sent)
        self.assertEqual(
            _Client.captured,
            {
                "from_": "whatsapp:+14155238886",
                "to": "whatsapp:+573228250742",
                "body": "Hola, gracias por tu respuesta.",
            },
        )

    def test_send_whatsapp_uses_twilio_content_template_when_requested(self):
        env = {
            "TWILIO_ACCOUNT_SID": "AC_test",
            "TWILIO_AUTH_TOKEN": "token",
            "TWILIO_WHATSAPP_FROM": "whatsapp:+14155238886",
            "TWILIO_CONTENT_SID": "HXb5b62575e6e4ff6129ad7c8efe1f983e",
        }
        _Client.captured = {}

        with patch.dict(os.environ, env), patch("src.outreach.whatsapp_service.Client", _Client):
            result = send_whatsapp(
                "+573228250742",
                "ignored when ContentSid is used",
                has_opt_in=True,
                dry_run=False,
                content_variables={"1": "12/1", "2": "3pm"},
                use_content_template=True,
            )

        self.assertTrue(result.sent)
        self.assertEqual(
            _Client.captured,
            {
                "from_": "whatsapp:+14155238886",
                "to": "whatsapp:+573228250742",
                "content_sid": "HXb5b62575e6e4ff6129ad7c8efe1f983e",
                "content_variables": '{"1":"12/1","2":"3pm"}',
            },
        )
        self.assertEqual(result.provider_response["sid"], "MM_test")


if __name__ == "__main__":
    unittest.main()
