# Import Checklist

## Antes de importar

- `GROQ_API_KEY` está presente en `.env`
- `analysis/top50.csv` existe en el entorno de n8n
- `SLACK_WEBHOOK_URL` está configurada

## Importar

1. Importa `DEMO-WF3-outreach.json`
2. Importa `DEMO-WF4-calificacion.json`
3. Importa `DEMO-WF5-handoff.json`

## Verificar

- WF-4 apunta a Groq
- WF-5 no pide credencial real de Salesforce
- WF-1/WF-2 escriben CSV local

## Troubleshooting

- Si WF-4 falla, revisa `GROQ_API_KEY`
- Si WF-1 falla, confirma que `analysis/top50.csv` esté montado en n8n
- Si WF-5 falla, revisa los logs del nodo Code
