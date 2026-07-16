import os
import unittest
from unittest.mock import patch

from src.enrichment.apify_apollo_scraper import (
    first_present,
    hogar_colombia_input,
    normalize_company,
    run_apollo_organizations_scraper,
)
from src.enrichment.apollo_client import draft_message, search_people
from src.enrichment.llm_research import synthesize_company_profile
from src.handoff.slack_service import extract_meeting_times, post_handoff
from src.qualification.draft_writer import draft_outreach_email
from src.qualification.llm_qualifier import classify_reply, normalize_action, parse_qualification


class _Response:
    def __init__(self, payload, status_code=200):
        self._payload = payload
        self.status_code = status_code

    def json(self):
        return self._payload

    def raise_for_status(self):
        return None


class ExternalClientsMockedTest(unittest.TestCase):
    def test_qualification_parse_normalize_and_classify(self):
        self.assertEqual(normalize_action("AGENDAR", 10), "agendar")
        self.assertEqual(normalize_action("texto largo", 75), "agendar")
        parsed = parse_qualification('{"intent_score": 42, "suggested_action": "otro", "reasoning": "Tibio"}')
        self.assertEqual(parsed.suggested_action, "nurture")

        response = _Response({"choices": [{"message": {"content": '{"intent_score": 95, "suggested_action": "agendar", "reasoning": "Quiere reunion"}'}}]})
        with patch.dict(os.environ, {"GROQ_API_KEY": "key"}), patch("src.qualification.llm_qualifier.requests.post", return_value=response):
            result = classify_reply("Me interesa manana", {"brand_id": "Brand_X"})
        self.assertEqual(result.suggested_action, "agendar")

    def test_llm_research_and_draft_writer_use_groq_payloads(self):
        response = _Response({"choices": [{"message": {"content": "Perfil sintetico"}}]})
        with patch.dict(os.environ, {"GROQ_API_KEY": "key"}), patch("src.enrichment.llm_research.requests.post", return_value=response):
            profile = synthesize_company_profile({"name": "Casa"})
        self.assertEqual(profile, "Perfil sintetico")

        response = _Response({"choices": [{"message": {"content": "Email borrador"}}]})
        with patch.dict(os.environ, {"GROQ_API_KEY": "key"}), patch("src.qualification.draft_writer.requests.post", return_value=response):
            draft = draft_outreach_email({"name": "Casa"}, "Perfil")
        self.assertEqual(draft, "Email borrador")

    def test_apify_normalization_and_request(self):
        run_input = hogar_colombia_input()
        self.assertTrue(run_input["hasEmail"])
        item = {
            "organization": {"name": "Casa Viva", "domain": "casaviva.co", "industry": ["Retail", "Home"], "country": "Colombia", "city": "Bogota"},
            "name": "Laura Perez",
            "title": "CEO",
            "email": "laura@casaviva.co",
            "phone": "+571234",
            "linkedinUrl": "linkedin.com/in/laura",
        }
        prospect = normalize_company(item)
        self.assertEqual(prospect.name, "Casa Viva")
        self.assertEqual(prospect.industry, "Retail, Home")
        self.assertEqual(first_present({"a": ""}, {"a": "ok"}, keys=("a",)), "ok")

        with patch.dict(os.environ, {"APIFY_API_TOKEN": "token"}), patch("src.enrichment.apify_apollo_scraper.requests.post", return_value=_Response([item])) as post:
            prospects = run_apollo_organizations_scraper({"totalResults": 1}, max_results=1)
        self.assertEqual(len(prospects), 1)
        post.assert_called_once()

    def test_apollo_client_and_draft_message(self):
        payload = {
            "people": [
                {
                    "name": "Carlos",
                    "title": "Head Ecommerce",
                    "email": "carlos@example.com",
                    "phone_numbers": [{"raw_number": "+571"}],
                    "organization": {"name": "Casa"},
                }
            ]
        }
        with patch.dict(os.environ, {"APOLLO_API_KEY": "key"}), patch("src.enrichment.apollo_client.requests.post", return_value=_Response(payload)):
            people = search_people(organization_domains=["casa.co"], titles=["CEO"])
        self.assertEqual(people[0].organization, "Casa")
        self.assertIn("Casa", draft_message({"category": "Hogar", "gmv_cop_millions_12m": 10}, people[0]))

    def test_slack_handoff_dry_and_live_mock(self):
        brand = {"brand_id": "Brand_X", "tier": "B", "contacto_email": "a@b.co", "contacto_whatsapp": "+57", "category": "Hogar"}
        classification = {"suggested_action": "agendar", "intent_score": 90}
        self.assertTrue(extract_meeting_times("Opcion 1: martes 3pm"))

        dry = post_handoff(brand, classification, "Opcion 1: martes 3pm", dry_run=True)
        self.assertTrue(dry["dry_run"])

        with patch.dict(os.environ, {"SLACK_WEBHOOK_URL": "https://hooks.slack.test"}), patch("src.handoff.slack_service.requests.post", return_value=_Response({"ok": True}, status_code=200)) as post:
            sent = post_handoff(brand, classification, "Reply", dry_run=False)
        self.assertTrue(sent["sent"])
        post.assert_called_once()


if __name__ == "__main__":
    unittest.main()
