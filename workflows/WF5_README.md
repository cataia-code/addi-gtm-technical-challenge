# WF-5: Handoff (Salesforce Simulado + Slack)

## Resumen

WF-5 no usa una credencial real de Salesforce en el demo. Un nodo Code arma el payload con el mismo contrato de campos y lo imprime en logs. Slack recibe el resumen del handoff.

## Comportamiento

1. Recibe el payload clasificado desde WF-4.
2. Construye el payload Salesforce local.
3. Imprime el payload en consola.
4. Notifica a Slack.

## Contrato

Mantener estos campos:

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

## Nota de producción

"Salesforce se simula como log local; en producción este nodo Code se reemplaza por un HTTP Request real a la API de Salesforce con el mismo payload."
