"""Sandbox dispatch channels. Real only when sandbox credentials are set; otherwise simulated and logged.
- sms: Twilio (test credentials recommended) — SMS_SANDBOX_KEY="ACCOUNT_SID:AUTH_TOKEN", SMS_SANDBOX_FROM/TO
- messaging: Telegram bot — MESSAGING_SANDBOX_TOKEN, MESSAGING_SANDBOX_CHAT_ID
- voice: simulated call (TTS audio generated when Text-to-Speech is configured)
- alert_feed: CAP message published to the platform's own feed (GET /api/alerts/feed)
"""
import httpx

from app import integrations
from app.config import settings

CHANNELS = ["sms", "messaging", "voice", "alert_feed"]


def send(channel: str, text: str, cap_xml: str | None) -> dict:
    if channel == "sms" and integrations.sms_enabled():
        try:
            sid, token = settings.sms_sandbox_key.split(":", 1)
            r = httpx.post(f"https://api.twilio.com/2010-04-01/Accounts/{sid}/Messages.json", auth=(sid, token),
                           data={"From": settings.sms_sandbox_from, "To": settings.sms_sandbox_to, "Body": text[:1500]},
                           timeout=20)
            r.raise_for_status()
            integrations.clear_error("sms")
            return {"channel": channel, "simulated": False, "provider": "twilio-sandbox",
                    "provider_id": r.json().get("sid"), "status": "sent"}
        except Exception as exc:  # noqa: BLE001
            integrations.record_error("sms", exc)
    if channel == "messaging" and integrations.messaging_enabled():
        try:
            r = httpx.post(f"https://api.telegram.org/bot{settings.messaging_sandbox_token}/sendMessage",
                           json={"chat_id": settings.messaging_sandbox_chat_id, "text": text}, timeout=20)
            r.raise_for_status()
            integrations.clear_error("messaging")
            return {"channel": channel, "simulated": False, "provider": "telegram-sandbox",
                    "provider_id": str(r.json().get("result", {}).get("message_id")), "status": "sent"}
        except Exception as exc:  # noqa: BLE001
            integrations.record_error("messaging", exc)
    if channel == "alert_feed":
        return {"channel": channel, "simulated": False, "provider": "tatraksha-cap-feed", "status": "published",
                "note": "Published to GET /api/alerts/feed (local CAP feed)"}
    return {"channel": channel, "simulated": True, "provider": "simulator", "status": "simulated",
            "note": "Sandbox credentials not configured – message recorded in dispatch log only",
            "preview": text[:160]}
