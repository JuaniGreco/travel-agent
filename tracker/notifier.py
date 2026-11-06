"""Notificador instantáneo de alertas (Discord, Telegram, Webhook genérico).

Especialmente útil para promociones relámpago de Black Friday donde las tarifas
con descuento duran pocas horas.
Implementado con la biblioteca estándar (urllib.request) para no requerir dependencias extra.
"""
from __future__ import annotations

import json
import logging
import urllib.error
import urllib.request
from typing import Optional

from .env import get_str
from .models import Alert

logger = logging.getLogger("tracker.notifier")


def _post_json(url: str, payload: dict, timeout_s: float = 10.0) -> bool:
    try:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json", "User-Agent": "TravelAgent-Florida2027/1.0"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=timeout_s) as resp:
            return 200 <= resp.status < 300
    except Exception as exc:
        logger.warning(f"Error al enviar notificación a {url}: {exc}")
        return False


def send_discord(webhook_url: str, alerts: list[Alert], trip_name: str) -> bool:
    """Envía un mensaje con embeds atractivos a un canal de Discord."""
    if not webhook_url or not alerts:
        return False

    color_map = {
        "AHORRO DIRECTO": 0x2ECC71,    # Verde
        "PRIVACIDAD": 0x3498DB,        # Azul
        "UPGRADE": 0x9B59B6,           # Violeta
        "MÍNIMO HISTÓRICO": 0xE67E22,   # Naranja
    }

    fields = []
    for a in alerts:
        title = f"[{a.kind}] {a.target}"
        val = a.message
        if a.suspicious:
            val += "\n⚠️ *Verificar: posible precio por noche o sin impuestos.*"
        fields.append({"name": title, "value": val, "inline": False})

    payload = {
        "username": "Florida 2027 Price Tracker",
        "avatar_url": "https://img.icons8.com/fluency/96/beach.png",
        "embeds": [
            {
                "title": f"🚨 ¡Nuevas alertas de viaje! – {trip_name}",
                "description": f"Se detectaron **{len(alerts)}** oportunidades de precio.",
                "color": color_map.get(alerts[0].kind, 0xF1C40F),
                "fields": fields[:25],
                "footer": {"text": "Travel Agent · Automatización Florida 2027"},
            }
        ],
    }
    return _post_json(webhook_url, payload)


def send_telegram(bot_token: str, chat_id: str, alerts: list[Alert], trip_name: str) -> bool:
    """Envía un mensaje con formato Markdown a un chat o canal de Telegram."""
    if not bot_token or not chat_id or not alerts:
        return False

    lines = [f"🚨 *¡Alertas de viaje Florida 2027!* ({trip_name})\n"]
    for a in alerts:
        flag = " ⚠️ *(verificar precio)*" if a.suspicious else ""
        lines.append(f"• *[{a.kind}] {a.target}*\n  {a.message}{flag}")

    text = "\n".join(lines)
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True,
    }
    return _post_json(url, payload)


def dispatch_alerts(
    alerts: list[Alert],
    trip_name: str,
    discord_url: Optional[str] = None,
    telegram_token: Optional[str] = None,
    telegram_chat: Optional[str] = None,
) -> dict[str, bool]:
    """Despacha las alertas a todos los canales configurados."""
    if not alerts:
        return {}

    discord_url = discord_url if discord_url is not None else get_str("DISCORD_WEBHOOK_URL")
    telegram_token = telegram_token if telegram_token is not None else get_str("TELEGRAM_BOT_TOKEN")
    telegram_chat = telegram_chat if telegram_chat is not None else get_str("TELEGRAM_CHAT_ID")

    results = {}
    if discord_url:
        results["discord"] = send_discord(discord_url, alerts, trip_name)
    if telegram_token and telegram_chat:
        results["telegram"] = send_telegram(telegram_token, telegram_chat, alerts, trip_name)

    return results

