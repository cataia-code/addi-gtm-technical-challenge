import ast
import unittest
from pathlib import Path

from src.enrichment.apify_apollo_scraper import hogar_colombia_input, normalize_company


class ApifyProspectingGateTest(unittest.TestCase):
    def test_hogar_colombia_input_is_bounded(self):
        run_input = hogar_colombia_input()

        self.assertEqual(run_input["number_of_pages_to_scrape"], 1)
        self.assertIn("Colombia", run_input["organization_locations"])
        self.assertIn("home decor", run_input["organization_industries"])

    def test_normalize_company_handles_common_actor_fields(self):
        company = normalize_company(
            {
                "organization_name": "Casa Test",
                "domain": "casatest.co",
                "industry": "Retail",
                "city": "Bogota",
                "country": "Colombia",
            }
        )

        self.assertEqual(company.name, "Casa Test")
        self.assertEqual(company.domain, "casatest.co")
        self.assertEqual(company.industry, "Retail")

    def test_test2_script_does_not_import_live_outreach_services(self):
        script_path = Path("live_demo/test2_prospeccion_apify_gate.py")
        tree = ast.parse(script_path.read_text(encoding="utf-8"))
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                imports.append(node.module or "")

        forbidden = {"src.outreach.email_service", "src.outreach.whatsapp_service"}
        self.assertTrue(forbidden.isdisjoint(set(imports)))


if __name__ == "__main__":
    unittest.main()
