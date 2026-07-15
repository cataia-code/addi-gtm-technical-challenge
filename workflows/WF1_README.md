# WF-1: Ingesta Scoring

## Resumen

WF-1 lee el archivo real `analysis/top50.csv`, valida que tenga 50 filas, y escribe una salida local en `workflows/demo/staging_output.csv`.

## Flujo

1. Cron lunes 6:00 AM COT.
2. Leer `analysis/top50.csv` con `Read Binary File`.
3. Parsear con `Spreadsheet File`.
4. Validar conteo total y split `A/B`.
5. Escribir CSV local de staging.
6. Notificar a Slack.

## Reglas

- No usar datos simulados.
- No usar Google Sheets en esta versión.
- La ruta de entrada debe ser exactamente `analysis/top50.csv`.

## Salida

- `workflows/demo/staging_output.csv`

## Verificación

- 50 filas totales.
- 15 filas Tier A.
- 35 filas Tier B.
