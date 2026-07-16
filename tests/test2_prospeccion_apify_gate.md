# Test 2: prospeccion real LangGraph a Excel

No se envia Slack, email ni WhatsApp. Los leads se validan, deduplican contra SQLite y se guardan en Excel.

## Apify input

```json
{
  "totalResults": 3,
  "hasEmail": true,
  "emailStatusIncludes": [
    "verified"
  ],
  "hasPhone": true,
  "personLocationCountryIncludes": [
    "Colombia"
  ],
  "companyLocationCountryIncludes": [
    "Colombia"
  ],
  "companyIndustryIncludes": [
    "Retail",
    "Furniture",
    "Consumer Goods"
  ],
  "personTitleIncludes": [
    "Founder",
    "CEO",
    "Director",
    "Head of Ecommerce",
    "Ecommerce Manager"
  ],
  "roleMatchMode": "any",
  "companyKeywordIncludes": [
    "hogar",
    "muebles",
    "decoracion",
    "home"
  ],
  "companyKeywordMode": "broad",
  "resetProgress": false,
  "dontSaveProgress": true,
  "countOnly": false
}
```

- `2026-07-15T19:06:02` nodo_apify_buscar_leads: 3 leads recibidos desde Apify.
- `2026-07-15T19:06:02` nodo_validar_campos_completos: 3 leads con campos completos.
- `2026-07-15T19:06:02` nodo_filtrar_duplicados_db: 3 leads nuevos.
- `2026-07-15T19:06:02` nodo_investigar_y_redactar: 3 perfiles y borradores creados.
- `2026-07-15T19:06:02` nodo_exportar_excel_y_registrar_db: Excel guardado en C:\Users\ASUS\Documents\GitHub\addi_technical_challenge\data\test2_prospectos_apify.xlsx.
- `2026-07-15T19:06:02` nodo_exportar_excel_y_registrar_db: 3 leads registrados en SQLite.
- `2026-07-15T19:06:02` Excel generado: C:\Users\ASUS\Documents\GitHub\addi_technical_challenge\data\test2_prospectos_apify.xlsx
- `2026-07-15T19:06:02` Leads exportados: 3
- `2026-07-15T19:06:15` Verificacion Excel: 3 filas, 12 columnas, 0 celdas faltantes en campos requeridos.
- `2026-07-15T19:06:20` Verificacion dedupe SQLite: los 3 emails exportados retornan prospect_exists=True.
