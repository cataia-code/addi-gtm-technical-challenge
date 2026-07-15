# Runbook demo real controlada

## Precondiciones

- `.env` local con `GROQ_API_KEY`, `SLACK_WEBHOOK_URL`, `DEMO_EMAIL_DESTINO`,
  `DEMO_WHATSAPP_NUMBER`, `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN` y
  `TWILIO_WHATSAPP_FROM`.
- `credentials.json` y `token.json` locales para Gmail. No deben subirse a Git.
- Opt-in explicito para el numero de WhatsApp de prueba. En sandbox de Twilio,
  el usuario debe haber enviado el mensaje `join ...` requerido por Twilio.

## Prueba 1 - E2E con top50 controlado

Marca sugerida: `Brand_0145` porque ya fue usada en n8n y tiene Tier B alto.

Flujo esperado:

1. Cargar fila real de `analysis/top50.csv`.
2. Usar `DEMO_EMAIL_DESTINO` como email del contacto controlado.
3. Enviar email D0 real por Gmail.
4. Responder desde el inbox controlado con un texto de interes.
5. Clasificar reply con Groq.
6. Verificar opt-in WhatsApp.
7. Enviar WhatsApp real por Twilio solo si existe opt-in.
8. Enviar handoff a Slack con Block Kit.

Casos minimos:

- Interes claro: debe terminar en `agendar` y handoff Hunter.
- Objecion: debe terminar en `nurture` y no enviar WhatsApp.
- Opt-out: debe terminar en `descartar` y bloquear WhatsApp.

## Prueba 2 - Apollo/Clay sin contacto automatico

Objetivo: obtener posibles contactos y crear borradores, no enviar mensajes.

Reglas:

- Apollo/Clay solo puede devolver prospectos y metadatos.
- El LLM puede generar un borrador contextual.
- Ningun email ni WhatsApp se envia a terceros sin aprobacion humana explicita.
- Si el contacto no tiene email/telefono verificable, no se activa outreach.

## Comandos de validacion local

```powershell
.\.venv\Scripts\python.exe -m compileall src live_demo
.\.venv\Scripts\python.exe -m src.scoring.compute_score
.\.venv\Scripts\python.exe live_demo\run_controlled_demo.py
```

## Estado actual validado

- Compilacion Python: PASS.
- Scoring modular contra `analysis/top50.csv`: PASS.
- Demo dry-run:
  - `Brand_0002`: brief Hunter Tier A.
  - `Brand_0145`: clasifica `agendar` y prepara handoff.
  - `Brand_0826`: detecta opt-out y bloquea WhatsApp.

