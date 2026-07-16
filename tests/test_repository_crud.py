import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.db import repository
from src.db.models import connect


class RepositoryCrudTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db_path = Path(self.tmp.name) / "agent_memory.sqlite3"

        def connect_tmp():
            return connect(self.db_path)

        self.connect_patch = patch("src.db.repository.connect", connect_tmp)
        self.connect_patch.start()

    def tearDown(self):
        self.connect_patch.stop()
        self.tmp.cleanup()

    def test_lead_reply_opt_in_and_prospect_crud(self):
        repository.upsert_lead(
            "Brand_CRUD",
            category="Hogar",
            gmv_cop_millions_12m=100.0,
            tier="B",
            contacto_email="lead@example.com",
            contacto_whatsapp="+573001112233",
        )
        lead = repository.get_lead("Brand_CRUD")
        self.assertEqual(lead["category"], "Hogar")
        self.assertFalse(repository.was_contacted_recently("Brand_CRUD"))

        repository.mark_contacted("Brand_CRUD", thread_id="thread-1")
        self.assertTrue(repository.was_contacted_recently("Brand_CRUD"))

        repository.save_reply("Brand_CRUD", "Me interesa agendar", {"suggested_action": "agendar"})
        replies = repository.list_replies("Brand_CRUD")
        self.assertEqual(len(replies), 1)
        self.assertIn("agendar", replies[0]["clasificacion_json"])

        self.assertFalse(repository.has_opt_in("Brand_CRUD", "whatsapp"))
        repository.grant_opt_in("Brand_CRUD", "whatsapp")
        self.assertTrue(repository.has_opt_in("Brand_CRUD", "whatsapp"))
        repository.revoke_opt_in("Brand_CRUD", "whatsapp")
        self.assertFalse(repository.has_opt_in("Brand_CRUD", "whatsapp"))

        prospect = {
            "name": "Casa CRUD",
            "domain": "casacrud.co",
            "industry": "Retail",
            "country": "Colombia",
            "city": "Bogota",
            "contact_name": "Ana",
            "contact_title": "CEO",
            "contact_email": "ana@casacrud.co",
            "contact_phone": "+571234",
            "linkedin_url": "linkedin.com/in/ana-crud",
            "profile": "Perfil",
            "draft_email": "Borrador",
        }
        self.assertFalse(repository.prospect_exists(contact_email=prospect["contact_email"]))
        repository.save_prospect_consultation(prospect)
        self.assertTrue(repository.prospect_exists(contact_email=prospect["contact_email"]))


if __name__ == "__main__":
    unittest.main()
