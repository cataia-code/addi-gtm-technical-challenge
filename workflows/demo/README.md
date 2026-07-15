# Demo Workflows

Este paquete contiene versiones de demo para validar el flujo con datos reales y sin credenciales bloqueantes.

## Incluye

1. `DEMO-WF3-outreach.json`
2. `DEMO-WF4-calificacion.json`
3. `DEMO-WF5-handoff.json`

## Cambios clave

- WF-4 usa Groq.
- WF-5 simula Salesforce en un nodo Code y solo loggea el payload.
- WF-1 y WF-2 escriben staging local en CSV.

## Variables

- `GROQ_API_KEY`
- `SLACK_WEBHOOK_URL`
- `CLAY_API_KEY` si quieres ejecutar enrichment real

## Ruta de entrada

- `analysis/top50.csv`
