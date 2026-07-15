import unittest
from unittest.mock import patch

from src.agents.graph import build_reply_graph


class _Qualification:
    def as_dict(self):
        return {
            "intent_score": 90,
            "is_decision_maker": True,
            "objection_type": None,
            "suggested_action": "agendar",
            "reasoning": "Quiere agendar.",
        }


class _WhatsAppResult:
    sent = True
    reason = "sent"
    provider_response = {"sid": "SM_test", "status": "queued", "error_code": None}


class ReplyGraphTest(unittest.TestCase):
    def test_reply_graph_agendar_sends_whatsapp_and_posts_slack(self):
        graph = build_reply_graph()
        state = {
            "brand_data": {
                "brand_id": "Brand_0145",
                "tier": "B",
                "category": "Hogar",
                "contacto_email": "cliente@example.com",
                "contacto_whatsapp": "+573228250742",
            },
            "tier": "B",
            "ya_contactado": True,
            "reply_recibido": "Si me interesa. Opcion 1: martes 3pm",
            "clasificacion": None,
            "decision": "",
            "log_razonamiento": [],
            "dry_run": False,
            "whatsapp_result": None,
        }

        with patch("src.agents.nodes.classify_reply", return_value=_Qualification()), patch(
            "src.agents.nodes.repository.has_opt_in", return_value=True
        ), patch("src.agents.nodes.send_whatsapp", return_value=_WhatsAppResult()) as send_whatsapp, patch(
            "src.agents.nodes.post_handoff"
        ) as post_handoff:
            result = graph.invoke(state)

        self.assertEqual(result["decision"], "agendar")
        self.assertEqual(result["whatsapp_result"]["sid"], "SM_test")
        send_whatsapp.assert_called_once()
        post_handoff.assert_called_once()
        self.assertIn("nodo_enviar_whatsapp_agendar", "\n".join(result["log_razonamiento"]))


if __name__ == "__main__":
    unittest.main()
