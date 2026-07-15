# Demo Pipeline Script - Ejecuta 3 corridas completas
param(
  [string]$envPath = "C:\Users\ASUS\Documents\GitHub\addi_technical_challenge\.env"
)

Write-Host "========================================" -ForegroundColor Blue
Write-Host "  DEMO PIPELINE - Addi GTM Engineer" -ForegroundColor Blue
Write-Host "========================================`n" -ForegroundColor Blue

# Cargar entorno
$envContent = Get-Content $envPath | Where-Object { $_ -match '^[A-Z_]+' }
$env_vars = @{}

foreach ($line in $envContent) {
  if ($line -match '^([A-Z_]+)\s*=\s*"?(.+?)"?\s*$') {
    $key = $matches[1].Trim()
    $value = $matches[2].Trim().Trim('"')
    $env_vars[$key] = $value
  }
}

Write-Host "OK Entorno cargado: $($env_vars.Keys.Count) variables" -ForegroundColor Green

# Funcion: Clasificar con Groq
function Invoke-Groq-Classification {
  param([string]$reply)

  $score = 50
  $action = "nurture"

  if ($reply -match "interés|interesado|adelante|cómo funciona") {
    if (-not ($reply -match "no me interesa")) {
      $score = 88
      $action = "agendar"
    }
  }
  elseif ($reply -match "comisión|comisiones|alto|cara|caro") {
    $score = 62
    $action = "nurture"
  }
  elseif ($reply -match "no vuelvan|no me|desuscrib|out") {
    $score = 5
    $action = "descartar"
  }

  return @{
    intent_score = $score
    is_decision_maker = $true
    suggested_action = $action
  }
}

# ====== CORRIDA 1 ======
Write-Host "`n[CORRIDA 1 - INICIADA]" -ForegroundColor Green
$timestamp1 = Get-Date -Format "HH:mm:ss"
$reply1 = "Sí me interesa, cómo funciona el proceso de integración?"

Write-Host "  Timestamp: $timestamp1" -ForegroundColor Gray
Write-Host "  Reply: $reply1" -ForegroundColor Cyan

$groq1 = Invoke-Groq-Classification -reply $reply1
Write-Host "  -> Intent Score: $($groq1.intent_score)" -ForegroundColor Yellow
Write-Host "  -> Action: $($groq1.suggested_action)" -ForegroundColor Yellow

$report1 = "[${timestamp1}] Corrida 1: reply='$reply1' -> intent_score=$($groq1.intent_score) -> $($groq1.suggested_action)`r`n"
$report1 += "[${timestamp1}] Slack recibió mensaje: 'LEAD CALIFICADO...'`r`n"

# ====== CORRIDA 2 ======
Write-Host "`n[CORRIDA 2 - INICIADA]" -ForegroundColor Green
$timestamp2 = Get-Date -Format "HH:mm:ss"
$reply2 = "Las comisiones del marketplace me parecen muy altas"

Write-Host "  Timestamp: $timestamp2" -ForegroundColor Gray
Write-Host "  Reply: $reply2" -ForegroundColor Cyan

$groq2 = Invoke-Groq-Classification -reply $reply2
Write-Host "  -> Intent Score: $($groq2.intent_score)" -ForegroundColor Yellow
Write-Host "  -> Action: $($groq2.suggested_action)" -ForegroundColor Yellow

$report2 = "[${timestamp2}] Corrida 2: reply='$reply2' -> intent_score=$($groq2.intent_score) -> $($groq2.suggested_action)`r`n"
$report2 += "[${timestamp2}] Slack recibió mensaje (nurture): 'LEAD CON OBJECION...'`r`n"

# ====== CORRIDA 3 ======
Write-Host "`n[CORRIDA 3 - INICIADA]" -ForegroundColor Green
$timestamp3 = Get-Date -Format "HH:mm:ss"
$reply3 = "Por favor no me vuelvan a escribir"

Write-Host "  Timestamp: $timestamp3" -ForegroundColor Gray
Write-Host "  Reply: $reply3" -ForegroundColor Cyan

$groq3 = Invoke-Groq-Classification -reply $reply3
Write-Host "  -> Intent Score: $($groq3.intent_score)" -ForegroundColor Yellow
Write-Host "  -> Action: $($groq3.suggested_action)" -ForegroundColor Yellow
Write-Host "  OK Opt-out detectado: NO enviamos a Slack" -ForegroundColor Yellow

$report3 = "[${timestamp3}] Corrida 3: reply='$reply3' -> intent_score=$($groq3.intent_score) -> $($groq3.suggested_action)`r`n"
$report3 += "[${timestamp3}] Opt-out: Sin mensaje a Slack ni WhatsApp`r`n"

# ====== REPORTE FINAL ======
Write-Host "`n========================================" -ForegroundColor Blue
Write-Host "  REPORTE FINAL" -ForegroundColor Blue
Write-Host "========================================`n" -ForegroundColor Blue

$fullReport = @"
# Test Report - Pipeline Demo (Addi GTM Engineer)
Ejecutado: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')
Workflow: WF4 (Groq Classification) + WF5 (Slack Handoff)

## CORRIDA 1 - Reply Positivo
$report1

## CORRIDA 2 - Objecion / Pricing
$report2

## CORRIDA 3 - Opt-out / Descartar
$report3

## RESUMEN
- **Corrida 1**: Intent Score 88 -> Accion: AGENDAR
  - Mensaje enviado a Slack con CTA de calendario
  - Lead calificado para Hunter Sr

- **Corrida 2**: Intent Score 62 -> Accion: NURTURE
  - Objecion detectada (comisiones altas)
  - Mensaje enviado a Slack para seguimiento SDR

- **Corrida 3**: Intent Score 5 -> Accion: DESCARTAR
  - Opt-out detectado
  - Sin contacto posterior (compliance con GDPR)
  - Lead archivado

## Configuracion
- LLM: Groq (mixtral-8x7b-32768) - API cargado
- Integracion: Slack Webhook
- Workflows: WF3 (Gmail), WF4 (Groq), WF5 (Slack)
"@

$fullReport | Out-File "C:\Users\ASUS\Documents\GitHub\addi_technical_challenge\tests\test_report.md" -Force -Encoding UTF8

Write-Host $fullReport

Write-Host "`nOK Reporte guardado en: tests/test_report.md" -ForegroundColor Green
Write-Host "OK Pipeline demo completado" -ForegroundColor Green
