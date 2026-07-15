# Plan de accion - Addi GTM Engineer

## Objetivo

Construir una prueba defendible de una motion GTM asistida por AI para Marketplace:
segmentacion de cuentas BNPL x-sell, enrichment controlado, outreach, calificacion,
handoff a Hunter y evidencia de compliance.

## Principios de ejecucion

1. No enviar mensajes reales a terceros desconocidos sin aprobacion humana explicita.
2. Probar E2E primero con datos reales de `analysis/top50.csv`, pero usando el email y
   WhatsApp del usuario como destino controlado.
3. Mantener n8n como evidencia de arquitectura visual existente, mientras se construye
   una base Python modular mas facil de probar.
4. Usar Slack Block Kit como canal de visibilidad y aprobacion. Slack no renderiza HTML.
5. Registrar cada decision en logs locales para poder explicar el flujo en la defensa.

## Fase 0 - Seguridad y checkpoint

Estado: iniciado.

- Crear `.gitignore` para excluir `.env`, `credentials.json`, `token.json` y bases locales.
- Crear `.env.example` sin valores reales.
- Detectar que `.git` esta incompleto/vacio; antes de hacer push se debe correr `git init`
  limpio y auditar que no se incluyan secretos.

## Fase 1 - Modularizacion Python

Estado: iniciado.

Entregables:

- `src/scoring/compute_score.py`: calcula y valida top 50 contra el dataset.
- `src/qualification/llm_qualifier.py`: clasificador Groq con enum estricto
  `agendar|nurture|descartar`.
- `src/outreach/email_service.py`: Gmail API con email HTML.
- `src/outreach/whatsapp_service.py`: Twilio WhatsApp con gate de opt-in.
- `src/handoff/slack_service.py`: handoff enriquecido en Slack Block Kit.
- `src/db/*`: SQLite para leads, replies, opt-ins y contact log.

## Fase 2 - Demo E2E controlada

Objetivo: una fila real de `top50.csv` se modifica en runtime con email y telefono del
usuario. El sistema envia email real, espera o recibe reply, clasifica con Groq, valida
opt-in, envia WhatsApp real por Twilio y hace handoff a Slack/Hunter.

Criterios PASS:

- El email D0 llega al inbox controlado.
- El reply se clasifica con JSON valido y `suggested_action` normalizado.
- WhatsApp solo se envia si hay opt-in registrado.
- Slack recibe brief Hunter con datos reales, reply, clasificacion y razonamiento.
- El flujo opt-out bloquea WhatsApp y deja evidencia.

## Fase 3 - LangGraph

Objetivo: demostrar agentes Hunter y SDR con estado compartido.

Rutas:

- Tier A: brief Hunter, sin outreach automatico.
- Tier B: duplicate check, email D0, reply, LLM qualification, router, WhatsApp gate,
  Slack handoff.

## Fase 4 - Enrichment Apollo/Clay seguro

Objetivo: buscar prospectos potenciales sin contactar automaticamente.

Regla: Apollo/Clay solo genera candidatos y borradores. Ningun correo o WhatsApp sale a
terceros hasta aprobacion humana.

Entregables:

- `src/enrichment/apollo_client.py`
- fixture local de ejemplo
- borrador de mensaje con fuentes y razonamiento

## Fase 5 - Notebooks y documento

Entregables:

- Notebook diagnostico S1->S2.
- Notebook scoring y sensibilidad.
- Notebook eval LLM con matriz de confusion.
- Documento final del business case.
- `qa_prep.md` con preguntas duras y respuestas ancladas a numeros.

