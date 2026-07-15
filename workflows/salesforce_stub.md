# Salesforce Stub & Field Mapping (WF-5)

WF-5 does not call Salesforce in the demo. It builds the same payload locally, logs it, and sends Slack. In production, the Code node is replaced by a real Salesforce API call with the same payload.

## Payload Contract

### Standard fields

- `FirstName`
- `LastName`
- `Company`
- `Email`
- `Phone`
- `LeadSource`
- `Status`
- `OwnerId`

### Custom fields

- `xsell_score__c`
- `bnpl_gmv_12m__c`
- `bnpl_momentum__c`
- `cms_detected__c`
- `qualification_summary__c`
- `intent_score__c`
- `objection_type__c`
- `suggested_action__c`
- `linkedin_url__c`
- `enrichment_status__c`

## Field Mapping

| Source | Salesforce field |
|---|---|
| `brand_id` | `Company` |
| `contacto_nombre` | `FirstName` + `LastName` |
| `contacto_email` | `Email` |
| `phone` | `Phone` |
| `final_score` | `xsell_score__c` |
| `gmv_cop_millions_12m` | `bnpl_gmv_12m__c` |
| `gmv_90d_to_12m_ratio` | `bnpl_momentum__c` |
| `cms_detectado` | `cms_detected__c` |
| `reasoning` | `qualification_summary__c` |
| `intent_score` | `intent_score__c` |
| `objection_type` | `objection_type__c` |
| `suggested_action` | `suggested_action__c` |
| `linkedin_url` | `linkedin_url__c` |
| `enrichment_status` | `enrichment_status__c` |

## Example payload

```json
{
  "FirstName": "Maria",
  "LastName": "Rodriguez",
  "Company": "Brand_0145",
  "Email": "maria@brand0145.com",
  "LeadSource": "Inbound - Addi Marketplace Motion",
  "Status": "Open - Not Contacted",
  "OwnerId": "KAM_HUNTER_SR_LOCAL",
  "xsell_score__c": 89.2,
  "bnpl_gmv_12m__c": 4908,
  "bnpl_momentum__c": 3.25,
  "cms_detected__c": "Shopify",
  "qualification_summary__c": "Explicit interest, willing to include CFO.",
  "intent_score__c": 85,
  "objection_type__c": null,
  "suggested_action__c": "agendar",
  "linkedin_url__c": "https://linkedin.com/in/maria-rodriguez-123/",
  "enrichment_status__c": "success"
}
```
