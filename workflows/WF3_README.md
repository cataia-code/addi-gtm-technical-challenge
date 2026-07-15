# WF-3: Outreach (Email D0 → LinkedIn D2 → WhatsApp D5)

## Descripción General

**Propósito:** Ejecutar una secuencia de outreach multicanal a 10 días para marcas Tier B con `enrichment_status = success`.

**Secuencia:**
- **Día 0:** Email via Smartlead (personalizado con {{merge_fields}})
- **Día 2:** LinkedIn manual task (SDR lo hace con su cuenta, protege contra ToS risk)
- **Día 5:** WhatsApp Business API (solo si `opt_in=true`, compliance)

**Trigger:** Webhook desde WF-2 cuando enrichment completó, O activación manual

**Duración:** Asincrónico (10 días de ejecución, pero n8n no ocupa recursos continuos gracias a Wait nodes)

---

## Qué Entra (Input)

**Fuente:** Google Sheet tab "Tier_B" enriquecido (post-WF-2)

**Requiere:**
- `enrichment_status = "success"` (skip si es manual_review o failed)
- `contacto_email` (para Smartlead)
- `contacto_nombre` (personalization)
- `brand_id`, `category`, `gmv_cop_millions_12m`, `gmv_90d_to_12m_ratio` (merge fields)
- `linkedin_url` (para tarea manual D2)
- `opt_in` (boolean, default false si no presente) (para WhatsApp D5)

**Ejemplo:**
```json
{
  "brand_id": "Brand_0145",
  "category": "Hogar",
  "contacto_nombre": "María Rodríguez",
  "contacto_email": "maria.rodriguez@brand0145.com",
  "linkedin_url": "https://linkedin.com/in/maria-rodriguez-123/",
  "gmv_cop_millions_12m": 4908,
  "gmv_90d_to_12m_ratio": 3.25,
  "opt_in": true
}
```

---

## Qué Sale (Output)

**Destino:** Google Sheet tab "Tier_B" (nuevas columnas de tracking)

**Columnas agregadas:**
```
outreach_email_d0              (timestamp de envío)
outreach_email_d0_opened       (boolean, desde Smartlead tracking)
outreach_email_d0_clicked      (boolean, desde Smartlead tracking)
outreach_email_d0_smartlead_id (campaign ID)
outreach_variant_b_sent        (boolean, si se envió reengagement)
linkedin_status                (pending_manual | completed | skipped)
outreach_whatsapp_d5           (boolean)
outreach_whatsapp_d5_id        (message ID desde 360dialog)
outreach_status                (in_progress | completed | paused)
```

**Ejemplo post-WF-3:**
```json
{
  "brand_id": "Brand_0145",
  "outreach_email_d0": "2026-07-14T18:30:00Z",
  "outreach_email_d0_opened": true,
  "outreach_email_d0_clicked": false,
  "outreach_email_d0_smartlead_id": "camp_12345",
  "outreach_variant_b_sent": true,
  "linkedin_status": "pending_manual",
  "outreach_whatsapp_d5": true,
  "outreach_whatsapp_d5_id": "msg_67890",
  "outreach_status": "in_progress"
}
```

---

## Lógica de Secuencia

```
Leer Tier_B (solo enrichment_status = success)
   ↓
D0 (mismo día):
   ├─ Smartlead: Enviar email personalizado
   ├─ Log: timestamp + campaign_id
   └─ Tracking: Open pixel + click tracking
   ↓
[WAIT 2 DÍAS]
   ↓
D2 (2 días después):
   ├─ Generar tarea Slack para SDR
   ├─ Copy: "Conecta con {{contacto_nombre}} en LinkedIn"
   ├─ Manual: SDR abre LinkedIn, copia propuesta, envía connection
   └─ Mark: linkedin_status = "pending_manual"
   ↓
[MONITOREO: ¿Email abierto + clickeado?]
   ├─ Sí: Priorizar para WF-4 inmediatamente
   └─ No: Enviar variante B del asunto (reengagement)
   ↓
[WAIT 3 DÍAS MÁS]
   ↓
D5 (5 días después):
   ├─ IF opt_in = true:
   │  ├─ Llamar 360dialog WhatsApp API
   │  ├─ Enviar template message pre-aprobado
   │  └─ Log: message_id
   └─ ELSE:
      └─ Skip (compliance)
   ↓
[D10: Si no hay reply, mover a nurture queue]
```

---

## Variables de Entorno Requeridas

```bash
# Smartlead (Email)
SMARTLEAD_API_KEY=<API key>
SMARTLEAD_WEBHOOK_API=https://api.smartlead.ai/v1
SMARTLEAD_FROM_EMAIL=hunter@addi.com

# Google Sheets
GOOGLE_SHEETS_ID=<spreadsheet ID>

# WhatsApp (360dialog)
WHATSAPP_360DIALOG_API_KEY=<API key>
WHATSAPP_PHONE_NUMBER_ID=<registered phone number ID>
WHATSAPP_BOOKING_LINK=https://addi-book.typeform.com/to/mp-xsell

# Slack
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/PATH
```

---

## Merge Fields (Exactitud Crítica)

**Email D0 & Variante B usan estos merge fields:**

| Field | Source | Example | Nota |
|---|---|---|---|
| `{{contacto_nombre}}` | Enriquecimiento (WF-2) | María Rodríguez | Personalización crítica |
| `{{brand_id}}` | top50.csv | Brand_0145 | Identificación única |
| `{{gmv_cop_millions_12m}}` | top50.csv | 4908 | Sin comas (número puro) |
| `{{gmv_90d_to_12m_ratio}}` | top50.csv | 3.25 | Porcentaje, decimales |
| `{{category}}` | top50.csv | Hogar | Capitalizado (si en CSV está lowercase) |
| `{{linkedin_url}}` | Enriquecimiento (WF-2) | https://linkedin.com/in/... | Para D2 task |

**Validación:**
- ❌ `{{gmv_cop_millions_12m}}` = "4,908" (commas rompen renderizado)
- ✅ `{{gmv_cop_millions_12m}}` = "4908" (puro número)
- ❌ `{{category}}` = "hogar" (minúsculas en email se ve desprofesional)
- ✅ `{{category}}` = "Hogar" (capitalizado)

---

## Contrato con Smartlead (D0 Email)

### Request
```json
POST https://api.smartlead.ai/v1/campaigns

{
  "email": "maria.rodriguez@brand0145.com",
  "name": "María Rodríguez",
  "subject": "Hogar: Crece con BNPL en Addi Marketplace",
  "body": "[email body with merge fields]",
  "tracking": true
}
```

### Response
```json
{
  "campaign_id": "camp_12345",
  "status": "sent",
  "timestamp": "2026-07-14T18:30:00Z"
}
```

### Tracking Updates (Webhook inverse)
Smartlead envía webhook cuando:
- Email abierto: `event: "open"`
- Link clickeado: `event: "click"`

n8n espera estos webhooks y actualiza Google Sheet automáticamente.

---

## Contrato con 360dialog (D5 WhatsApp)

### Request
```json
POST https://waba.360dialog.io/v1/messages

{
  "messaging_product": "whatsapp",
  "to": "+57XXXXXXXXX",
  "type": "template",
  "template": {
    "name": "addi_bnpl_pitch",
    "language": {"code": "es"},
    "parameters": {
      "body": {
        "parameters": [
          {"type": "text", "text": "María Rodríguez"},
          {"type": "text", "text": "Brand_0145"},
          {"type": "text", "text": "Hogar"}
        ]
      }
    }
  }
}
```

### Response
```json
{
  "messages": [
    {
      "id": "msg_67890",
      "message_status": "accepted"
    }
  ]
}
```

**Nota:** Template ID `addi_bnpl_pitch` debe estar pre-aprobado en 360dialog.

---

## Manejo de Errores

### D0 Email (Smartlead) Error
- **Timeout / 5xx:** Retry ×2 (backoff 1s, 2s)
- **Fallback:** Marcar `outreach_status = failed_email`, log Slack, no bloquea WF
- **Resultado:** Brand skips D2/D5, marcar para manual follow-up

### D2 LinkedIn Task Error
- **Slack notification falla:** Log error, continúa (non-critical)
- **SDR no recibe task:** Monitor manual; if >5 tasks missing, escalate

### D5 WhatsApp Error
- **Invalid phone number:** Log error, skip (don't retry)
- **360dialog timeout:** Retry ×2, then log (don't block)
- **Compliance:** If opt_in ≠ true, NEVER send (critical validation)

### D10 Nurture Assignment
- **If no reply + no click after D10:** Move to "Nurture_Queue" tab
- **SDR review 1x/week:** Decide whether to re-engage or discard

---

## Simplificaciones vs Producción

| Aspecto | MVP | Producción | Razón |
|---|---|---|---|
| **LinkedIn automation** | Manual SDR task | Selenium bot (riesgoso) | ToS violation; manual es compliance |
| **Email variants** | D0 + variante B | A/B testing multicanal (5+ variants) | Test subject lines, timing |
| **Tracking** | Smartlead pixel | Custom UTM + mixpanel | Granular analytics |
| **WhatsApp templates** | 1 template | Dynamic templates (3+) | Test engagement diff |
| **Async delays** | Hardcoded 2d, 5d | ML-optimized timing | Predict best send times |

---

## Qué Falta para Producción

1. **Real-time Smartlead webhook integration:**
   - Actual: N8n polls Google Sheet for tracking (manual)
   - Futuro: Smartlead sends webhook → n8n instantly updates
   - Implementar: Webhook receiver + dynamic data mapping
   - Tiempo: 2 horas

2. **Phone number enrichment (D5 WhatsApp):**
   - Actual: Assumes `phone` field en contacto (puede estar vacío)
   - Futuro: Clay también devuelva phone; si no hay, skip WhatsApp
   - Implementar: Clay phone extraction + WF-2 update
   - Tiempo: 1 hora

3. **Email A/B testing framework:**
   - Actual: 1 subject line fijo
   - Futuro: Randomize subject (D0 variant A vs B)
   - Implementar: Split por {{$random}} + track variants
   - Tiempo: 3 horas

4. **Scheduled sending (timezone-aware):**
   - Actual: Email sends immediately on D0
   - Futuro: Schedule D0 email para 9 AM COT recipient timezone
   - Implementar: Timezone parsing + Smartlead scheduling
   - Tiempo: 2 horas

5. **Unsubscribe & compliance tracking:**
   - Actual: No unsubscribe link
   - Futuro: Email footer con unsubscribe link + tracking
   - Implementar: GDPR compliance email headers
   - Tiempo: 1 hora

---

## Testing

### Test Local (Antes de Importar)

1. **Validar Smartlead API key:**
   ```bash
   curl -X POST https://api.smartlead.ai/v1/campaigns \
     -H "Authorization: Bearer $SMARTLEAD_API_KEY" \
     -d '{"email":"test@example.com","subject":"Test","body":"Test","tracking":true}'
   ```

2. **Verificar 360dialog credenciales:**
   ```bash
   curl -X POST https://waba.360dialog.io/v1/messages \
     -H "Authorization: Bearer $WHATSAPP_360DIALOG_API_KEY" \
     -d '{"messaging_product":"whatsapp","to":"+PHONE","type":"text"}'
   ```

### Test en n8n (Sandbox)

1. **Importar WF-3 JSON**

2. **Test con 1 brand:**
   - Editar Tier_B en Google Sheet: solo Brand_0145
   - Configure: `opt_in=true`
   - Execute Workflow

3. **Verificar D0:**
   - Slack should notify: "D0 email enviado"
   - Check Smartlead campaign created
   - Verify merge fields rendered ({{gmv_cop_millions_12m}} = "4908", not "4,908")

4. **Simular D2 (esperar 2 min, no 2 días):**
   - Editar Wait node: 2 minutos en lugar de 2 días (test acelerado)
   - Check: Slack task generado para LinkedIn

5. **Simular D5:**
   - Editar Wait node D2→D5: 1 minuto (total 3 min desde inicio)
   - Check: WhatsApp enviado si opt_in=true

6. **Test opt_in=false:**
   - Crear segundo test con opt_in=false
   - Verify: WhatsApp NOT sent (branch lógica IF funciona)

---

## Monitoreo Post-Deployment

**Métricas clave:**

1. **Email delivery rate:**
   - Target: 95%+ (Smartlead, industry standard)
   - Check: Smartlead dashboard → Delivery report

2. **Email open rate:**
   - Target: 20-30% (B2B SaaS benchmark)
   - Check: Smartlead → Open events

3. **Email click rate:**
   - Target: 2-5% (B2B SaaS benchmark)
   - Check: Smartlead → Click events

4. **LinkedIn task completion:**
   - Target: 80%+ (SDR manual actions)
   - Check: Google Sheet `linkedin_status` = "completed"

5. **WhatsApp delivery:**
   - Target: 99%+ (WhatsApp API SLA)
   - Check: 360dialog → Message status

6. **Reply rate (feeds WF-4):**
   - Target: 5-15% (depends on copy quality)
   - Check: Replies llegando a Smartlead → n8n webhook

---

## Ejemplos de Email Renderizado

### Brand_0145 (Hogar)
```
Subject: Hogar: Crece con BNPL en Addi Marketplace

Body:
Hola María Rodríguez,

Vimos que Brand_0145 genera COP 4908 MM anuales con momentum del 3.25% 
en los últimos 3 meses.

En categoría Hogar, el volumen de consumo con BNPL sigue creciendo. 
Muchas marcas como ustedes ya multiplican ordenes originando opciones de crédito 
en Addi Marketplace — y sin esfuerzo operativo extra (nuestro stack maneja 
validación, desembolso, cobranza).

¿Nos damos 15 min esta semana para explorar la oportunidad?

Saludos,
Hunter Jr
Marketplace Growth, Addi
```

### Variante B (reengagement si no abierto a 48h)
```
Subject: Brand_0145: Aclaración sobre BNPL en Hogar 🎯

Body:
Hola María Rodríguez,

Pasé por alto detalles clave en mi email anterior. Te voy al punto:

• 35 marcas en Hogar ya mueven BNPL en Addi con comisión plana
• Ustedes en particular crecen 3.25x trimestral — eso es oportunidad
• No reemplazamos tu procesador: sumamos canal extra (Marketplace)

Propuesta: 25 min, Zoom, viernes 2 PM. Muestro números de 2-3 casos similares.

¿Te dejo 2 horarios?

Hunter Jr
Marketplace Growth, Addi
```

---

## Contacto & Escalación

**Si Smartlead emails fallan:**
1. Check Smartlead status page
2. Verify SMARTLEAD_API_KEY válida
3. Check email addresses are valid (no @example.com)

**Si WhatsApp no se envía:**
1. Verify opt_in field is true
2. Check phone number format (+57XXXXXXXXX)
3. Verify template pre-approved in 360dialog

**Si >10% de emails fallan:**
- Escalar a #automation channel
- Consider fallback: Gmail direct integration
