# Workflow Architecture & Data Contracts

## System Overview

```
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚                      ADDI MARKETPLACE GTM MOTION                â”‚
â”‚                    (1 Hunter Sr + 1 SDR + AI)                   â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜

    analysis/top50.csv (frozen: 50 brands, 15 Tier A + 35 Tier B)
           â”‚
           â–¼
    â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
    â”‚  WF-1 INGESTA    â”‚ Trigger: Cron Monday 6:00 AM COT
    â”‚  (1h runtime)    â”‚ Input: CSV file
    â”‚                  â”‚ Output: Google Sheets (Tier_A + Tier_B tabs)
    â””â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
             â”‚
             â”œâ”€â–º cola_A (15 rows)  â”€â”€â–º Hunter Sr (manual path)
             â”‚                          [NOT auto-enriched, NOT auto-scored]
             â”‚
             â””â”€â–º cola_B (35 rows)  â”€â”€â–º WF-2 enrichment
                                        â”‚
                                        â–¼
                            â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
                            â”‚  WF-2 ENRICHMENT     â”‚ Trigger: Webhook from WF-1
                            â”‚  (30m runtime)       â”‚ Input: cola_B (35 rows)
                            â”‚ [Clay waterfall]     â”‚ Output: Enriched contacts (Google Sheet)
                            â””â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
                                     â”‚
                    â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¼â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
                    â”‚                â”‚                â”‚
                  success      manual_review        failed
                    â”‚                â”‚                â”‚
                    â–¼                â–¼                â–¼
             WF-3 outreach    [pause flow]   [pause flow]
                    â”‚
                    â–¼
            â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
            â”‚  WF-3 OUTREACH       â”‚ Trigger: Webhook from WF-2
            â”‚  (Multiday sequence) â”‚
            â”‚                      â”‚ D0: Email (Smartlead)
            â”‚  D0 D2 D5            â”‚ D2: LinkedIn manual task
            â”‚                      â”‚ D5: WhatsApp (opt_in only)
            â””â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
                     â”‚
        â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¼â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
        â”‚            â”‚            â”‚
      reply      no reply     open without
      (any day)   (D10)         click (48h)
        â”‚            â”‚            â”‚
        â–¼            â–¼            â–¼
     WF-4        nurture     variante B
   (scoring)      queue        email
        â”‚
        â–¼
    â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
    â”‚  WF-4 CALIFICACIÃ“N      â”‚ Trigger: Webhook from Smartlead (reply detected)
    â”‚  (Groq qualification) â”‚ Input: reply_text + brand context
    â”‚  (5-10s per reply)      â”‚ Output: intent_score + suggested_action
    â””â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
             â”‚
    â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”´â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
    â”‚                â”‚              â”‚
  â‰¥70            40â€“69          <40
  (agendar)     (nurture)     (descartar)
    â”‚                â”‚              â”‚
    â–¼                â–¼              â–¼
  WF-5          nurture queue   [log discard]
  handoff       (1x/week SDR)
    â”‚              review)
    â–¼
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚  WF-5 HANDOFF        â”‚ Trigger: Webhook from WF-4 (intent_score â‰¥70)
â”‚  (Salesforce + Slack)â”‚ Input: Qualified lead + Groq analysis
â”‚  (2-3s per lead)     â”‚ Output: Salesforce Lead + Slack notification
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
    â”‚
    â”œâ”€â–º Salesforce: Create Lead (custom fields + assignment)
    â”œâ”€â–º Slack: Notify Hunter/SDR with brief
    â””â”€â–º SLA: Reminder at 24h, escalation at 48h (no touch)
```

---

## Data Contracts (Input â†’ Output)

### WF-1: Ingesta & Scoring

**Input:**
```
File: analysis/top50.csv
Format: CSV (UTF-8)
Rows: 50 (15 Tier A + 35 Tier B)
Columns: rank, brand_id, tier, category, gmv_cop_millions_12m, 
         n_unique_clients_12m, gmv_90d_to_12m_ratio, days_since_last_orig, 
         recency_score, fit_score, momentum_score, category_bonus, final_score, why, routing
```

**Processing:**
- Read CSV
- Validate: Tier A = 15 rows (tier='A'), Tier B = 35 rows (tier='B')
- Group by tier

**Output:**
```
Google Sheets Document: "GTM-Motion-Top50-[DATE]"
â”œâ”€ Tab "Tier_A" (15 rows + header)
â”‚  Columns: [all from CSV]
â”‚  Rows: Sorted by rank (1-15)
â”‚
â””â”€ Tab "Tier_B" (35 rows + header)
   Columns: [all from CSV]
   Rows: Sorted by rank (16-50)
```

**Destination:** Google Sheets ID stored in `GOOGLE_SHEETS_ID` env var

**Data Quality Checks:**
- Row count: Tier A = 15, Tier B = 35 (fail if mismatch)
- Required columns: brand_id, tier, routing (fail if missing)
- No NULL in: brand_id, tier, category

---

### WF-2: Enrichment (Clay Waterfall)

**Input:**
```json
{
  "brand_id": "Brand_0145",
  "category": "Hogar",
  "gmv_cop_millions_12m": 4908,
  "tier": "B"
}
```

**Processing (per brand in cola_B):**
1. Call Clay API: waterfall (Apollo â†’ LinkedIn â†’ website scrape)
2. Retry x2 if API fails (not due to "no results found")
3. Extract fields: contacto_nombre, contacto_email, contacto_cargo, linkedin_url, cms_detectado, dominio_sitio
4. If Clay succeeds: enrichment_status = "success"
5. If Clay returns no results: enrichment_status = "manual_review"
6. If Clay API error after 2 retries: enrichment_status = "failed"

**Output (appended to Google Sheet Tier_B):**
```json
{
  "brand_id": "Brand_0145",
  "enrichment_status": "success",
  "contacto_nombre": "MarÃ­a RodrÃ­guez",
  "contacto_email": "maria.rodriguez@brand0145.com",
  "contacto_cargo": "Operations Manager",
  "linkedin_url": "https://linkedin.com/in/maria-rodriguez-123/",
  "cms_detectado": "Shopify",
  "dominio_sitio": "brand0145.com"
}
```

**Merge Strategy:** Left join on Google Sheet (WF-2 updates existing Tier_B rows with new columns)

**Fallback:** If Clay doesn't return contact in 2 retries:
- Mark enrichment_status = "manual_review"
- Do NOT stop pipeline
- Continue to next brand
- Log to Slack (#automation): "Brand_0145 requires manual enrichment research"

---

### WF-3: Outreach (Multiday Sequence)

**Input (from WF-2 success only):**
```json
{
  "brand_id": "Brand_0145",
  "contacto_nombre": "MarÃ­a RodrÃ­guez",
  "contacto_email": "maria.rodriguez@brand0145.com",
  "gmv_cop_millions_12m": 4908,
  "gmv_90d_to_12m_ratio": 3.25,
  "category": "Hogar",
  "opt_in": true  // [Optional, if available; default=false]
}
```

**Processing:**

**D0 (Day 0, same day as WF-2 completion):**
- Send email via Smartlead
- Subject: Merge `{{category}}` (e.g., "Hogar: GMV crece con BNPL en Addi Marketplace")
- Body: Merge {{gmv_cop_millions_12m}}, {{gmv_90d_to_12m_ratio}}, {{category}}, {{contacto_nombre}}
- Tracking: Open pixel + click link
- Log: Smartlead campaign ID, send timestamp

**D2 (Day 2):**
- Check email open status from Smartlead
- If opened + clicked: skip D2, fast-track to WF-4
- If opened but NOT clicked: send variante B (different subject)
- If NOT opened: send variante B (different subject)
- D2 action: Generate Slack task for SDR with LinkedIn copy + contact details
  - Text: "ðŸ”— MANUAL LINKEDIN: Brand_0145, MarÃ­a RodrÃ­guez, [link]"
  - SDR manually connects + sends proposal
  - Marks in sheet: linkedin_status = "pending_manual"

**D5 (Day 5):**
- Check: Does opt_in = true?
  - YES: Send WhatsApp via 360dialog
    - Message: "Hola {{contacto_nombre}}, De Addi aquÃ­..." + booking link
    - Log: Message ID, delivery status
  - NO: Skip WhatsApp (compliance)

**D10 (Day 10):**
- If NO reply + NO click by D10: Move to nurture queue
- Mark: outreach_status = "no_response_nurturing"
- Schedule SDR review 1x/week (manual decision: follow-up or discard)

**Output (updated in Google Sheet Tier_B):**
```json
{
  "brand_id": "Brand_0145",
  "outreach_email_d0": "2026-07-14T18:00:00Z",
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

### WF-4: Qualification (Groq Scoring)

**Trigger:** Webhook from Smartlead (when reply detected) or manual polling from Gmail/inbox

**Input:**
```json
{
  "brand_id": "Brand_0145",
  "category": "Hogar",
  "gmv_cop_millions_12m": 4908,
  "gmv_90d_to_12m_ratio": 3.25,
  "final_score": 89.2,
  "contacto_nombre": "MarÃ­a RodrÃ­guez",
  "reply_text": "Hi Hunter,\n\nThanks for reaching out. We're interested in exploring BNPL for our marketplace. Can we schedule a call with our CFO?",
  "reply_date": "2026-07-15T10:30:00Z"
}
```

**Processing:**
1. Build Groq prompt: system prompt + few-shot (7 archetypes) + lead context + reply_text
2. Call Groq API (sonnet-4-6, temp=0, max_tokens=500)
3. Parse JSON response
4. Validate:
   - intent_score in [0, 100]
   - is_decision_maker is boolean
   - objection_type is valid enum (or null)
   - suggested_action is valid enum
5. If JSON invalid or missing fields:
   - Retry 1 time with same prompt
   - If fails again: mark qualification_status = "manual_review", log to Slack, escalate
6. If JSON valid: proceed to routing

**Output:**
```json
{
  "brand_id": "Brand_0145",
  "reply_id": "reply_12345",
  "classification": {
    "intent_score": 85,
    "is_decision_maker": false,
    "objection_type": null,
    "suggested_action": "agendar",
    "reasoning": "Explicit interest, willing to include CFO (decision-maker). Move to demo."
  },
  "qualification_status": "success",
  "qualified_timestamp": "2026-07-15T10:32:00Z"
}
```

**Routing (Branching Logic):**
- If `intent_score >= 70`: Trigger WF-5 (handoff)
- If `40 <= intent_score < 70`: Append to nurture queue (sheet tab "Nurture_Queue")
- If `intent_score < 40`: Log discard (sheet tab "Discard_Log", reason = `reasoning`)

**Fallback (Groq API fails 3x):**
- Log error to Slack (#automation)
- Message Hunter Sr / SDR: "Manual qualification needed for Brand_0145"
- Create task in Salesforce (manual reminder)

---

### WF-5: Handoff (Salesforce + Slack)

**Input (from WF-4, only if suggested_action = "agendar"):**
```json
{
  "brand_id": "Brand_0145",
  "category": "Hogar",
  "gmv_cop_millions_12m": 4908,
  "gmv_90d_to_12m_ratio": 3.25,
  "final_score": 89.2,
  "contacto_nombre": "MarÃ­a RodrÃ­guez",
  "contacto_email": "maria.rodriguez@brand0145.com",
  "linkedin_url": "https://linkedin.com/in/maria-rodriguez-123/",
  "cms_detectado": "Shopify",
  "routing": "Motion/SDR",
  "intent_score": 85,
  "is_decision_maker": false,
  "objection_type": null,
  "reasoning": "Explicit interest, willing to include CFO...",
  "reply_text": "Hi Hunter, Thanks for reaching out..."
}
```

**Processing:**

**Step 1: Salesforce Lead Creation**
1. Map fields: brand_id â†’ Company, contacto_* â†’ FirstName/LastName/Email, etc.
2. POST to Salesforce REST API: `/services/data/v60.0/sobjects/Lead`
3. Set owner based on routing:
   - routing = "KAM/Hunter Sr" â†’ OwnerId = $HUNTER_SR_SALESFORCE_ID
   - routing = "Motion/SDR" â†’ OwnerId = $SDR_MOTION_SALESFORCE_ID
4. On success: Record Salesforce Lead ID, set status = "created"
5. On error: Retry Ã—2 with backoff, then fallback to Slack (manual creation)

**Step 2: Slack Notification**
1. Determine channel:
   - routing = "KAM/Hunter Sr" â†’ #hunter-sr
   - routing = "Motion/SDR" â†’ #sdr-motion
2. Format message:
   ```
   ðŸŽ¯ HANDOFF: Nuevo lead calificado
   Brand: Brand_0145 (Hogar)
   GMV 12m: COP 4,908 MM
   Momentum: 3.25x
   Decision Maker: false (MarÃ­a ops, CFO invited)
   Objection: ninguna
   Intent Score: 85/100
   Next Step: agendar
   
   Reply: "Hi Hunter, Thanks for reaching out. We're interested..."
   
   [OPEN IN SALESFORCE BUTTON]
   ```
3. Include button linking to: `https://[instance].salesforce.com/[Lead ID]`

**Step 3: SLA & Escalation**
1. Create internal record: {lead_id, created_at, assigned_owner, channel}
2. Schedule reminders:
   - At +24h: If no activity in Salesforce â†’ send reminder to channel: "Any progress on Brand_0145?"
   - At +48h: If still no activity â†’ escalate to next level
     - If owner is SDR â†’ escalate to #sdr-motion (team review)
     - If owner is Hunter Sr â†’ escalate to #sales-leadership

**Output (created in Salesforce):**
```json
{
  "salesforce_lead_id": "00Qxx000002S5ZEAV",
  "salesforce_owner": "Hunter Jr (SDR Motion)",
  "status": "Open - Not Contacted",
  "fields_set": {
    "Company": "Brand_0145",
    "Email": "maria.rodriguez@brand0145.com",
    "xsell_score__c": 89.2,
    "bnpl_gmv_12m__c": 4908,
    "bnpl_momentum__c": 3.25,
    "cms_detected__c": "Shopify",
    "intent_score__c": 85,
    "qualification_summary__c": "Explicit interest, willing to include CFO..."
  }
}
```

---

## Retry Policies (Global)

### Strategy: Exponential Backoff + Fallback

**For all external API calls (Clay, Groq, Smartlead, Salesforce, WhatsApp):**

```
Attempt 1: Immediate
  â†“ (on error)
Wait 1 second
Attempt 2
  â†“ (on error)
Wait 2 seconds
Attempt 3 (if applicable)
  â†“ (on error)
Log error â†’ Fallback action
```

### Retry Rules by Tool:

| Tool | Error Type | Retry Count | Backoff | Fallback Action |
|---|---|---|---|---|
| Clay | Timeout / 5xx | 2 | Exp(1s, 2s) | Mark "manual_review", continue |
| Clay | No results (200 OK, empty) | 0 | N/A | Mark "manual_review", continue |
| Smartlead | 5xx / timeout | 2 | Exp(1s, 2s) | Mark "failed", Slack alert |
| Groq | 5xx / rate limit | 2 | Exp(2s, 4s) | Mark "pending_retry" + reschedule in 1h |
| Salesforce | 5xx / timeout | 2 | Exp(1s, 2s) | Fallback to Slack (manual) |
| 360dialog | Timeout / invalid number | 2 | Exp(1s, 2s) | Mark "whatsapp_failed", log, continue |

**Note:** If any single brand encounters >2 failures across the pipeline, mark as "escalate_to_manual" and notify Hunter Sr via Slack.

---

## Error Handling & Observability

### Slack Alerts (#automation channel)

**All failures log to Slack with:**
- Timestamp
- Workflow name
- Brand ID
- Error message (first 200 chars)
- Action taken (retry / manual_review / discard)

**Example:**
```
âš ï¸ WF-2 Enrichment Error
Workflow: WF-2 enrichment
Brand: Brand_0145
Error: Clay API timeout after 2 retries
Action: Marked for manual enrichment review
Timestamp: 2026-07-15T10:45:00Z
Next: Hunter Sr to manually research contacto details
```

### Logging Levels

- **INFO:** Workflow start/end, item count processed, successful API calls
- **WARN:** Retry attempts, fallback to manual, rate limit warnings
- **ERROR:** API failures after retries, JSON parsing failures, missing data

### Monitoring Dashboard (Future)

- Daily: Count of brands processed, success rate, retry rate
- Weekly: Error patterns, Clay fallback rate, manual review backlog
- Monthly: End-to-end pipeline conversion, cost per qualified lead

---

## Environment Variables Required

**All environment variables must be set before importing workflows into n8n.**

```bash
# Google Sheets
GOOGLE_SHEETS_ID=<spreadsheet ID>
GOOGLE_CREDENTIALS_JSON=<path to service account JSON>

# Clay API
CLAY_API_KEY=<API key from Clay dashboard>

# Smartlead (Email)
SMARTLEAD_API_KEY=<API key>
SMARTLEAD_CAMPAIGN_ID=<campaign ID for BNPL outreach>

# WhatsApp (360dialog)
WHATSAPP_360DIALOG_API_KEY=<API key>
WHATSAPP_PHONE_NUMBER_ID=<registered phone number ID>
WHATSAPP_BOOKING_LINK=https://addi-book.typeform.com/to/mp-xsell

# Groq API
GROQ_API_KEY=<API key from Groq dashboard>

# Salesforce
SALESFORCE_CLIENT_ID=<OAuth app client ID>
SALESFORCE_CLIENT_SECRET=<OAuth app secret>
SALESFORCE_INSTANCE_URL=https://addi--c.salesforce.com
HUNTER_SR_SALESFORCE_ID=<18-char user ID>
SDR_MOTION_SALESFORCE_ID=<18-char user ID>

# Slack
SLACK_BOT_TOKEN=xoxb-...
SLACK_CHANNEL_AUTOMATION=#automation
SLACK_CHANNEL_HUNTER_SR=#hunter-sr
SLACK_CHANNEL_SDR_MOTION=#sdr-motion
SLACK_CHANNEL_SALES_LEADERSHIP=#sales-leadership

# n8n
N8N_HOST=http://localhost:5678  (if self-hosted)
N8N_API_KEY=<n8n API key>
```

---

## Testing Checklist

**Before deploying to production:**

- [ ] WF-1: Test CSV read, output 15 Tier A + 35 Tier B rows to test Google Sheet
- [ ] WF-2: Test Clay API call with 1 brand, verify enrichment fields populated
- [ ] WF-2: Test Clay retry logic (mock failure on first call, verify retry succeeds)
- [ ] WF-3: Test email merge fields (check {{gmv_cop_millions_12m}} renders as "4908", not "4,908")
- [ ] WF-3: Test WhatsApp branch (IF opt_in=true, then send; IF opt_in=false, skip)
- [ ] WF-4: Test Groq API with 1 reply, verify JSON output parsed correctly
- [ ] WF-4: Test JSON parsing failure recovery (mock invalid JSON, verify retry + manual_review)
- [ ] WF-5: Test Salesforce Lead creation with test org / sandbox
- [ ] WF-5: Test Slack notification formatting (emoji, link, merge fields)
- [ ] WF-5: Test SLA reminder scheduling (set to +5 min for testing, verify Slack message at +5 min)
- [ ] All: Test error handling (mock API timeout, verify Slack alert + retry)

---

## Deployment Steps

1. **Create environment file:** `.env` in n8n directory with all vars above
2. **Import workflows:** n8n UI â†’ Workflows â†’ Import â†’ select `wf1...wf5.json`
3. **Activate credentials:** n8n UI â†’ Credentials â†’ configure each tool (Clay, Smartlead, etc.)
4. **Set env var references:** In each workflow, replace hardcoded values with `{{ env.VAR_NAME }}`
5. **Test WF-1:** Manually trigger cron or "Execute Workflow" to verify CSV read + GSheet write
6. **Test end-to-end:** Run with sample data (1 Tier B brand from top50.csv)
7. **Enable production triggers:** Activate cron for WF-1 (Monday 6 AM COT)
8. **Monitor:** Slack alerts, check Google Sheet updates daily

---

## Rollback Plan

**If a workflow fails in production:**
1. Slack alert triggers â†’ team notified
2. Pause affected workflow (disable trigger)
3. Check error log in Slack + n8n audit trail
4. Fix issue (e.g., API key expired, schema change)
5. Test in sandbox
6. Re-enable workflow
7. Log incident (postmortem if >1 hour downtime)

**Data integrity:** All processed brands logged to Google Sheet; if workflow fails mid-batch, re-run from last checkpoint (WF supports idempotency via brand_id lookup).

---

## Performance SLAs

| Workflow | Target Runtime | Trigger | Notes |
|---|---|---|---|
| WF-1 | <5 min | Weekly cron Mon 6 AM | Read CSV, split, write 2 tabs |
| WF-2 | 30 min | After WF-1 | 35 brands Ã— ~50ms per Clay call = 1.75s + overhead |
| WF-3 | Async (Days 0/2/5) | After WF-2 d0, after WF-2 d2, etc. | Email send <100ms, task gen <1s |
| WF-4 | 10 sec per reply | On webhook or poll | Groq call ~1-2s, retry logic adds <2s |
| WF-5 | 5 sec per lead | On webhook from WF-4 | Salesforce + Slack notifications <2s each |

**Estimated monthly API calls:**
- Clay: 50â€“60 (enrichment)
- Groq: 50â€“100 (qualifications)
- Smartlead: 100â€“150 (emails)
- 360dialog: 20â€“40 (WhatsApp)
- Salesforce: 10â€“20 (Lead creation)

**Total estimated cost:** USD ~1,350/month (see costos.md)

---

## Known Limitations & Future Improvements

**Current (MVP):**
- Tier A NOT auto-enriched; Hunter Sr manual path
- Tier A NOT auto-scored; Hunter Sr qualifies manually
- Google Sheets as staging (not Databricks)
- LinkedIn manual only (no bot risk)

**Phase 2 (M3):**
- Batch Clay enrichment (API optimization)
- Salesforce lead dedupe (check existing Account before create Lead)
- Tier A auto-enrichment (with lower frequency than Tier B)
- Opportunity auto-creation (post-discovery call webhook)
- Analytics dashboard (N8n built-in or Streamlit)

**Phase 3 (M6+):**
- BNPL propensity model (ML, predict reply rate by brand profile)
- A/B testing framework (Smartlead variants, track open rate)
- Self-hosted LLM (Llama 2) for classification (cost save ~USD 100/month)
- Slack threaded replies (keep context per lead across multiple touches)

