"""
Notificaciones y Alertas Instantáneas a Telegram / WhatsApp — HuntJob Chile.

Envia alertas en tiempo real cuando se detecta una oferta laboral con Match ATS > 85%
para que el candidato postule de inmediato.
"""

import os
import requests

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "8801493170:AAF1KwZbFGKTtap5DIEkhU2oy0bWRO6Apdo")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "5116730522")


def enviar_alerta_oferta_destacada(titulo: str, empresa: str, score_ats: int, enlace_oferta: str = "") -> bool:
    """
    Envía una notificación enriquecida a Telegram con la alerta de trabajo detectado.
    """
    if score_ats < 80:
        return False

    emoji_score = "🔥" if score_ats >= 90 else "🎯"
    enlace_txt = f"\n👉 [Ver y Postular en HuntJob]({enlace_oferta})" if enlace_oferta else ""

    mensaje = (
        f"🚨 *NUEVA OFERTA LABORAL MATCH ALTO* 🚨\n\n"
        f"💼 *Cargo:* {titulo}\n"
        f"🏢 *Empresa:* {empresa}\n"
        f"{emoji_score} *Compatibilidad ATS:* *{score_ats}%*\n\n"
        f"✨ Tu CV cumple con las competencias clave requeridas.{enlace_txt}"
    )

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": mensaje,
        "parse_mode": "Markdown"
    }

    try:
        res = requests.post(url, json=payload, timeout=10)
        return res.status_code == 200
    except Exception as e:
        print(f"Error enviando alerta Telegram HuntJob: {e}")
        return False
