# Sprint 2 Business Case

## Executive Summary
Sprint 2 validated an end-to-end n8n demo using real data from `analysis/top50.csv`, Groq-based qualification, Slack handoff, and a Salesforce simulation fallback. The pipeline now runs in live n8n with three real Tier B rows and produces deterministic routing for `agendar`, `nurture`, and `descartar`.

## What Was Validated
- Real CSV ingestion from `analysis/top50.csv`
- Groq qualification using `llama-3.3-70b-versatile`
- Slack notifications for qualified outcomes
- Salesforce simulated locally as a payload log, not a live API dependency
- Routing hardened to normalize `suggested_action` to the strict enum

## Business Value
- Reduces manual qualification effort on inbound replies
- Preserves demo reliability without depending on Salesforce credentials
- Uses real data and real LLM calls, which makes the demo credible for stakeholders
- Keeps the routing logic safe against free-text model variance

## Risks Addressed
- Prompt drift from Groq returning descriptive text instead of enum values
- Demo failures caused by missing external credentials
- False assumptions from simulated data instead of the approved CSV

## Status
- Live n8n execution completed successfully
- Three demo scenarios were rerun successfully
- Routing now uses score-based normalization, so Slack/WhatsApp behavior is stable even if the model wording changes

## Next Steps
- Keep the workflow active for the live panel demo
- If Salesforce is required later, swap the Code-node stub for a real HTTP Request with the same payload contract
- If strict model output is required, keep the prompt instruction and retain the routing guardrail
