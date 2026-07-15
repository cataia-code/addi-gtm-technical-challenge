# Demo Script

## Mensaje base

> "Hoy voy a mostrar el flujo de Addi Marketplace con n8n usando datos reales de `analysis/top50.csv`, clasificación con Groq y handoff simulado sin Salesforce real."

## Orden

1. WF-1: lectura real de `analysis/top50.csv`
2. WF-2: enrichment
3. WF-4: clasificación con Groq
4. WF-5: handoff simulado y log local

## Puntos clave

- Groq usa `llama-3.3-70b-versatile`
- Salesforce en demo se imprime como payload local
- Slack sigue siendo la notificación visible

## Cierres

- Interest: `agendar`
- Objection: `nurture`
- Opt-out: `descartar`
