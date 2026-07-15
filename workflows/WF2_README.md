# WF-2: Enrichment (Clay Waterfall)

## Descripción General

**Propósito:** Enriquecer cada marca de Tier B (35 filas) con datos de contacto verificados usando Clay API (waterfall: Apollo → LinkedIn → website scrape).

**Trigger:** Webhook POST desde WF-1 cuando la cola Tier B está lista, O activación manual en n8n

**Duración estimada:** 30–40 minutos (35 brands × ~50ms per API call)

**Aplicable a:** Tier B SOLO (35 marcas). Tier A (15 marcas) NO se auto-enriquece (Hunter Sr lo trabaja manualmente).

---

## Qué Entra (Input)

**Fuente:** Google Sheet tab "Tier_B" (escrito por WF-1)

**Estructura:**
```json
{
  "brand_id": "Brand_0145",
  "category": "Hogar",
  "gmv_cop_millions_12m": 4908,
  "gmv_90d_to_12m_ratio": 3.25,
  "tier": "B",
  "routing": "Motion/SDR"
}
```

**Cantidad:** 35 filas (Tier B completo)

**Procesamiento:** WF-2 itera por cada brand, llama a Clay API una vez, y espera respuesta.

---

## Qué Sale (Output)

**Destino:** Google Sheet tab "Tier_B" (nuevas columnas agregadas)

**Nuevas columnas agregadas por WF-2:**
```
enrichment_status      (success | manual_review | failed)
contacto_nombre        (string, empty if not found)
contacto_email         (string, empty if not found)
contacto_cargo         (string, empty if not found)
linkedin_url           (URL, empty if not found)
cms_detectado          (string: Shopify, WooCommerce, Custom, etc.)
dominio_sitio          (string: domain.com)
```

**Ejemplo de fila completa después de WF-2:**
```json
{
  "brand_id": "Brand_0145",
  "category": "Hogar",
  "gmv_cop_millions_12m": 4908,
  "final_score": 89.2,
  "routing": "Motion/SDR",
  "enrichment_status": "success",
  "contacto_nombre": "María Rodríguez",
  "contacto_email": "maria.rodriguez@brand0145.com",
  "contacto_cargo": "Operations Manager",
  "linkedin_url": "https://linkedin.com/in/maria-rodriguez-123/",
  "cms_detectado": "Shopify",
  "dominio_sitio": "brand0145.com"
}
```

---

## Lógica de Clay Waterfall

```
Para cada brand en Tier_B:
  ┌─────────────────────────────────────────────────┐
  │ Llamar Clay API: company_domain="{{brand_id}}"  │
  └─────────────────┬───────────────────────────────┘
                    │
        ┌───────────┴────────────┐
        │                        │
   ✅ Éxito               ❌ Error/No respuesta
  (contacto found)       (retry x1, luego x2)
        │                        │
        ▼                        ▼
  Extract:                   ┌─────────────┐
  - name                     │ Retry 1 sec │
  - email                    └──────┬──────┘
  - title/role                      │
  - linkedin_profile_url        ❌ Fails?
  - cms detected              (retry 1 más)
  - domain                         │
        │                        ┌─┴─────────┐
        │                        │           │
        │                    ✅ Éxito   ❌ Falla x2
        │                        │           │
        └─────────────┬──────────┘           │
                      │                      │
                      ▼                      ▼
              ┌──────────────────┐   ┌──────────────────┐
              │ enrichment_status│   │enrichment_status:│
              │ = "success"      │   │ "manual_review"  │
              └──────────────────┘   └──────────────────┘
                      │                      │
                      └──────────┬───────────┘
                                 ▼
                    Escribir fila a Google Sheet
                    (continue con siguiente brand)
```

**Decisiones clave:**
- **Retry policy:** 2 reintentos total si API falla (no si "no results", eso es "manual_review")
- **No bloquea flujo:** Si Clay falla para Brand A, marca como "manual_review" y **continúa** con Brand B (no detiene el pipeline)
- **Fallback:** Si no encuentra contacto: enrichment_status = "manual_review", Hunter Sr hace búsqueda manual después

---

## Variables de Entorno Requeridas

```bash
# Clay API
CLAY_API_KEY=<API key from Clay dashboard>

# Google Sheets
GOOGLE_SHEETS_ID=<spreadsheet ID>

# Slack (notificaciones)
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/PATH
```

---

## Contrato con Clay API

### Request
```json
POST https://api.clay.com/v2/search
Authorization: Bearer {{ CLAY_API_KEY }}

{
  "company_domain": "Brand_0145",
  "enrichment_profile": ["apollo", "linkedin", "website"]
}
```

### Response (Success 200)
```json
{
  "result": {
    "contacts": [
      {
        "name": "María Rodríguez",
        "email": "maria.rodriguez@brand0145.com",
        "title": "Operations Manager",
        "linkedin_profile_url": "https://linkedin.com/in/maria-rodriguez-123/",
        "cms": "Shopify",
        "domain": "brand0145.com"
      }
    ]
  }
}
```

### Response (No Results 200)
```json
{
  "result": {
    "contacts": []
  }
}
```
→ WF-2 marca como "manual_review" (no es error, solo data no encontrada)

### Response (Error 5xx / Timeout)
```
Status: 500 Internal Server Error
```
→ WF-2 reintenta (x2), luego marca como "manual_review" si sigue fallando

---

## Manejo de Errores

### Escenario 1: Clay API timeout
- **Acción:** Retry automático a 1s + 2s backoff
- **Si falla x2:** enrichment_status = "manual_review"
- **Log:** Slack → #automation channel
  ```
  ⚠️ WF-2 Error: Clay timeout para Brand_0145
  Acción: Marcado para manual_review
  Next: Hunter Sr busca contacto manualmente
  ```

### Escenario 2: Clay returns "no contacts" (empty array)
- **Acción:** NO es un error de API, es "no data found"
- **Resultado:** enrichment_status = "manual_review"
- **Log:** Informativo en Google Sheet

### Escenario 3: Google Sheets write fails
- **Acción:** Retry x2
- **Fallback:** Log error + Slack alert

### Escenario 4: Missing CLAY_API_KEY
- **Acción:** n8n error inmediato (credential not found)
- **Fallback:** Configure credential in n8n UI antes de correr

---

## Simplificaciones vs Producción

| Aspecto | MVP (Actual) | Producción | Razón Cambio |
|---|---|---|---|
| **API calls** | Serial (1 brand a la vez) | Batch API (5+ brands/call) | Reducir latency + API calls |
| **Enrichment fuentes** | Clay solo | Clay + Apollo native + LinkedIn Sales Nav + Clearbit | Diversificar fuentes si Clay falla |
| **Caching** | No | Redis cache de resultados previos | Evitar re-enriquecer mismo brand 2x |
| **Data quality** | Basic (keep empty if not found) | Validation + data quality scoring | Marcar baja-calidad-contactos |
| **Async processing** | Sync (espera respuesta) | Async + webhook callback | Mejora velocidad si Clay es lento |

---

## Qué Falta para Producción

1. **Batch Clay API calls:**
   - Actual: 1 call per brand (serial)
   - Futuro: POST multiple brands en una sola request
   - Implementar: Crear loops batch de 5 brands
   - Tiempo: 2 horas

2. **Fallback a Apollo nativo:**
   - Actual: Clay usa Apollo como step 1, pero si falla, no hay retry con Apollo directo
   - Futuro: Si Clay falla, llamar Apollo API directamente como fallback
   - Implementar: Apollo credential + branching logic
   - Tiempo: 3 horas

3. **LinkedIn Sales Navigator context:**
   - Actual: Clay extrae LinkedIn URL, pero no verifica si es valid/updated
   - Futuro: Validar LinkedIn URL + get more contact info (company, followers, etc.)
   - Implementar: LinkedIn API call (manual token needed)
   - Tiempo: 4 horas

4. **Data quality scoring:**
   - Actual: Cualquier contacto devuelto es "success"
   - Futuro: Score calidad (ej: email @company vs @gmail → company mejor)
   - Implementar: Add field `contact_quality_score` (0-100)
   - Tiempo: 2 horas

5. **Deduplication & enrichment history:**
   - Actual: Cada run de WF-2 re-enriquece todo
   - Futuro: Check si brand ya fue enriquecido; si sí, skip or revalidate after N days
   - Implementar: Add timestamp + revalidate flag
   - Tiempo: 3 horas

---

## Testing

### Test Local (Antes de Importar)

1. **Validar Clay API key:**
   ```bash
   curl -X POST https://api.clay.com/v2/search \
     -H "Authorization: Bearer $CLAY_API_KEY" \
     -H "Content-Type: application/json" \
     -d '{"company_domain":"shopify.com","enrichment_profile":["apollo"]}'
   ```
   → Debe retornar contacto válido (ej: Shopify leadership)

2. **Test con 1 brand:**
   - Editar Tier_B en Google Sheet: dejar solo Brand_0145
   - Importar WF-2 en n8n
   - Ejecutar manualmente
   - Verificar columnas enrichment_ agregadas con datos

### Test en n8n (Sandbox)

1. **Importar WF-2 JSON:**
   ```bash
   # n8n UI: Workflows → Import → wf2_enrichment.json
   ```

2. **Configurar credenciales:**
   - Google Sheets credential (service account)
   - n8n HTTP node: Colocar CLAY_API_KEY en header (Bearer token)

3. **Test run con 3 brands:**
   - Editar Tier_B: dejar solo filas 1–3
   - Execute Workflow
   - Esperar ~3 minutos
   - Verificar Google Sheet tiene 3 filas con enrichment_status = "success" o "manual_review"

4. **Verificar data:**
   - contacto_nombre, contacto_email poblados (si Clay devolvió)
   - linkedin_url formato correcto (https://linkedin.com/in/...)
   - cms_detectado en ["Shopify", "WooCommerce", "Custom", ""] (nunca NULL)

### Test de Retry (Simular falla Clay)

1. **Mock timeout:** Editar WF-2 nodo Clay: cambiar URL a algo inválido
2. **Execute Workflow:** Debe retry 2x, luego marcar "manual_review"
3. **Restaurar URL correcta**
4. **Execute nuevamente:** Debe completar exitosamente

---

## Monitoreo Post-Deployment

**Métricas a trackear:**

1. **Enrichment success rate:**
   - Target: ≥80% (28/35 brands encuentran contacto)
   - Check: Contar "success" vs "manual_review" en Google Sheet

2. **Average API latency:**
   - Target: <1 segundo per brand
   - Check: n8n execution history

3. **Manual review backlog:**
   - Si >5 brands quedan en "manual_review", escalar a Hunter Sr

4. **Clay API errors:**
   - Track 5xx errors, rate limits, timeouts
   - Si >3 errors en una run, investigate Clay status page

---

## Ejemplos de Enriquecimiento

### Brand_0145 (Hogar, 4.9B GMV) — ✅ Success
```
brand_id: Brand_0145
enrichment_status: success
contacto_nombre: María Rodríguez
contacto_email: maria.rodriguez@brand0145.com
contacto_cargo: Operations Manager
linkedin_url: https://linkedin.com/in/maria-rodriguez-123/
cms_detectado: Shopify
dominio_sitio: brand0145.com
```
→ Ready para WF-3 (Outreach)

### Brand_XXXX (Hipotético) — ⚠️ Manual Review
```
brand_id: Brand_XXXX
enrichment_status: manual_review
contacto_nombre: [empty]
contacto_email: [empty]
contacto_cargo: [empty]
linkedin_url: [empty]
cms_detectado: [empty]
dominio_sitio: [empty]
```
→ Hunter Sr hace búsqueda manual vía LinkedIn + Google

---

## Contacto & Escalación

**Si Clay no enriquece:**
1. Verificar CLAY_API_KEY es válida
2. Verificar que "brand_id" es un dominio válido (ej: "brand0145.com" no "Brand_0145")
3. Si Clay API está down: check https://status.clay.com/
4. Notificar #automation con detalles de error

**Si <80% de enrichment success:**
- Esto podría indicar que Clay no tiene data para categoría o región (Colombia)
- Considerar fallback a Apollo directo + manual research
