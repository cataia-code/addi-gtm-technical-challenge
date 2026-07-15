import unittest

from src.handoff.slack_service import build_handoff_blocks, extract_meeting_times


class SlackServiceTest(unittest.TestCase):
    def test_extract_meeting_times_from_prefilled_reply(self):
        reply = """Hola equipo Addi,

Si me interesa revisar la oportunidad de Addi Marketplace.

Mis horarios sugeridos para una llamada de 20 minutos son:
- Opcion 1: martes 3pm
- Opcion 2: jueves 10am
- Opcion 3:
"""

        self.assertEqual(
            extract_meeting_times(reply),
            [
                "Mis horarios sugeridos para una llamada de 20 minutos son:",
                "Opcion 1: martes 3pm",
                "Opcion 2: jueves 10am",
                "Opcion 3:",
            ],
        )

    def test_build_handoff_blocks_is_compact_and_reply_first(self):
        brand = {
            "brand_id": "Brand_0145",
            "category": "Moda",
            "contacto_email": "cliente@example.com",
            "contacto_whatsapp": "+573228250742",
            "gmv_cop_millions_12m": 4908,
            "tier": "B",
            "final_score": 95.1,
            "gmv_90d_to_12m_ratio": 1.3,
        }
        classification = {
            "intent_score": 90,
            "suggested_action": "agendar",
            "reasoning": "Quiere revisar la oportunidad y propuso horarios.",
        }
        reply = "Si me interesa.\n- Opcion 1: martes 3pm"

        blocks = build_handoff_blocks(
            brand,
            classification,
            reply,
            ["listener: Gmail"],
            action_taken="WhatsApp enviado + handoff Slack",
            timestamp="2026-07-15T17:30:00",
        )
        rendered = str(blocks)

        self.assertIn("cliente@example.com", rendered)
        self.assertIn("+573228250742", rendered)
        self.assertIn("Opcion 1: martes 3pm", rendered)
        self.assertIn("WhatsApp enviado + handoff Slack", rendered)
        self.assertIn("*Reply:*", rendered)
        self.assertNotIn("*GMV 12m:*", rendered)
        self.assertNotIn("*Score:*", rendered)
        self.assertLessEqual(len(blocks), 5)


if __name__ == "__main__":
    unittest.main()
