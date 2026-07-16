# Addi GTM Technical Challenge

CI/CD: https://github.com/cataia-code/addi-gtm-technical-challenge/actions

Proyecto GTM con scoring validado, agentes LangGraph, demos reales controladas y memoria local en SQLite dentro de `data/`.

## Motion completa

```mermaid
flowchart TD
    A["Dataset fuente<br/>data/GTM-Engineer-BC-Dataset.xlsx"] --> B["Diagnostico S1 -> S2<br/>DuckDB sobre funnel_snapshot"]
    B --> B1["Por que S1 -> S2<br/>dias sin toque por stage<br/>% pipeline estancado<br/>CVR S3+ por source"]
    A --> C["Universo de oportunidad"]
    C --> C1["Filtros MP fit<br/>is_marketplace_today = 0<br/>is_active_90d = 1<br/>excluir categorias no automatizables"]
    C1 --> D["Scoring calculado<br/>src.scoring.compute_score.calcular_score"]

    D --> E["Tier A<br/>Top 15 por GMV 12m"]
    E --> E1["Ruta Hunter Sr / KAM<br/>brief manual a Slack<br/>sin outreach automatico"]

    D --> F["Tier B<br/>Top 35 por score<br/>cap categoria 40%"]
    F --> G["Formula Tier B"]
    G --> G1["fit_score<br/>GMV pct 30/55<br/>clientes pct 15/55<br/>ticket target 275k 10/55"]
    G --> G2["momentum_score<br/>min(gmv90d*4/gmv12m, 2) / 2 * 100"]
    G --> G3["recency_score<br/>exp(-days_since_last_orig / 30) * 100"]
    G --> G4["category_bonus<br/>10 si BPI < 12%<br/>5 si BPI < 19%<br/>0 si BPI >= 19%"]
    G1 --> G5["final_score<br/>0.55 fit + 0.25 momentum + 0.05 recency + bonus"]
    G2 --> G5
    G3 --> G5
    G4 --> G5

    F --> H["Validacion critica<br/>tests/test_scoring_integrity.py"]
    H --> H1["8 asserts<br/>sin duplicados<br/>sin categorias excluidas<br/>Tier A exacto<br/>correlaciones correctas<br/>cap categoria<br/>GMV contra dataset"]
    H --> H2["Comparacion contra analysis/top50.csv<br/>50 final_score con tolerancia 0.1"]

    F --> I["Motion SDR automatizada"]
    I --> J["Chequeo duplicado<br/>src.db.repository<br/>data/agent_memory.sqlite3"]
    J --> K["Email D0 HTML real<br/>src.outreach.email_service<br/>Gmail API"]
    K --> L["Gmail listener real<br/>live_demo.email_listener<br/>wait_for_reply_and_classify"]
    L --> M["LangGraph reply graph<br/>compiled_reply_graph.invoke(state)"]

    M --> N["nodo_clasificar_reply<br/>Groq LLM<br/>suggested_action exacto"]
    N --> O["nodo_router<br/>agendar / nurture / descartar"]
    O -->|agendar| P["Gate WhatsApp<br/>requiere opt-in<br/>bloquea opt-out"]
    P --> Q["Twilio WhatsApp real<br/>src.outreach.whatsapp_service"]
    Q --> R["Slack handoff<br/>Block Kit"]
    O -->|nurture| R
    O -->|descartar u opt-out| S["Slack descarte<br/>WhatsApp bloqueado por compliance"]

    R --> T["Memoria local<br/>agent_interactions<br/>replies<br/>leads<br/>opt_ins"]
    S --> T
    T --> U["Auditoria y demos<br/>notebooks 06 y 07<br/>tests reales documentados"]

    V["Prospeccion externa opcional<br/>notebook 07 / test2"] --> W["Apify por categoria y cantidad"]
    W --> X["Validar campos completos<br/>deduplicar contra SQLite"]
    X --> Y["Groq perfil + borrador<br/>sin enviar a desconocidos"]
    Y --> Z["Excel en data/<br/>test2_prospectos_apify.xlsx"]
    Z --> T
```

## Arquitectura

```text
analysis/
  top50.csv                         Ranking oficial versionado
  validation_report.md              Resumen de validacion en espanol
data/
  GTM-Engineer-BC-Dataset.xlsx      Dataset fuente preservado
  agent_memory.sqlite3              Runtime local ignorado por git
  test2_prospectos_apify.xlsx       Export de prospeccion
live_demo/
  test1_e2e_real.py                 Gmail -> listener -> LangGraph -> WhatsApp/Slack
  test2_prospeccion_apify_gate.py   Apify/Groq -> LangGraph -> Excel
  email_listener.py                 Listener Gmail que invoca compiled_reply_graph
notebooks/
  01_diagnostico_seleccion_s1s2.ipynb
  02_scoring_model.ipynb
  04_qualification_llm_eval.ipynb
  05_agente_langgraph_demo.ipynb
  06_demo_e2e_langgraph_real.ipynb
  07_demo_prospeccion_langgraph_excel.ipynb
src/
  agents/                           Grafos y nodos LangGraph
  db/                               SQLite, memoria y repositorio
  enrichment/                       Apify/Apollo y perfiles LLM
  handoff/                          Slack Block Kit
  outreach/                         Gmail y Twilio WhatsApp
  qualification/                    Prompt y clasificador Groq
  scoring/                          Score, constantes y validators
tests/
  test_scoring_integrity.py          Gate CI de los 8 asserts
```

## Notebooks

Ejecutar desde la raiz del repo:

```bash
jupyter notebook
```

- `01_diagnostico_seleccion_s1s2.ipynb`: diagnostico con DuckDB, graficos y conclusion S1 -> S2.
- `02_scoring_model.ipynb`: importa `src.scoring.compute_score.calcular_score`, muestra formula, sensibilidad y asserts.
- `04_qualification_llm_eval.ipynb`: evaluacion real del clasificador con Groq. Requiere `GROQ_API_KEY`.
- `05_agente_langgraph_demo.ipynb`: demo de rutas LangGraph con filas reales.
- `06_demo_e2e_langgraph_real.ipynb`: motion completa: score, imputar email/WhatsApp, grafo legible, email real, listener, WhatsApp y Slack.
- `07_demo_prospeccion_langgraph_excel.ipynb`: prospeccion por categoria/cantidad, deduplicacion y Excel.

## Tests reales

Los dos tests reales usan agentes LangGraph.

### Test 1: E2E outreach real

```bash
python live_demo/test1_e2e_real.py
```

Flujo real:

1. Lee `analysis/top50.csv`.
2. Selecciona `DEMO_BRAND_ID` si existe; si no, toma el mejor Tier B.
3. Imputa `DEMO_EMAIL_DESTINO` y `DEMO_WHATSAPP_NUMBER`.
4. Envia email HTML real por Gmail.
5. `email_listener.py` espera el reply.
6. El listener invoca `compiled_reply_graph.invoke(state)`.
7. LangGraph clasifica con Groq, enruta, aplica opt-in/opt-out, envia WhatsApp si corresponde y postea Slack.

Real: Gmail, Groq, Twilio WhatsApp, Slack.  
Simulado: nada, salvo que `dry_run=True` se pase manualmente en llamadas internas.

### Test 2: prospeccion real a Excel

```bash
python live_demo/test2_prospeccion_apify_gate.py --confirm-run --max-results 3
```

Flujo real:

1. Muestra el input de Apify antes de ejecutar.
2. Invoca `compiled_prospecting_graph.invoke(...)`.
3. LangGraph llama Apify, valida campos completos, deduplica contra SQLite, genera perfil/borrador con Groq y exporta Excel.
4. Registra memoria local en `data/agent_memory.sqlite3`.

Real: Apify y Groq.  
Simulado/no permitido: Slack, email y WhatsApp. Este script no importa servicios de envio.

## Tests y cobertura

```bash
pytest tests/ -v
coverage run --source=src -m pytest tests/
coverage report -m
```

El gate mas importante es:

```bash
pytest tests/test_scoring_integrity.py -v
```

Ese test recalcula el score y falla si se rompe cualquiera de los 8 checks validados: duplicados, categorias excluidas, Tier A exacto, correlaciones, cap de categoria, GMV contra dataset y tolerancia contra `analysis/top50.csv`.

## Variables locales

Las credenciales viven solo en `.env`, que esta ignorado por git. Variables usadas:

```text
GROQ_API_KEY
SLACK_WEBHOOK_URL
DEMO_EMAIL_DESTINO
DEMO_WHATSAPP_NUMBER
TWILIO_ACCOUNT_SID
TWILIO_AUTH_TOKEN
TWILIO_WHATSAPP_FROM
TWILIO_CONTENT_SID
GOOGLE_CLIENT_ID
GOOGLE_CLIENT_SECRET
APIFY_API_TOKEN
```

No subir `.env`, `credentials.json`, `token.json` ni bases SQLite.
