import os
import unittest
from unittest.mock import patch

from src.outreach.whatsapp_service import send_whatsapp


class _TwilioResponse:
    ok = True
    status_code = 201
    text = "created"

    def json(self):
        return {"sid": "MM_test", "status": "queued"}


class WhatsAppServiceTest(unittest.TestCase):
    def test_send_whatsapp_uses_twilio_content_template(self):
        env = {
            "TWILIO_ACCOUNT_SID": "AC_test",
            "TWILIO_AUTH_TOKEN": "token",
            "TWILIO_WHATSAPP_FROM": "whatsapp:+14155238886",
            "TWILIO_CONTENT_SID": "HXb5b62575e6e4ff6129ad7c8efe1f983e",
        }
        captured = {}

        def fake_post(url, data, auth, timeout):
            captured.update(url=url, data=data, auth=auth, timeout=timeout)
            return _TwilioResponse()

        with patch.dict(os.environ, env), patch("src.outreach.whatsapp_service.requests.post", fake_post):
            result = send_whatsapp(
                "+573228250742",
                "ignored when ContentSid is used",
                has_opt_in=True,
                dry_run=False,
                content_variables={"1": "12/1", "2": "3pm"},
            )

        self.assertTrue(result.sent)
        self.assertEqual(
            captured["data"],
            {
                "From": "whatsapp:+14155238886",
                "To": "whatsapp:+573228250742",
                "ContentSid": "HXb5b62575e6e4ff6129ad7c8efe1f983e",
                "ContentVariables": '{"1":"12/1","2":"3pm"}',
            },
        )


if __name__ == "__main__":
    unittest.main()
