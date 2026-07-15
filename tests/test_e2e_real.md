# Test E2E real

- `2026-07-15T17:34:06` Inicio E2E real controlado Brand_0145.
- `2026-07-15T17:34:06` Lead insertado en SQLite y opt_in WhatsApp registrado.
- `2026-07-15T17:34:08` Email D0 HTML enviado por Gmail. message_id=19f67ea6b4659596 thread_id=19f67ea6b4659596
- `2026-07-15T17:34:08` Iniciando listener Gmail: polling cada 15 segundos esperando reply unread en el thread.
- `2026-07-15T17:35:40` Reply detectado y clasificado. decision=agendar classification={"intent_score": 90, "is_decision_maker": true, "objection_type": null, "suggested_action": "agendar", "reasoning": "El merchant muestra interés claro en revisar la oportunidad y proporciona horarios para una llamada", "es_opt_out": false}
- `2026-07-15T17:35:42` WhatsApp en espanol aceptado por Twilio. sid=SMa07a6bee1d536e385058b9439676fd13 Nota: en Sandbox, entrega final requiere que el destino haya enviado el join code correcto.
- `2026-07-15T17:35:48` Verificacion Twilio fetch: sid=SMa07a6bee1d536e385058b9439676fd13 status=delivered error_code=None error_message=None
- `2026-07-15T17:35:42` Slack Block Kit final enviado. action_taken=WhatsApp en espanol aceptado por Twilio + handoff Slack
- `2026-07-15T17:35:42` E2E real completado.
- `2026-07-15T17:40:00` Slack reenviado con reply en bloque de codigo para preservar cuerpo multilinea completo. message_id=19f67ec26531139b
