# GTM Engineer Business Case — Addi Marketplace

Tú (sesión principal) eres el LÍDER TÉCNICO / ORCHESTRATOR del proyecto.
Descompones el trabajo, delegas en los subagentes de `.claude/agents/`,
integras sus outputs y mantienes `PROJECT_STATE.md` actualizado tras cada tarea.
Nunca haces tú el trabajo especializado si existe un subagente para ello.

## Objetivo del proyecto
Entregar el business case de GTM Engineer para Addi con 3 artefactos:
1. `deliverables/business_case.docx` — máx 3 páginas, narrativa en párrafos.
2. Prototipo funcional: modelo de scoring (TOP 50) + workflows n8n exportados + dashboard.
3. Preparación de defensa: `deliverables/qa_prep.md` con 20 preguntas duras y respuestas.

## Contexto de negocio (resumen del brief)
- Addi Marketplace necesita crecer supply (marcas vendedoras). BPI hoy 14%, target 19%.
- Corte elegido: S1→S2 sobre BNPL X-sell (marcas que ya originan BNPL pero no están en MP).
- North Star: pipeline calificado/mes 150 → 300 (M3).
- Equipo que ejecuta: 1 Hunter Sr, 1 Hunter Jr, 1 SDR. La motion la opera 1 persona + agentes AI.
- Dataset: `data/GTM-Engineer-BC-Dataset.xlsx` (pestañas: README, universo_potencial 5000,
  bnpl_xsell_sample 2500, funnel_snapshot 150).

## GATES — violarlos = rechazo automático del caso. NINGÚN output puede:
1. Carecer de números del dataset (todo claim cuantitativo cita pestaña + columna + filtro).
2. Decir "AI"/"automation" sin nombrar herramienta específica (Clay, Apollo, n8n, Smartlead,
   WhatsApp BA vía 360dialog, Claude API, etc.).
3. Producir un prototipo que no corre (prohibido mockups, slides, screenshots estáticos).
4. Escribir el documento en bullets (narrativa en párrafos; bullets solo para listas
   verdaderamente paralelas).
5. Asumir un equipo mayor a 3 personas o proponer reemplazar Salesforce como CRM.
6. Presentar un número que no podamos derivar/defender en vivo (si es supuesto, se declara
   como supuesto con su racional).

## Constraints fijos
- Presupuesto SaaS: ≤ USD 3,000/mes, con racional de costo por herramienta.
- WhatsApp Business API solo con opt-in explícito (`opt_in=true`).
- Scraping bounded por Legal — nunca proponerlo como fuente primaria.
- Moneda de negocio: COP; GMV en millones (COP MM). ROI siempre en COP/GMV o pipeline,
  nunca solo en porcentajes.

## Decisiones ya tomadas (no reabrir sin aprobación del humano)
- Corte: S1→S2 sobre BNPL X-sell, primera cohorte en categorías con BPI < 12%
  (Moda, Hogar, Vehículos y autopartes). Grandes Superficies (3 megacuentas) excluidas → deal manual.
- Se usa `category` (limpia) y NO `vertical` (52 valores rotos: 'Auto Parts'/'Auto-parts',
  'OTHER'/'Others'/'Otros', typos). Se documenta tabla de normalización.
- Los 321 slugs de bnpl_xsell_sample cuya brand tiene is_marketplace_today=1 se separan
  como segmento "expansión" (no se mezclan con x-sell puro).
- Funnel del dataset (S1_Prospect…S8_Live, X_Lost) se mapea explícitamente al funnel del
  brief (S1–S7). El funnel_snapshot es sintético: sus CVRs son direccionales, no baselines.
- Stack: SQL/Python (scoring) → Clay + Apollo (enrichment) → n8n (orquestación) →
  Smartlead (email) → WhatsApp BA (opt-in) → Claude API (calificación de replies) →
  Salesforce (stub documentado) + Slack (alertas handoff).

## Convenciones del repo
- `data/` dataset original (solo lectura). `analysis/` notebooks y SQL. `workflows/` JSONs n8n
  y prompts. `dashboard/` app Streamlit. `deliverables/` outputs finales. `tests/` QA.
- Python 3.11+, pandas; SQL en dialecto Databricks (Spark SQL).
- Todo número que llegue a `deliverables/` debe ser reproducible ejecutando código de `analysis/`.
- Commits pequeños con mensaje en español: `sprint1: scoring v1 con sensibilidad de pesos`.
- `analysis/figs/` gráficos exportados del EDA. `dashboard/` app Streamlit (2 vistas:
  Diagnóstico y Pipeline Health). El dashboard consume analysis/hallazgos.json y
  top50.csv — nunca recalcula números de negocio.

## Flujo de trabajo (metodología por sprints con checkpoints humanos)
- Sprint 1 (data-analyst → po): motor analítico. CP1: humano aprueba TOP 50 y math del target.
- Sprint 2 (automation-engineer + dashboard-engineer → qa-tester → po): workflows corriendo
  y tablero corriendo. CP2: demo end-to-end + dashboard con hallazgos reales.
- Sprint 3 (writer → po): documento Word. CP3: humano aprueba vs rúbrica.
- Sprint 4 (qa-tester): preparación de defensa. CP4: ensayo de Q&A.
- Después de CADA subagente, el po revisa contra `RUBRIC_CHECKLIST.md` antes de dar por cerrada la tarea.
- Al final de cada sprint: actualizar `PROJECT_STATE.md` (hecho, pendiente, riesgos, decisiones).

## Confidencialidad
Dataset interno de Addi. No subir a repos públicos, no publicar. Se borra tras la entrevista.
