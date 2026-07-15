import unittest
from unittest.mock import patch

from live_demo.whatsapp_listener import handle_inbound_whatsapp


class WhatsAppListenerTest(unittest.TestCase):
    def test_inbound_whatsapp_classifies_and_posts_handoff_dry_run(self):
        brand = {"brand_id": "Brand_0145", "tier": "B", "category": "Moda"}
        classification = {
            "intent_score": 85,
            "suggested_action": "agendar",
            "reasoning": "Quiere conversar.",
        }

        with patch("src.agents.nodes.classify_reply") as classify_reply, patch(
            "live_demo.whatsapp_listener.post_handoff"
        ) as post_handoff:
            classify_reply.return_value.as_dict.return_value = classification
            state = handle_inbound_whatsapp(
                {"From": "whatsapp:+573228250742", "Body": "Si, agendemos", "MessageSid": "SM_test"},
                brand,
            )

        self.assertEqual(state["decision"], "agendar")
        self.assertEqual(state["reply_recibido"], "Si, agendemos")
        post_handoff.assert_called_once()
        self.assertTrue(post_handoff.call_args.kwargs["dry_run"])


if __name__ == "__main__":
    unittest.main()
