"""Cloud Translation + Text-to-Speech adapters (REST, GOOGLE_CLOUD_API_KEY). Demo mode: no machine
translation (approved templates only) and the dashboard plays a browser speech-synthesis preview."""
import httpx

from app import integrations
from app.config import settings

TTS_VOICES = {"en": "en-IN", "bn": "bn-IN", "or": "or-IN"}


def translate(text: str, target: str, source: str = "en") -> dict:
    if integrations.translation_enabled():
        try:
            r = httpx.post("https://translation.googleapis.com/language/translate/v2",
                           params={"key": settings.google_cloud_api_key},
                           json={"q": text, "source": source, "target": target, "format": "text"}, timeout=20)
            r.raise_for_status()
            integrations.clear_error("translation_tts")
            return {"text": r.json()["data"]["translations"][0]["translatedText"], "mode": "real",
                    "engine": "Cloud Translation v2", "requires_review": True}
        except Exception as exc:  # noqa: BLE001
            integrations.record_error("translation_tts", exc)
    return {"text": None, "mode": "demo", "engine": "none (use approved templates)", "requires_review": True,
            "note": "Machine translation not configured; advisories use pre-approved en/or/bn templates."}


def text_to_speech(text: str, language: str) -> dict:
    lang = TTS_VOICES.get(language, "en-IN")
    if integrations.translation_enabled():
        try:
            r = httpx.post("https://texttospeech.googleapis.com/v1/text:synthesize",
                           params={"key": settings.google_cloud_api_key},
                           json={"input": {"text": text}, "voice": {"languageCode": lang},
                                 "audioConfig": {"audioEncoding": "MP3"}}, timeout=30)
            r.raise_for_status()
            integrations.clear_error("translation_tts")
            return {"mode": "real", "engine": "Cloud Text-to-Speech", "language_code": lang,
                    "audio_url": "data:audio/mpeg;base64," + r.json()["audioContent"]}
        except Exception as exc:  # noqa: BLE001
            integrations.record_error("translation_tts", exc)
    return {"mode": "demo", "engine": "browser speechSynthesis preview", "language_code": lang, "audio_url": None,
            "text": text}
