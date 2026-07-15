# RUBRIC_CHECKLIST.md — Guardián de calidad del business case

El `po` usa esta checklist para revisar CADA entrega de subagente y antes de cerrar cada sprint.
"RECHAZADO" si falla cualquier gate o eje.

## Los 6 GATES (violarlos = rechazo automático)

- [ ] **Gate 1 — Trazabilidad de números:** todo claim cuantitativo cita pestaña + columna + filtro del dataset.
- [ ] **Gate 2 — Herramientas nombradas:** nunca "AI"/"automation" genérico; siempre herramienta específica (Clay, Apollo, n8n, Smartlead, WhatsApp BA vía 360dialog, Claude API, etc.).
- [ ] **Gate 3 — Prototipo funcional:** el prototipo corre de verdad; prohibido mockups, slides o screenshots estáticos.
- [ ] **Gate 4 — Narrativa en párrafos:** documento en prosa; bullets solo para listas verdaderamente paralelas.
- [ ] **Gate 5 — Equipo y CRM:** equipo ≤ 3 personas (1 Hunter Sr, 1 Hunter Jr, 1 SDR); no se propone reemplazar Salesforce.
- [ ] **Gate 6 — Defendible en vivo:** todo número es derivable/defendible; supuestos declarados explícitamente con racional.

## Los 5 EJES de evaluación

- [ ] **Eje 1 — Rigor analítico:** el scoring/TOP 50 usa columnas correctas (`category`, no `vertical`), excluye Grandes Superficies, separa expansión de x-sell puro, y el mapeo de funnel (S1_Prospect…S8_Live/X_Lost → S1–S7 del brief) es explícito. El `funnel_snapshot` se trata como direccional/sintético, no como baseline.
- [ ] **Eje 2 — Viabilidad operativa:** la motion es ejecutable por 1 persona + agentes AI con el equipo dado; presupuesto SaaS ≤ USD 3,000/mes con racional de costo por herramienta; WhatsApp Business API solo con `opt_in=true`; scraping (si aparece) está bounded por Legal y nunca es fuente primaria.
- [ ] **Eje 3 — Impacto de negocio:** ROI expresado en COP/GMV o pipeline (nunca solo %); conecta con BPI 14%→19% y pipeline calificado 150→300/mes (M3); moneda COP, GMV en millones (COP MM).
- [ ] **Eje 4 — Calidad de comunicación:** `business_case.docx` ≤ 3 páginas, narrativa clara y ejecutiva, sin jerga sin explicar.
- [ ] **Eje 5 — Preparación para defensa:** `qa_prep.md` cubre 20 preguntas duras (data, negocio, técnicas, riesgo) con respuestas defendibles en vivo, alineadas a los gates.

## Checkpoints humanos (CP)

- [ ] **CP1** — aprobación del TOP 50 y de la matemática del target (fin Sprint 1).
- [ ] **CP2** — demo end-to-end de workflows + dashboard (fin Sprint 2).
- [ ] **CP3** — aprobación del documento vs esta rúbrica (fin Sprint 3).
- [ ] **CP4** — ensayo de Q&A (fin Sprint 4).

## Confidencialidad
- [ ] Dataset interno de Addi no se sube a repos públicos ni se publica.
