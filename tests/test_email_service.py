import base64
import unittest
from email import message_from_bytes

from src.outreach.email_service import build_cta_href, build_cta_mailto, build_email_html, create_message


class EmailServiceTest(unittest.TestCase):
    def test_html_contains_prefilled_mailto_button(self):
        brand = {
            "brand_id": "Brand_0145",
            "category": "Moda",
            "gmv_cop_millions_12m": 123.4,
        }

        html = build_email_html(brand, "addi-replies@example.com")

        self.assertIn("<!doctype html>", html)
        self.assertIn("https://mail.google.com/mail/?", html)
        self.assertIn("to=addi-replies%40example.com", html)
        self.assertIn("su=Re%3A+Addi+Marketplace+-+Brand_0145", html)
        self.assertIn("body=Hola+equipo+Addi", html)
        self.assertIn("Agendar conversacion", html)

    def test_create_message_sets_reply_to_and_html_part(self):
        message = create_message(
            "lead@example.com",
            "Subject",
            "<p>Hola</p>",
            reply_to="addi-replies@example.com",
        )
        raw = base64.urlsafe_b64decode(message["raw"])
        parsed = message_from_bytes(raw)

        self.assertEqual(parsed["To"], "lead@example.com")
        self.assertEqual(parsed["Reply-To"], "addi-replies@example.com")
        self.assertTrue(parsed.is_multipart())

    def test_build_cta_mailto_prefills_subject_and_body(self):
        href = build_cta_mailto({"brand_id": "Brand_0145"}, "addi-replies@example.com")

        self.assertTrue(href.startswith("mailto:addi-replies%40example.com?"))
        self.assertIn("Opcion%201", href)

    def test_build_cta_href_opens_gmail_compose_with_to_subject_body(self):
        href = build_cta_href({"brand_id": "Brand_0145"}, "addi-replies@example.com")

        self.assertTrue(href.startswith("https://mail.google.com/mail/?"))
        self.assertIn("to=addi-replies%40example.com", href)
        self.assertIn("su=Re%3A+Addi+Marketplace+-+Brand_0145", href)
        self.assertIn("body=Hola+equipo+Addi", href)


if __name__ == "__main__":
    unittest.main()
