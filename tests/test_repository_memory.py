import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.db import repository
from src.db.models import connect


class RepositoryMemoryTest(unittest.TestCase):
    def test_agent_interactions_are_saved_and_searchable(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "agent_memory.sqlite3"

            def connect_tmp():
                return connect(db_path)

            with patch("src.db.repository.connect", connect_tmp):
                repository.save_agent_interaction(
                    run_id="run-1",
                    source="notebook_06",
                    event_type="reply_clasificado",
                    brand_id="Brand_TEST",
                    content="El cliente quiere agendar el martes a las 3pm.",
                    metadata={"suggested_action": "agendar", "intent_score": 90},
                )

                latest = repository.list_agent_interactions(limit=5)
                hits = repository.search_agent_interactions("martes", limit=5)

        self.assertEqual(len(latest), 1)
        self.assertEqual(latest[0]["brand_id"], "Brand_TEST")
        self.assertEqual(len(hits), 1)
        self.assertIn("agendar", hits[0]["metadata_json"])


if __name__ == "__main__":
    unittest.main()
