# Reporte de validacion

Este archivo reemplaza el reporte legacy en ingles. La validacion activa del proyecto vive en codigo:

- `src/scoring/compute_score.py` recalcula el score desde `analysis/top50.csv`.
- `src/scoring/validators.py` contiene los 8 asserts reutilizables del modelo.
- Los notebooks `01` y `02` muestran el diagnostico, la formula y los resultados visuales.
- Las pruebas automatizadas estan en `tests/`.

Regla operativa: no se usa una base SQLite para reconstruir el top 50. El ranking se lee desde `analysis/top50.csv` y la base local en `data/agent_memory.sqlite3` queda solo para memoria de interacciones, respuestas, opt-ins y prospectos consultados.
