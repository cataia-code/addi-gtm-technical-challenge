# Test E2E real

- `2026-07-15T16:43:50` Inicio E2E real controlado Brand_0145.
- `2026-07-15T16:43:50` Lead insertado en SQLite y opt_in WhatsApp registrado.
- `2026-07-15T16:43:51` Email D0 HTML enviado por Gmail. message_id=19f67bc6447f9d8f thread_id=19f67bc6447f9d8f
- `2026-07-15T16:43:51` Iniciando listener Gmail: polling cada 15 segundos esperando reply unread en el thread.
- `2026-07-15T16:43:53` Reply detectado y clasificado. decision=agendar classification={"intent_score": 90, "is_decision_maker": false, "objection_type": null, "suggested_action": "agendar", "reasoning": "El merchant muestra interés en revisar la oportunidad de llevar su demanda al Marketplace", "es_opt_out": false}
- `2026-07-15T16:43:54` WhatsApp real enviado por Twilio. sid=SM8ba065eb34bfc19d12bfea06afdc391d
- `2026-07-15T16:43:55` Slack Block Kit final enviado. action_taken=WhatsApp real enviado + handoff Slack
- `2026-07-15T16:43:55` E2E real completado.
