# Memoria local de agentes

La base runtime se crea en `data/agent_memory.sqlite3` y esta ignorada por git.

Contiene:

- `leads`: estado operativo de leads contactados.
- `replies`: respuestas recibidas y clasificacion LLM.
- `opt_ins`: permisos por canal.
- `prospect_consultations`: prospectos reales ya consultados para evitar duplicados.
- `agent_interactions`: bitacora tipo RAG simple con `embedding_text` para busqueda local.

El ranking oficial no sale de esta base. El score y el top 50 se leen directamente desde `analysis/top50.csv`.
