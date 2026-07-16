import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.agents.prospecting_graph import build_prospecting_graph
from src.enrichment.apify_apollo_scraper import CompanyProspect


class ProspectingGraphTest(unittest.TestCase):
    def test_graph_validates_dedupes_exports_and_registers(self):
        prospect = CompanyProspect(
            name="Casa Test",
            domain="casatest.co",
            industry="Furniture",
            country="Colombia",
            city="Bogota",
            contact_name="Ana Gomez",
            contact_title="CEO",
            contact_email="ana@casatest.co",
            contact_phone="+571234567",
            linkedin_url="linkedin.com/in/ana",
            raw={},
        )
        graph = build_prospecting_graph()
        with tempfile.TemporaryDirectory() as tmpdir, patch(
            "src.agents.prospecting_nodes.run_apollo_organizations_scraper",
            return_value=[prospect],
        ), patch("src.agents.prospecting_nodes.repository.prospect_exists", return_value=False), patch(
            "src.agents.prospecting_nodes.synthesize_company_profile", return_value="Perfil breve."
        ), patch("src.agents.prospecting_nodes.draft_outreach_email", return_value="Borrador email."), patch(
            "src.agents.prospecting_nodes.repository.save_prospect_consultation"
        ) as save_prospect, patch("src.agents.prospecting_nodes.ROOT", Path(tmpdir)):
            result = graph.invoke({"run_input": {"totalResults": 1}, "max_results": 1, "log": []})

        self.assertEqual(len(result["enriched_rows"]), 1)
        self.assertTrue(result["output_path"].endswith("data\\test2_prospectos_apify.xlsx") or result["output_path"].endswith("data/test2_prospectos_apify.xlsx"))
        self.assertIn("campos completos", "\n".join(result["log"]))
        save_prospect.assert_called_once()


if __name__ == "__main__":
    unittest.main()
