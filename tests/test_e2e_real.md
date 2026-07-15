# Test E2E real

- `2026-07-15T17:04:17` Inicio E2E real controlado Brand_0145.
- `2026-07-15T17:04:17` Lead insertado en SQLite y opt_in WhatsApp registrado.
- `2026-07-15T17:04:18` Email D0 HTML enviado por Gmail. message_id=19f67cf1b85c9535 thread_id=19f67cf1b85c9535
- `2026-07-15T17:04:18` Iniciando listener Gmail: polling cada 15 segundos esperando reply unread en el thread.
- `2026-07-15T17:11:25` Recuperacion E2E: buscando reply demo desde thread_id=19f67cf1b85c9535 after_epoch_ms=1784153053000.
- `2026-07-15T17:11:42` Reply recuperado y clasificado. decision=agendar classification={"intent_score": 90, "is_decision_maker": true, "objection_type": null, "suggested_action": "agendar", "reasoning": "El merchant muestra interés claro en revisar la oportunidad y proporciona horarios para una llamada", "es_opt_out": false}
- `2026-07-15T17:11:43` WhatsApp enviado via Twilio SDK. sid=MM6f800a9443bab1fd7869dac3829cdc0a status=queued
- `2026-07-15T17:12:00` Verificacion Twilio fetch: sid=MM6f800a9443bab1fd7869dac3829cdc0a status=delivered error_code=None error_message=None
- `2026-07-15T17:11:44` Slack Block Kit final enviado. action_taken=WhatsApp template enviado via Twilio SDK + handoff Slack
- `2026-07-15T17:11:44` Recuperacion E2E completada.
- `2026-07-15T17:23:00` Correccion: email HTML reenviado con CTA Gmail Compose corregido. message_id=19f67dafafa37a6d thread_id=19f67dafafa37a6d
- `2026-07-15T17:23:08` Correccion: WhatsApp en espanol enviado por Body via Twilio SDK. sid=SM2aa3d81bfed1cbf6d323f8d8e9b89810 status=delivered error_code=None
- `2026-07-15T17:20:51` Recuperacion E2E: buscando reply demo desde thread_id=19f67dafafa37a6d after_epoch_ms=1784153832000.
- `2026-07-15T17:21:09` Reply recuperado y clasificado. decision=agendar classification={"intent_score": 90, "is_decision_maker": true, "objection_type": null, "suggested_action": "agendar", "reasoning": "El merchant muestra interés claro en revisar la oportunidad y proporciona horarios para una llamada", "es_opt_out": false}
- `2026-07-15T17:21:10` WhatsApp enviado via Twilio SDK. sid=SM0cc7e18a41c2ec4e0cbe4c03a6d1c1b8 status=queued
- `2026-07-15T17:21:18` Verificacion Twilio fetch: sid=SM0cc7e18a41c2ec4e0cbe4c03a6d1c1b8 status=delivered error_code=None error_message=None
- `2026-07-15T17:21:10` Slack Block Kit final enviado. action_taken=WhatsApp en espanol enviado via Twilio SDK + handoff Slack
- `2026-07-15T17:21:10` Recuperacion E2E completada.
