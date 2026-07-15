# PROJECT_STATE.md — GTM Engineer Business Case (Addi Marketplace)

Última actualización: 2026-07-14 (setup inicial, pre-Sprint 1)

## Estado general
Setup verificado. Dataset confirmado y legible. Ningún sprint ejecutado todavía.
Esperando aprobación humana para iniciar Sprint 1.

## Verificación de dataset
`data/GTM-Engineer-BC-Dataset.xlsx` existe y se leyó con pandas (`py -c "..."`, Python 3.13.0 vía launcher `py`; `python`/`python3` no están disponibles en este entorno).

| Pestaña | Shape (filas, cols) | Columnas clave |
|---|---|---|
| README | (38, 2) | descripción del dataset |
| universo_potencial | (5000, 16) | brand_id, category, vertical, cluster, n_slugs, n_originations_12m/90d, gmv_cop_millions_12m/90d, avg_ticket_cop, is_marketplace_today, is_active_90d |
| bnpl_xsell_sample | (2500, 13) | slug_id, brand_id, category, vertical, cluster, n_orig_12m/90d, gmv_cop_millions_12m/90d, is_active_90d |
| funnel_snapshot | (150, 13) | lead_id, brand_id, source, category, cluster, stage, owner, est_mp_gmv_cop_millions_y1, lost_reason |

Coincide con lo esperado en CLAUDE.md (universo_potencial 5000, bnpl_xsell_sample 2500, funnel_snapshot 150).

## Plan de sprints y checkpoints

### Sprint 1 — Motor analítico (data-analyst → po)
- Auditoría de calidad de datos: usar `category` (limpia), documentar tabla de normalización de `vertical` (52 valores rotos, no se usa).
- Separar segmento "expansión" (321 slugs con `is_marketplace_today=1`) del x-sell puro.
- Mapear funnel del dataset (S1_Prospect…S8_Live, X_Lost) al funnel del brief (S1–S7).
- Construir modelo de scoring y TOP 50 (excluyendo las 3 megacuentas de Grandes Superficies).
- Math del target: BPI 14%→19%, pipeline calificado 150→300/mes (M3), con cita de pestaña+columna+filtro para cada número.
- Entregables: notebooks/SQL/CSVs reproducibles en `analysis/`.
- **CP1 (checkpoint humano):** aprobación del TOP 50 y de la matemática del target.

### Sprint 2 — Prototipo funcional (automation-engineer → qa-tester → po)
- 5 workflows n8n: ingesta/scoring, enrichment (Clay+Apollo), outreach multicanal (Smartlead + WhatsApp BA opt-in), calificación de replies (Claude API), handoff (Salesforce stub + Slack).
- JSONs importables en `workflows/`, dashboard funcional en `dashboard/` (Streamlit).
- QA end-to-end: arquetipos de replies, edge cases de datos.
- **CP2 (checkpoint humano):** demo end-to-end funcionando (nada de mockups/slides).

### Sprint 3 — Documento ejecutivo (writer → po)
- `deliverables/business_case.md` → `.docx`, máx 3 páginas, narrativa en párrafos, usa solo números de `analysis/` y `workflows/`.
- **CP3 (checkpoint humano):** aprobación vs `RUBRIC_CHECKLIST.md`.

### Sprint 4 — Preparación de defensa (qa-tester)
- `deliverables/qa_prep.md`: 20 preguntas duras y respuestas defendibles en vivo.
- **CP4 (checkpoint humano):** ensayo de Q&A.

## Regla de proceso
Después de cada subagente, el `po` revisa contra `RUBRIC_CHECKLIST.md` antes de cerrar la tarea. Al final de cada sprint se actualiza este archivo (hecho, pendiente, riesgos, decisiones).

## Hecho
- Lectura completa de CLAUDE.md (objetivo, 6 gates, constraints, decisiones tomadas).
- Verificación de dataset y shapes de las 4 pestañas.
- Creación de PROJECT_STATE.md y RUBRIC_CHECKLIST.md.

### Sprint 1 — Iteración 1 (Rechazada)
- Modelo TOP 50 monolítico rechazado por PO: solo 7.4% GMV capturado, recency binario.

### Sprint 1 — Iteración 2 (Rechazada por arquitectura)
- Modelo 2 tiers (A GMV puro + B scoring) con 20.9% GMV capturado.
- Problema identificado: mezcla universo_potencial (49.3k MM/brand) + bnpl_xsell_sample 
  (254 MM/brand) reduce GMV capturado vs benchmark 46.6%.

### Sprint 1 — Iteración 3 (Bugs críticos encontrados)
- PO identificó 5 bugs: momentum sign, Tier A incompleto, GMVs incorrectos, MP-fit mal aplicado, 
  Tier A sin scores.
- **Correcciones completadas por data-analyst:**
  1. Momentum correlation fix: -0.87 → +0.97 (monotónico creciente) ✓
  2. Tier A completo: Brand_0001 + Brand_0003 (faltaban) ✓
  3. GMVs 1:1 con dataset (8 filas corregidas) ✓
  4. MP-fit filtros aplicados (Educación, Viajes, Salud, Música excluidos) ✓
  5. Tier A con scores calculados (fit, momentum, recencia, categoría) ✓
  
- **Validaciones automáticas: 4/4 pasadas** ✓

### Sprint 1 — Estado Final (v3 Completa)
- **Portafolio TOP 50 final:**
  - Tier A (15 brands): 1,239,401 MM (99.3%), GMV puro, routing KAM/Hunter Sr
  - Tier B (35 brands): 8,682 MM (0.7%), scoring multidimensional, routing Motion/SDR
  - **Total: 1,248,083 MM = 34.9% oportunidad** (vs benchmark 46.6%, gap -11.7pp)
  
- **Modelo scoring Tier B (reproducible):**
  - fit 55% (log GMV 30% + n_unique_clients 15% + ticket_compatible 10%)
  - momentum 25% (gmv_90d×4/gmv_12m, winsorizado 2.0, correlación +0.97)
  - recencia 5% (exp decay suave, no binario)
  - categoría 15% (bono BPI < 12%: +10pp, < 19%: +5pp)
  
- **Entregables finales en `analysis/`:**
  1. `top50.csv` (50 brands, 15 columnas: rank, tier, category, GMV, scores, why, routing)
  2. `scoring_model.py` (reproducible con asserts 4/4 automáticos)
  3. `hallazgos.json` (KPIs estructurados)
  4. `README.md` (documentación)
  5. `FIXES_SUMMARY.md` (detalle de 5 correcciones)
  6. `scoring_model_comparison.md` (análisis iteración 1 vs 3)
  7. `scoring_model_exclusions.md` (MP-fit racional)
  8. `figs/0{1-6}_*.png` (6 gráficos: score dist, GMV tier, concentración, Pareto, Fit vs Momentum, momentum validation)
  
- **Sanity checks reproducidos:**
  - BPI = 716/5000 = 14.3% ✓
  - Oportunidad = 4,175 brands, COP 3,573.7B ✓
  - Candidatos Tier B post-filtros = 1,738 ✓
  - is_active_90d filtro aplicado en ambos tiers ✓
  - Grandes Superficies incluidas en Tier A (deal manual, documentado) ✓
  
- **Gates cumplidos:**
  - Gate 1 (números dataset): ✓ (pestaña + columna + query visible)
  - Gate 2 (herramientas): ✓ (no aplica scoring, aplica en automation)
  - Gate 3 (ejecutable): ✓ (CSV + script reproducible, asserts 4/4)
  - Gate 4 (narrativa): ✓ (reportes con párrafos)
  - Gate 5 (equipo): ✓ (3 personas)
  - Gate 6 (derivable): ✓ (SQL reproducible)

## Sprint 2 EN PROGRESO

### Checkpoint 1 (CP1): ✅ APROBADO
- top50.csv CONGELADO (50 filas: 15 Tier A + 35 Tier B)
- 29.87% GMV capturado (837.5B MM COP)
- 8/8 validaciones pasadas

### Sprint 2A: Automation Engineer (EN PROGRESO)
**Objetivo:** 5 workflows n8n JSON importables en `/workflows/`

**WF-1 ingesta_scoring:**
- Input: top50.csv (leer tal cual)
- Output: Google Sheet (2 tabs: Tier_A, Tier_B)
- Trigger: Cron lunes 6:00 AM COT
- Status: EN CONSTRUCCIÓN

**WF-2 enrichment (cola_B solo):**
- Input: brand_id, category de Tier B
- Output: contacto, email, cargo, LinkedIn URL, CMS
- API: Clay (waterfall Apollo → LinkedIn → scrape)
- Retry: x2 si falla, marcar manual_review si persiste
- Status: EN CONSTRUCCIÓN

**WF-3 outreach (multicanal, cola_B enriquecida):**
- Email d0 → LinkedIn d2 (manual) → WhatsApp d5 (solo si opt_in=true)
- Copy con {{merge_fields}} reales (GMV, momentum, category)
- Branching: abrió 48h sin respuesta → variante B; click → WF-4; 10d sin señal → nurture
- Status: EN CONSTRUCCIÓN

**WF-4 calificación (replies via Smartlead):**
- Claude API (sonnet-4-6, temp=0) con few-shot 7 arquetipos
- Output: {intent_score, is_decision_maker, objection_type, suggested_action}
- Routing: >=70 → agendar (WF-5); 40-69 → nurture; <40 → descartar
- Validación JSON con retry x2 antes de fallback manual
- Status: EN CONSTRUCCIÓN

**WF-5 handoff (leads intent_score>=70):**
- Salesforce: campos custom (xsell_score__c, bnpl_gmv_12m__c, etc.)
- Slack: mensaje al Hunter con SLA 24h reminder, 48h escalada
- Status: EN CONSTRUCCIÓN

**Archivos de soporte:**
- workflows/copies.md (email d0, variante B, LinkedIn, WhatsApp templates)
- workflows/qualifier_prompt.md (Claude prompt + 7 arquetipos)
- workflows/salesforce_stub.md (field mapping)
- workflows/costos.md (Clay ~800, Apollo ~150, Smartlead ~100, n8n ~50, LinkedIn ~100, WhatsApp ~200, Claude ~100 = ~1500 USD total)
- workflows/ARCHITECTURE.md (diagrama de flujos, data contracts, retry policies)

**Credenciales por env vars (nunca hardcoded):**
- CLAY_API_KEY
- SMARTLEAD_API_KEY
- WHATSAPP_360DIALOG_API_KEY
- ANTHROPIC_API_KEY
- SALESFORCE_CLIENT_ID, SALESFORCE_CLIENT_SECRET, SALESFORCE_INSTANCE_URL

### Sprint 2A: Automation Engineer ✅ COMPLETADO
- ✅ 5 JSONs importables (wf1-wf5) generados
- ✅ 5 READMEs documentados (WF1-WF5_README.md)
- ✅ 4 archivos de soporte (copies.md, qualifier_prompt.md, salesforce_stub.md, costos.md)
- ✅ ARCHITECTURE.md (flujos, data contracts, 20 env vars, retry policies)
- ✅ Bonus: Demo package (3 workflows demo + ZIP + demo_script.md + IMPORT_CHECKLIST.md)
- ✅ Costos: USD 1,350/mes (dentro de 3,000 USD ceiling)
- Status: Awaiting QA validation

### Sprint 2C: QA Tester (EN PROGRESO)
**Suite de 5 tests (25 pruebas totales):**
1. Test 1 (7 Arquetipos contra WF-4): Validar clasificación correcta
2. Test 2 (Edge Cases): opt_in=false, no email, categoría sin normalizar, GMV nulo, reply en inglés
3. Test 3 (End-to-End): 1 lead sintético Tier B WF-1→WF-5 sin intervención
4. Test 4 (Documentation Readability): Lector sin contexto puede operar con READMEs
5. Test 5 (6 Asserts Automáticas): Sin hardcoded keys, retry logic, error handlers, etc.

**Criterios de éxito:**
- 7/7 arquetipos pasan (intent_score en rango)
- opt_in=false previene WhatsApp (gate legal CRÍTICO)
- Lead completa ciclo sin errores
- Documentación legible para lector externo
- 6/6 asserts técnicas pasan

### Sprint 2B: Dashboard Engineer (PENDIENTE)
- Trigger: Tras Sprint 2C aprobado
- Input: hallazgos.json + top50.csv
- Output: Streamlit app (2 tabs: Diagnóstico + Pipeline Health)

### Checkpoint 2 (CP2): Reporte Final
- Esperado DESPUÉS de Sprint 2C + 2B completados
- Estado de cada 5 workflows
- Resultado QA exacto (# pruebas/# pasan)
- Costo total vs 3000 USD ✓ (USD 1,350)
- Comando de importación n8n
- Env vars requeridas (20 documentadas)
- Si todo pasa: desbloquea Sprint 3 (writer → business_case.docx)

## Riesgos
- La discrepancia de CVR por source (data_quality_report.md sección 4) debe explicarse
  en vivo si surge en Q&A; está documentada como número direccional sobre funnel sintético
  con n pequeño.
- `funnel_snapshot` tiene fuentes con n muy bajo (Event n=2, KAM_handoff n=6) — cualquier
  CVR por esas fuentes no es estadísticamente robusto, ya declarado como supuesto.
- Escenario optimista de pipeline (350+/mes) depende de validar CVR 47.1% a escala mayor
  que la muestra actual — declarado explícitamente como supuesto no confirmado.

## Decisiones
- Ver "Decisiones ya tomadas" en CLAUDE.md — no reabrir sin aprobación del humano.
