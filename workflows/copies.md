# Email & Message Templates para Outreach

## Email Día 0 (Smartlead)

**Subject:** (Merge field requerido: {{category}})
```
GMV en {{category}}: Crece con BNPL en Addi Marketplace
```

**Body:**
```
Hola {{contacto_nombre}},

Vimos que {{brand_id}} genera COP {{gmv_cop_millions_12m}} MM anuales 
con momentum del {{gmv_90d_to_12m_ratio}}% en los últimos 3 meses.

En categoría {{category}}, el volumen de consumo con BNPL sigue creciendo. 
Muchas marcas como ustedes ya multiplican ordenes originando opciones de crédito 
en Addi Marketplace — y sin esfuerzo operativo extra (nuestro stack maneja 
validación, desembolso, cobranza).

¿Nos damos 15 min esta semana para explorar la oportunidad?

Saludos,
Hunter Jr
Marketplace Growth, Addi
```

---

## Email Variante B (Reengagement a 48h, sin apertura)

**Subject:**
```
{{brand_id}}: Aclaración sobre BNPL en {{category}} 🎯
```

**Body:**
```
Hola {{contacto_nombre}},

Pasé por alto detalles clave en mi email anterior. Te voy al punto:

• 35 marcas en {{category}} ya mueven BNPL en Addi con comisión plana
• Ustedes en particular crecen {{gmv_90d_to_12m_ratio}}% trimestral — eso es oportunidad
• No reemplazamos tu procesador: sumamos canal extra (Marketplace)

Propuesta: 25 min, Zoom, viernes 2 PM. Muestro números de 2-3 casos similares.

¿Te dejo 2 horarios?

Hunter Jr
Marketplace Growth, Addi
```

---

## LinkedIn Manual Task Template (para Slack → SDR)

**Contexto (generado automático en Slack):**
```
🔗 TAREA MANUAL: LinkedIn Connection
Brand: {{brand_id}} ({{category}})
Contacto: {{contacto_nombre}}
Email: {{contacto_email}}
LinkedIn: {{linkedin_url}}
GMV: COP {{gmv_cop_millions_12m}} MM | Momentum: {{gmv_90d_to_12m_ratio}}%

⚠️  No automatices — copia + pega manual con tu cuenta.
Deadline: Hoy antes de las 5 PM (D2 del flujo).
```

**Propuesta (copy para copiar):**
```
Hola {{contacto_nombre}},

En Addi vemos que {{brand_id}} crece fuerte en {{category}}. 
Tu equipo maneja BNPL bien — sabemos porque procesamos 
datos de la vertical.

Conectemos — quizá tiene sentido explorar Marketplace.

(Si no te interesa, no presión; solo entendamos por qué.)

—
Hunter Jr | Marketplace Growth, Addi
```

---

## WhatsApp Message (D5, solo si opt_in=true)

**Message Template:**
```
Hola {{contacto_nombre}} 👋

De Addi Marketplace aquí. Vimos que {{brand_id}} mueve {{gmv_cop_millions_12m}} MM en {{category}}.

¿Libre 15 min esta semana para hablar BNPL en nuestro marketplace? 
(Sin costo, sin compromiso.)

[BOOKING LINK AQUÍ]

Saludos,
Addi Sales
```

---

## Ejemplos Reales (Tier B Sample)

### Brand_0145 (Hogar, 89/100)
- **Nombre**: Brand_0145
- **GMV 12m**: COP 4,908 MM
- **Momentum**: 3.25x
- **Categoria**: Hogar

**Email D0 merged:**
```
Subject: Hogar: GMV crece con BNPL en Addi Marketplace

Hola [contacto_nombre],

Vimos que Brand_0145 genera COP 4,908 MM anuales con momentum del 3.25% 
en los últimos 3 meses.

En categoría Hogar, el volumen de consumo con BNPL sigue creciendo. 
Muchas marcas como ustedes ya multiplican ordenes originando opciones de crédito 
en Addi Marketplace — y sin esfuerzo operativo extra...
```

### Brand_0686 (Vehículos y autopartes, 86/100)
- **Nombre**: Brand_0686
- **GMV 12m**: COP 943 MM
- **Momentum**: 3.81x
- **Categoria**: Vehículos y autopartes

**Email D0 merged:**
```
Subject: Vehículos y autopartes: Crece con BNPL en Addi Marketplace

Hola [contacto_nombre],

Vimos que Brand_0686 genera COP 943 MM anuales con momentum del 3.81% 
en los últimos 3 meses.

En categoría Vehículos y autopartes, el volumen de consumo con BNPL sigue creciendo...
```

---

## Notas de Implementación

- **Merge fields obligatorios:**
  - `{{contacto_nombre}}` — del enrichment (WF-2)
  - `{{brand_id}}` — de top50.csv
  - `{{gmv_cop_millions_12m}}` — de top50.csv (guardar como número sin separadores)
  - `{{gmv_90d_to_12m_ratio}}` — de top50.csv (% como número)
  - `{{category}}` — de top50.csv
  - `{{linkedin_url}}` — del enrichment (WF-2)
  - `{{contacto_email}}` — del enrichment (WF-2)

- **Tracking en Smartlead:**
  - Pixel de apertura automático
  - Click tracking en links (Addi booking URL)
  - Fallback: si Smartlead falla, retry x2 con backoff

- **WhatsApp Business API:**
  - Solo si `opt_in = true` (validación explícita en WF-3)
  - Message ID 12345 (template preregistrada en 360dialog)
  - Link de booking: `https://addi-book.typeform.com/to/mp-xsell` (ejemplo, update en producción)

---

## Alternativas Descartadas

1. **Personalisación con IA (GPT):** Evaluado pero rechazado porque:
   - Costo extra (~$100/mes)
   - Latencia adicional (2-3s por email)
   - Riesgo de alucinaciones
   - En esta etapa, copy templado + merge fields es suficiente para validar canal

2. **SMS además de WhatsApp:** Descartado:
   - SMS Business API (Twilio) requiere TCPA compliance en Colombia
   - WhatsApp es más barato + mejor tasa de apertura
   - Mantén canales: email (asíncrono) + LinkedIn (manual) + WhatsApp (opt-in)

3. **Automatización de LinkedIn (Selenium):** Descartada por:
   - Riesgo de ban de cuenta
   - ToS violation explícito en LinkedIn
   - SDR manual + generador de task en Slack es el trade-off correcto
