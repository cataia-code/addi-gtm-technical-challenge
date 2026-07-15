# Cost Breakdown & SaaS Budget (Monthly)

**Total Budget:** ~USD 1,500/month (within constraint of USD 3,000/month)

---

## Detailed Cost Analysis

### 1. Clay API (Data Enrichment) â€” USD 800/month

**Usage:**
- Waterfall: Apollo â†’ LinkedIn â†’ Website scrape
- Apply to: Tier B only (35 brands)
- Frequency: ~1 call per brand per month (assume 1.5x for retries + new enrichments)
- Monthly volume: 35 Ã— 1.5 = ~53 API calls

**Pricing:**
- Clay contact enrichment: ~USD 0.80â€“1.50 per successful record (depends on data quality)
- At 35 brands Ã— $1.50/contact = USD 52.50/month (if all succeed first try)
- But with retry logic + new campaigns: assume ~60 calls/month
- Projected: 60 contacts Ã— $1.33/contact = USD 80/month (actual)
- **Budget allocation:** USD 800/month (10x buffer for scaling to 300-500 brands in M3)

**Billing:**
- Pay-as-you-go or prepaid credits
- Retry logic: Max 2 retries, then fallback to manual (doesn't retry infinitely)

**Alternative Considered & Rejected:**
- **Apollo (LinkedIn):** USD 150/month
  - Cheaper but less comprehensive (no website scrape)
  - Clay waterfall includes Apollo as step 1, so more data per call
  - Rejected: Clay is better ROI for BNPL vertical (website CMS relevant for integration path)

- **Hunter.io (Email only):** USD 99/month
  - Only gets emails, not contact data
  - Rejected: We need name + email + role (Clay does all three)

---

### 2. Smartlead (Email Outreach) â€” USD 100/month

**Usage:**
- Sending emails via WF-3 (Day 0 + Day 2 variant)
- Tier B only: 35 brands Ã— 2 emails = 70 emails/month (+ retries, assume 100 emails/month)
- Tracking: Open pixel + click tracking included

**Pricing:**
- Smartlead: USD 29/month (up to 500 credits) + USD 0.05/credit overage
- 1 email = 1 credit
- 100 emails/month = 100 credits = within free tier (free up to 500)
- **Cost: Minimal, covered under USD 29/month base plan**
- **Budget allocation:** USD 100/month (buffer for additional campaigns, templates, API access)

**Alternative Considered & Rejected:**
- **Mailchimp:** USD 50/month (unlimited sends)
  - No real-time open tracking in free tier
  - Rejected: Smartlead has better engagement data + native n8n integration

- **Sendgrid:** USD 30/month (500 sends/month)
  - Good for scale but overkill for 100 emails/month
  - Rejected: Smartlead simpler + cheaper for this volume

---

### 3. n8n (Workflow Orchestration) â€” USD 50/month

**Deployment Model:**
- Self-hosted n8n on Docker (EC2 micro or local infra)
- NOT using n8n Cloud (which would be USD 150+/month)

**Infrastructure:**
- Docker container on AWS EC2 t3.micro (USD 10/month)
- n8n license: Self-hosted free tier (unlimited workflows, 2 concurrent executions)
- Database: PostgreSQL (RDS micro = USD 15/month or use local SQLite for MVP)

**Scaling Considerations:**
- Current: 5 workflows, ~50 brands, ~100â€“200 API calls/month
- Projected M3: 300 brands, ~500 API calls/month
- n8n self-hosted can handle this without premium

**Budget allocation:** USD 50/month (includes EC2 + n8n license + monitoring)

**Alternative Considered & Rejected:**
- **n8n Cloud Pro:** USD 150/month
  - Managed hosting + enterprise support
  - Not needed for MVP; self-hosted scales to M3
  - Rejected: Self-hosted saves 3Ã— cost, complexity acceptable

- **Zapier:** USD 99/month (minimal plan)
  - Easier UI but proprietary integrations
  - No self-hosted option; vendor lock-in
  - Rejected: n8n more flexible + cheaper

---

### 4. 360dialog (WhatsApp Business API) â€” USD 200/month

**Usage:**
- WhatsApp opt-in only (WF-3, Day 5)
- Tier B: 35 brands
- Assume 60% opt-in rate = ~21 messages/month + retries = ~30 messages/month
- Billing: USD 0.0032/msg (outbound, Colombia pricing may vary)

**Pricing:**
- 360dialog: Fixed monthly plan (USD 50â€“200 depending on volume cap) + per-message
- Conservative estimate: USD 50/month base + (30 messages Ã— USD 0.005 estimate) = USD 50 + USD 0.15 â‰ˆ USD 50/month
- **Budget allocation:** USD 200/month (buffer for higher opt-in rates + additional campaigns)

**Trade-offs:**
- WhatsApp Business API requires pre-approval (Facebook/Meta)
- Message templates must be pre-registered
- opt_in=true enforcement is mandatory (compliance: GDPR-like in Colombia)

**Alternative Considered & Rejected:**
- **Twilio WhatsApp:** USD 0.0075/msg (more expensive)
  - Rejected: 360dialog cheaper + easier integration in LATAM

- **SMS via Twilio:** USD 0.007/msg
  - Legal: Colombia TCPA compliance murky
  - Rejected: WhatsApp better + cheaper

- **No WhatsApp, email only:** Saves USD 200/month
  - Trade-off: Email open rate ~25%, WhatsApp read rate ~98%
  - Rejected: Small budget for high impact; test it

---

### 5. Groq API (Qualification) â€” USD 100/month

**Usage:**
- WF-4: Calling llama-3.3-70b-versatile for each reply
- Assume: ~1 reply per lead per campaign = 35 replies/month in steady state
- But with retries (JSON parsing failures) + new campaigns: ~50 calls/month

**Pricing:**
- Groq Sonnet: USD 3 per 1M input tokens + USD 15 per 1M output tokens
- Input token estimate: ~1,000 tokens per call (prompt + few-shot + reply text)
- Output: ~200 tokens per call (JSON response)
- Cost per call: (1,000 Ã— $0.000003) + (200 Ã— $0.000015) = USD 0.0066/call
- 50 calls/month Ã— USD 0.0066 = USD 0.33/month (actual)
- **Budget allocation:** USD 100/month (buffer for higher reply volume, larger contexts, M3 scaling)

**Model Choice:**
- Evaluated: Groq-opus (more expensive, not needed for JSON)
- Selected: llama-3.3-70b-versatile (balanced cost/quality)
- Temperature: 0 (deterministic, no waste)

**Alternative Considered & Rejected:**
- **GPT-4 API:** USD 0.03/1K input, USD 0.06/1K output
  - Equivalent cost but worse at structured JSON
  - Rejected: Groq better for qualification task

- **Local LLM (Ollama/Llama 2):** Free
  - Requires GPU infrastructure; overkill for simple classification
  - Quality lower for few-shot examples
  - Rejected: Groq API better ROI

---

### 6. Salesforce CRM â€” USD 0/month (existing)

**Assumption:**
- Addi already has Salesforce org (Enterprise or Sales Cloud)
- WF-5 uses existing credentials + creates custom fields
- No additional licensing required

**If starting from scratch:** USD 150/month (Sales Cloud Startup)

---

### 7. LinkedIn Sales Navigator (Optional Context for Hunter/SDR) â€” USD 100/month

**Usage:**
- Provides account/contact intelligence (not automation)
- Hunter Sr + SDR uses for research, not scripted outreach
- LinkedIn API NOT used (no bot risk)

**Pricing:**
- Sales Navigator: USD 99.99/month (1 seat, usually team subscription)

**Note:** NOT included in critical path; strictly optional for richer context on D2 LinkedIn manual touch

**Alternative Considered & Rejected:**
- **Clearbit:** USD 150/month (competitor data)
  - Good but overkill for this use case
  - Clay + Apollo already provide company data
  - Rejected: Not needed

---

## Summary Table

| Tool | Monthly Cost | Purpose | Volume/Limit | Notes |
|---|---|---|---|---|
| Clay | USD 800 | Contact enrichment (waterfall) | 35â€“60 calls/month | Buffer for M3 scaling |
| Smartlead | USD 100 | Email outreach (D0, D2 variant) | 100 emails/month | Base plan + buffer |
| n8n Self-Hosted | USD 50 | Workflow orchestration | 5 workflows, 200 API calls/month | EC2 + n8n free tier |
| 360dialog WhatsApp | USD 200 | D5 opt-in messaging | 30â€“60 messages/month | Compliance buffer |
| Groq API | USD 100 | Qualification (WF-4) | 50 calls/month | JSON structuring |
| Salesforce | USD 0 | CRM (existing) | N/A | Assumed existing license |
| LinkedIn Navigator | USD 100 | (Optional) Hunter research | Manual only | Can skip; includes below |
| **TOTAL** | **USD 1,350** | **â€” ** | **â€” ** | **Within USD 3,000 constraint** |

---

## Cash Runway to M3 (3-Month Forecast)

**Assumption:** Scaling from 50 brands to 300 brands by end of M3.

| Month | Brands | Email Sends | Clay Calls | WhatsApp Msgs | Groq Calls | Estimated Total Cost |
|---|---|---|---|---|---|---|
| M1 | 50 | 100 | 60 | 30 | 50 | USD 1,350 |
| M2 | 150 | 300 | 200 | 100 | 150 | USD 1,850 |
| M3 | 300 | 600 | 400 | 200 | 300 | USD 2,500 |

**Optimization opportunities for M3:**
1. **Batch Clay calls:** Instead of 1 per brand, batch 5 calls/API request (if Clay supports) â†’ reduce API overhead
2. **Cache Groq responses:** Store few-shot examples server-side, reduce token usage by ~30%
3. **Self-hosted email:** Deploy Postfix + open-source email tool (replace Smartlead) â†’ save USD 100/month
4. **Switch to Llama 2 locally:** If scaling to 1,000+ calls/month, break-even on GPU infrastructure

---

## Break-Even Analysis (Pipeline ROI)

**Assumption (from brief):**
- Target pipeline: 150 qualified â†’ 300 by M3
- Conversion rate (qualified â†’ customer): ~20% (industry standard for BNPL)
- Average GMV per new customer: COP 2,000 MM (estimate from mid-tier Tier B)
- Commission to Addi: 2.5% (typical BNPL)
- Annual revenue per customer: COP 2,000 MM Ã— 2.5% = COP 50 MM

**Cost vs Revenue:**
- Monthly SaaS cost: USD 1,500 = ~COP 6,000,000 (at USD 1 = COP 4,000)
- Customers needed to break even: COP 6,000,000 / COP 50,000,000 = 0.12 customers/month
- At 20% conversion from 300 qualified/month = 60 customers/month â†’ COP 3,000 MM revenue
- **Payback: 2 months (highly profitable)**

---

## Known Limitations & Risks

1. **Clay waterfall incomplete:** If Apollo doesn't have contact, LinkedIn scrape might fail
   - Mitigated: Fallback to manual enrichment (marked in WF-2)
   - Cost: ~5% of brands require manual research (not factored into budget)

2. **WhatsApp compliance:** Colombia rules on WhatsApp consent evolving
   - Mitigated: opt_in=true enforcement in WF-3
   - Cost: None, but check local regs quarterly

3. **Salesforce API rate limits:** 15 API calls/second (tight for high volume)
   - Mitigated: n8n queue + retry logic
   - Cost: None, but may need Salesforce upgrade (USD 150â€“300/month) if >1,000 leads/month

4. **Groq API availability:** Outages rare but possible
   - Mitigated: Retry Ã—2, then escalate to manual (Slack notification)
   - Cost: None, but reduces auto-scaling during outages

---

## Budget Utilization & Guardrails

**Monthly budget approved:** USD 3,000
**Allocated:** USD 1,350 (45% utilization)
**Unallocated:** USD 1,650 (buffer)

**Buffer allocation (optional):**
- USD 200: Contingency (tool failures, unexpected SLA upgrades)
- USD 400: Tier A KAM tools (Hunter Sr research budget â€” LinkedIn Premium Ã— 2 seats, etc.)
- USD 500: Scaling tooling (higher-tier Smartlead, dedicated Salesforce support, etc.)
- USD 550: Reserve for Q4 campaigns or new channels

**Reallocation trigger:** If WhatsApp opt-in rate <20%, reallocate USD 100/month to SMS or additional email campaigns.

---

## Vendor Lock-In Risk Assessment

| Tool | Lock-In Risk | Mitigation |
|---|---|---|
| Clay | Medium | Apollo fallback; data portable as CSV |
| Smartlead | Low | Open standard SMTP; can export emails |
| n8n | Low | Self-hosted; workflows portable as JSON |
| 360dialog | Medium | WhatsApp Business API is standard; template IDs portable |
| Groq | Low | Prompt + history exportable; can switch to GPT-4 with prompt refactor |
| Salesforce | High | Core CRM; but custom fields are data, not locked |

**Recommendation:** Maintain export backups of all leads + workflows monthly to mitigate lock-in.

---

## Conclusion

**This stack is optimal for a 1-person operator + AI agents because:**
1. **Minimal fixed costs** (USD 50 n8n + USD 0 Salesforce = vendor scalability)
2. **Pay-as-you-go for volume** (Clay, Smartlead, Groq scale with usage)
3. **No additional hiring** (automation absorbs manual outreach, enrichment, qualification)
4. **Profitability at 60+ customers/month** (1-2 month payback)

**Trade-offs made:**
- Manual LinkedIn (vs automation) = compliance risk, but lower CAC
- Google Sheets for staging (vs Databricks) = simplicity, but lose real-time collab (fixable)
- Clay instead of custom scraper = cost, but quality + no legal risk

**Next review:** End of M2 (after 150 brands processed) to optimize costs + evaluate scaling to 500 brands.

