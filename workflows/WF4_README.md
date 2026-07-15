# WF-4: Calificación (Groq API)

## Resumen

WF-4 recibe replies por webhook, llama a Groq con `llama-3.3-70b-versatile`, y devuelve una clasificación JSON.

## Configuración

- Endpoint: `https://api.groq.com/openai/v1/chat/completions`
- Header: `Authorization: Bearer {{ $env.GROQ_API_KEY }}`
- Model: `llama-3.3-70b-versatile`
- Temperature: `0`

## Entrada

- `brand_id`
- `category`
- `gmv_cop_millions_12m`
- `gmv_90d_to_12m_ratio`
- `final_score`
- `contacto_nombre`
- `reply_text`
- `reply_date`

## Salida

```json
{
  "intent_score": 85,
  "is_decision_maker": true,
  "objection_type": null,
  "suggested_action": "agendar",
  "reasoning": "Explicit interest, ready for demo."
}
```

## Routing

- `intent_score >= 70` -> WF-5
- `40 <= intent_score < 70` -> nurture local log
- `intent_score < 40` -> discard local log
