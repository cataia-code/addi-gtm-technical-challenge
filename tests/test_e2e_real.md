# Test E2E real

- `2026-07-15T17:58:28` Inicio E2E real controlado Brand_0145.
- `2026-07-15T17:58:28` Lead insertado en SQLite y opt_in WhatsApp registrado.
- `2026-07-15T17:58:29` Email D0 HTML enviado por Gmail. message_id=19f6800b406a0773 thread_id=19f6800b406a0773
- `2026-07-15T17:58:29` Iniciando listener Gmail: polling cada 15 segundos esperando reply unread en el thread.
- `2026-07-15T17:59:52` Reply detectado y procesado por LangGraph. decision=agendar classification={"intent_score": 90, "is_decision_maker": true, "objection_type": null, "suggested_action": "agendar", "reasoning": "El merchant muestra interés claro y propone una fecha y hora para una llamada", "es_opt_out": false}
- `2026-07-15T17:59:52` LangGraph whatsapp_result={"sent": true, "status": "queued", "sid": "SM5b151cd5aa37e3ebf2e794686d0f0d5d", "error_code": null}
- `2026-07-15T18:00:00` Verificacion Twilio fetch: sid=SM5b151cd5aa37e3ebf2e794686d0f0d5d status=delivered error_code=None error_message=None
- `2026-07-15T17:59:52` LangGraph Slack handoff ejecutado por nodo_handoff_*.
- `2026-07-15T17:59:52` E2E real con LangGraph completado.
