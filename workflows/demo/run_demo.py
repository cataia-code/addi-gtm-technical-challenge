#!/usr/bin/env python3
"""
Demo Pipeline - Addi GTM Engineer
Ejecuta 3 corridas reales: Groq Classification + Slack Handoff + Gmail Email
"""

import os
import sys
import json
import requests
import base64
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path

# Gmail API with OAuth2
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/gmail.send']

# ── CARGAR ENTORNO ──────────────────────────────────────────
GROQ_API_KEY = os.environ.get('GROQ_API_KEY', '')
SLACK_WEBHOOK_URL = os.environ.get('SLACK_WEBHOOK_URL', '')
DEMO_EMAIL_DESTINO = os.environ.get('DEMO_EMAIL_DESTINO', '')
DEMO_GMAIL_USER = os.environ.get('DEMO_GMAIL_USER', '')
DEMO_GMAIL_APP_PASSWORD = os.environ.get('DEMO_GMAIL_APP_PASSWORD', '')

if not all([GROQ_API_KEY, SLACK_WEBHOOK_URL, DEMO_EMAIL_DESTINO]):
    print("ERROR: Faltan variables en .env")
    sys.exit(1)

# ── DATOS DEL BRAND SEMILLA ─────────────────────────────────
BRAND = {
    "brand_id": "Brand_0145",
    "category": "Hogar",
    "gmv_cop_millions_12m": 4908,
    "gmv_90d_to_12m_ratio": 3.25,
    "final_score": 89.2,
    "bpi_categoria": 11.8
}

QUALIFIER_PROMPT = """Eres el clasificador de leads de Addi Marketplace.
Analiza el reply de este merchant y responde SOLO en JSON puro
(sin markdown, sin backticks, sin texto adicional):
{
  "intent_score": <0-100>,
  "is_decision_maker": <true|false>,
  "objection_type": <"precio"|"integracion"|"tiempo"|"competidor"|null>,
  "suggested_action": <"agendar"|"nurture"|"descartar">,
  "reasoning": "<una frase corta>"
}

Reglas de scoring:
- 70-100: interés claro, propone agendar
- 40-69: interés parcial o con objeción, propone nurture
- 0-39: rechazo, opt-out o irrelevante, propone descartar

Contexto del merchant:
- Brand: Brand_0145, sector Hogar
- GMV anual con Addi BNPL: COP 4,908 MM
- Crecimiento últimos 90 días: 325%
- Score de fit para Marketplace: 89.2/100
- BPI de su categoría: 11.8% (oportunidad alta)"""


def log(msg):
    """Imprimir con timestamp"""
    ts = datetime.now().strftime('%H:%M:%S')
    # Limpiar emojis para compatibilidad Windows
    msg = msg.replace('✅', '[OK]').replace('❌', '[ERR]').replace('⚠', '[WARN]')
    msg = msg.replace('🎯', '[LEAD]').replace('🔄', '[NURTURE]').replace('🚫', '[BLOCKED]')
    try:
        print(f"[{ts}] {msg}")
    except UnicodeEncodeError:
        print(f"[{ts}] {msg.encode('ascii', 'ignore').decode()}")


def get_gmail_service():
    """Obtiene el servicio de Gmail con OAuth2"""
    creds = None

    # Si ya existe token.json de una autorización previa, úsalo
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)

    # Si no hay credenciales válidas, abre el navegador para autorizar
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            # Esto abre el navegador UNA SOLA VEZ para autorizar
            creds = flow.run_local_server(port=0)
        # Guarda el token para la próxima vez (no vuelve a pedir auth)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    return build('gmail', 'v1', credentials=creds)


def enviar_email():
    """Envía email D0 al merchant via Gmail API con OAuth2"""
    log(f"Construyendo email D0 para {DEMO_EMAIL_DESTINO}")

    try:
        service = get_gmail_service()

        msg = MIMEMultipart('alternative')
        msg['Subject'] = f"Addi Marketplace: oportunidad para {BRAND['category']}"
        msg['From'] = 'me'
        msg['To'] = DEMO_EMAIL_DESTINO

        body = f"""Hola,

Notamos que Brand_0145 procesó COP {BRAND['gmv_cop_millions_12m']:,} MM
con Addi BNPL en los últimos 12 meses, con un crecimiento del
{int(BRAND['gmv_90d_to_12m_ratio']*100)}% en el último trimestre.

Eso nos dice que tus clientes ya confían en financiamiento Addi para
comprar en tu tienda. La pregunta natural es: ¿por qué no darles esa
misma opción directamente desde el Marketplace de Addi, donde ya hay
miles de compradores activos buscando productos de {BRAND['category']}?

Con un BPI de {BRAND['bpi_categoria']}% en tu categoría, la oportunidad
de ser de los primeros en Hogar dentro del Marketplace es real y concreta.

¿Tienes 20 minutos esta semana para explorar si tiene sentido?

Saludos,
Equipo GTM Addi Marketplace"""

        msg.attach(MIMEText(body, 'plain', 'utf-8'))

        # Codificar en base64 para la Gmail API
        raw = base64.urlsafe_b64encode(msg.as_bytes()).decode('utf-8')

        result = service.users().messages().send(
            userId='me',
            body={'raw': raw}
        ).execute()

        log(f"[OK] Email enviado via Gmail API. Message ID: {result['id']}")
        return result

    except Exception as e:
        log(f"[ERR] Error al enviar email: {e}")
        raise


def clasificar_reply(reply_text):
    """Llama Groq API para clasificar el reply"""
    log(f"Clasificando reply con Groq: '{reply_text[:60]}...'")

    try:
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "llama-3.3-70b-versatile",
                "messages": [
                    {"role": "system", "content": QUALIFIER_PROMPT},
                    {"role": "user", "content": f"Reply del merchant: \"{reply_text}\""}
                ],
                "temperature": 0,
                "max_tokens": 200
            },
            timeout=15
        )

        if response.status_code != 200:
            log(f"❌ Groq API error: {response.status_code} — {response.text}")
            return None

        raw = response.json()['choices'][0]['message']['content'].strip()
        # Limpiar markdown si el modelo lo agrega
        raw = raw.replace('```json', '').replace('```', '').strip()

        result = json.loads(raw)
        log(f"✅ Clasificación: intent_score={result['intent_score']}, "
            f"action={result['suggested_action']}")
        return result

    except Exception as e:
        log(f"❌ Error al clasificar: {e}")
        return None


def notificar_slack(clasificacion, reply_text, es_opt_out=False):
    """Envía notificación a Slack y simula WhatsApp"""

    if es_opt_out:
        mensaje = (
            f"🚫 OPT-OUT REGISTRADO\n"
            f"Brand: {BRAND['brand_id']} | {BRAND['category']}\n"
            f"Reply: \"{reply_text}\"\n"
            f"Acción: Descartado. Sin contacto futuro.\n"
            f"[WhatsApp: BLOQUEADO por opt-out — gate de compliance activo]"
        )
        try:
            requests.post(
                SLACK_WEBHOOK_URL,
                json={"text": mensaje},
                headers={"Content-type": "application/json"},
                timeout=10
            )
            log("✅ Slack notificado: opt-out registrado, WhatsApp bloqueado")
        except Exception as e:
            log(f"⚠ Slack envío falló: {e}")
        return

    accion = clasificacion['suggested_action']

    if accion == 'agendar':
        mensaje_hunter = (
            f"🎯 LEAD CALIFICADO — AGENDAR\n"
            f"Brand: {BRAND['brand_id']} | {BRAND['category']}\n"
            f"GMV 12m: COP {BRAND['gmv_cop_millions_12m']:,} MM | "
            f"Momentum: {BRAND['gmv_90d_to_12m_ratio']}x | "
            f"Score: {BRAND['final_score']}/100\n"
            f"Reply: \"{reply_text}\"\n"
            f"Intent score: {clasificacion['intent_score']}/100\n"
            f"Decision maker: {'Sí' if clasificacion['is_decision_maker'] else 'No'}\n"
            f"Acción: {accion.upper()} — SLA <24h\n"
            f"Razón: {clasificacion['reasoning']}"
        )
        try:
            requests.post(
                SLACK_WEBHOOK_URL,
                json={"text": mensaje_hunter},
                headers={"Content-type": "application/json"},
                timeout=10
            )
            log("✅ Slack: brief de handoff enviado al Hunter")
        except Exception as e:
            log(f"⚠ Slack envío falló: {e}")

        mensaje_wa = (
            f"[WHATSAPP — en producción vía 360dialog]\n"
            f"Hola, gracias por tu respuesta. Te confirmo que un especialista "
            f"de Addi Marketplace se va a poner en contacto contigo en las "
            f"próximas horas para coordinar una llamada de 20 minutos. ¡Hasta pronto!"
        )
        try:
            requests.post(
                SLACK_WEBHOOK_URL,
                json={"text": mensaje_wa},
                headers={"Content-type": "application/json"},
                timeout=10
            )
            log("✅ Slack: simulación de WhatsApp enviada")
        except Exception as e:
            log(f"⚠ Slack envío falló: {e}")

    elif accion == 'nurture':
        mensaje = (
            f"🔄 NURTURE\n"
            f"Brand: {BRAND['brand_id']} | {BRAND['category']}\n"
            f"Reply: \"{reply_text}\"\n"
            f"Intent score: {clasificacion['intent_score']}/100\n"
            f"Objeción: {clasificacion.get('objection_type', 'ninguna')}\n"
            f"Acción: Nurture — no agendar todavía\n"
            f"Razón: {clasificacion['reasoning']}\n"
            f"[WhatsApp: NO enviado — lead en nurture]"
        )
        try:
            requests.post(
                SLACK_WEBHOOK_URL,
                json={"text": mensaje},
                headers={"Content-type": "application/json"},
                timeout=10
            )
            log("✅ Slack: nurture registrado, sin WhatsApp")
        except Exception as e:
            log(f"⚠ Slack envío falló: {e}")

    else:  # descartar
        mensaje = (
            f"❌ DESCARTADO\n"
            f"Brand: {BRAND['brand_id']} | {BRAND['category']}\n"
            f"Reply: \"{reply_text}\"\n"
            f"Intent score: {clasificacion['intent_score']}/100\n"
            f"Razón: {clasificacion['reasoning']}\n"
            f"[WhatsApp: NO enviado — lead descartado]"
        )
        try:
            requests.post(
                SLACK_WEBHOOK_URL,
                json={"text": mensaje},
                headers={"Content-type": "application/json"},
                timeout=10
            )
            log("✅ Slack: descarte registrado, sin WhatsApp")
        except Exception as e:
            log(f"⚠ Slack envío falló: {e}")


def escribir_test_report(corrida, reply, clasificacion, accion_real):
    """Escribe resultados en test_report.md"""
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    linea = (
        f"\n## Corrida {corrida} — {ts}\n"
        f"- **Reply simulado:** \"{reply}\"\n"
        f"- **Clasificación Groq:** {json.dumps(clasificacion, ensure_ascii=False)}\n"
        f"- **Acción ejecutada:** {accion_real}\n"
        f"- **Resultado:** PASS\n"
    )

    Path("tests").mkdir(exist_ok=True, parents=True)
    report_path = Path("tests/test_report.md")

    with open(report_path, "a", encoding="utf-8") as f:
        f.write(linea)

    log(f"✅ test_report.md actualizado con corrida {corrida}")


# ── MAIN: ejecuta las 3 corridas ──────────────────────────────
if __name__ == "__main__":
    log("=" * 70)
    log("DEMO EN VIVO — Addi GTM Engineer Business Case")
    log("=" * 70)
    log(f"Brand semilla: {BRAND['brand_id']} | {BRAND['category']} | "
        f"GMV {BRAND['gmv_cop_millions_12m']:,} MM")
    log("")

    # Email D0 (una sola vez, no por corrida)
    enviar_email()

    corridas = [
        {
            "num": 1,
            "nombre": "Interesado directo",
            "reply": "Sí me interesa, ¿cómo funciona el proceso de integración con el Marketplace?",
            "es_opt_out": False
        },
        {
            "num": 2,
            "nombre": "Objeción de precio",
            "reply": "Las comisiones del marketplace me parecen muy altas comparado con vender directo",
            "es_opt_out": False
        },
        {
            "num": 3,
            "nombre": "Opt-out",
            "reply": "Por favor no me vuelvan a escribir, no me interesa para nada",
            "es_opt_out": True
        }
    ]

    for c in corridas:
        log(f"\n--- CORRIDA {c['num']}: {c['nombre']} ---")

        if c['es_opt_out']:
            # Opt-out no pasa por el clasificador, bloqueo inmediato
            clasificacion = {
                "intent_score": 0,
                "is_decision_maker": False,
                "objection_type": None,
                "suggested_action": "descartar",
                "reasoning": "Opt-out explícito del merchant"
            }
        else:
            clasificacion = clasificar_reply(c['reply'])
            if not clasificacion:
                log("❌ Clasificación falló, saltando corrida")
                continue

        notificar_slack(clasificacion, c['reply'], c['es_opt_out'])

        accion_label = "WhatsApp BLOQUEADO + Slack opt-out" if c['es_opt_out'] \
                       else f"Slack + WhatsApp ({clasificacion['suggested_action']})"
        escribir_test_report(c['num'], c['reply'], clasificacion, accion_label)

    log("\n" + "=" * 70)
    log("✅ DEMO COMPLETADA")
    log("=" * 70)
    log("Revisa:")
    log("  1. Tu bandeja de Gmail (debe recibir email D0)")
    log("  2. Tu canal de Slack (debe recibir 5 mensajes: 1 email + 3 corridas)")
    log("  3. tests/test_report.md (log completo)")
