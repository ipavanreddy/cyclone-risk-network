"""Cloud Translation, Text-to-Speech and Speech-to-Text adapters (REST, GOOGLE_CLOUD_API_KEY).

- Translation is a reviewer aid (back-translation of an approved-template advisory into English); life-safety
  wording itself comes from pre-approved templates (PRD §18).
- Text-to-Speech renders the advisory as MP3 and archives it in Cloud Storage (advisory audio, PRD §28).
  Cloud TTS has no Odia (or-IN) voice, so Odia falls back to the browser speech-synthesis preview; that is a
  language gap, not an integration failure.
- Speech-to-Text reads the generated audio back so the officer can check the voice advisory is intelligible.
Demo mode: no machine translation, browser speech preview, no read-back.
"""
import base64
import hashlib
from functools import lru_cache

import httpx

from app import integrations, media
from app.config import settings

TTS_VOICES = {"en": "en-IN", "bn": "bn-IN", "or": "or-IN"}


def translate(text: str, target: str, source: str = "en") -> dict:
    if integrations.translation_enabled():
        try:
            r = httpx.post("https://translation.googleapis.com/language/translate/v2",
                           params={"key": settings.google_cloud_api_key},
                           json={"q": text, "source": source, "target": target, "format": "text"}, timeout=20)
            r.raise_for_status()
            integrations.clear_error("translation")
            return {"text": r.json()["data"]["translations"][0]["translatedText"], "mode": "real",
                    "engine": "Cloud Translation v2", "requires_review": True}
        except Exception as exc:  # noqa: BLE001
            integrations.record_error("translation", exc)
    return {"text": None, "mode": "demo", "engine": "none (use approved templates)", "requires_review": True,
            "note": "Machine translation not configured; advisories use pre-approved en/or/bn templates."}


@lru_cache(maxsize=8)
def tts_voice_available(language_code: str) -> bool:
    r = httpx.get("https://texttospeech.googleapis.com/v1/voices",
                  params={"key": settings.google_cloud_api_key, "languageCode": language_code}, timeout=15)
    r.raise_for_status()
    return any(language_code in v.get("languageCodes", []) for v in r.json().get("voices", []))


def _browser_fallback(text: str, lang: str, note: str) -> dict:
    return {"mode": "demo", "engine": "browser speechSynthesis preview", "language_code": lang, "audio_url": None,
            "text": text, "note": note}


def text_to_speech(text: str, language: str, advisory_id: str | None = None) -> dict:
    lang = TTS_VOICES.get(language, "en-IN")
    if not integrations.tts_enabled():
        return _browser_fallback(text, lang, "Text-to-Speech not configured")
    key = hashlib.sha256(f"{lang}|{text}".encode()).hexdigest()[:16]
    path = f"advisory-audio/{advisory_id or 'adhoc'}/{lang}-{key}.mp3"
    try:
        if not tts_voice_available(lang):
            return _browser_fallback(text, lang, f"Cloud Text-to-Speech has no {lang} voice yet; browser preview used")
        audio = media.download(path) if media.exists(path) else None
        cached = audio is not None
        if audio is None:
            r = httpx.post("https://texttospeech.googleapis.com/v1/text:synthesize",
                           params={"key": settings.google_cloud_api_key},
                           json={"input": {"text": text}, "voice": {"languageCode": lang},
                                 "audioConfig": {"audioEncoding": "MP3"}}, timeout=30)
            r.raise_for_status()
            audio = base64.b64decode(r.json()["audioContent"])
        integrations.clear_error("text_to_speech")
        gcs_uri = (f"gs://{settings.gcs_bucket}/{media.PREFIX}/{path}" if cached
                   else media.upload(path, audio, "audio/mpeg"))
        return {"mode": "real", "engine": "Cloud Text-to-Speech", "language_code": lang, "cached": cached,
                "gcs_uri": gcs_uri, "audio_url": "data:audio/mpeg;base64," + base64.b64encode(audio).decode()}
    except Exception as exc:  # noqa: BLE001
        integrations.record_error("text_to_speech", exc)
        return _browser_fallback(text, lang, "Cloud Text-to-Speech failed; browser preview used")


def speech_to_text(audio_b64: str, language: str, encoding: str = "MP3", sample_rate_hz: int = 24000) -> dict:
    lang = TTS_VOICES.get(language, "en-IN")
    if integrations.stt_enabled():
        try:
            r = httpx.post("https://speech.googleapis.com/v1/speech:recognize",
                           params={"key": settings.google_cloud_api_key},
                           json={"config": {"encoding": encoding, "sampleRateHertz": sample_rate_hz,
                                            "languageCode": lang, "enableAutomaticPunctuation": True},
                                 "audio": {"content": audio_b64}}, timeout=60)
            r.raise_for_status()
            results = r.json().get("results") or []
            alts = [res["alternatives"][0] for res in results if res.get("alternatives")]
            integrations.clear_error("speech_to_text")
            return {"mode": "real", "engine": "Cloud Speech-to-Text v1", "language_code": lang,
                    "transcript": " ".join(a.get("transcript", "") for a in alts).strip(),
                    "confidence": round(min((a.get("confidence", 0) for a in alts), default=0), 2)}
        except Exception as exc:  # noqa: BLE001
            integrations.record_error("speech_to_text", exc)
    return {"mode": "demo", "engine": "none", "language_code": lang, "transcript": None,
            "note": "Speech-to-Text not configured; no audio read-back check."}
