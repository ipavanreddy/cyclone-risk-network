"""Which integrations are real vs demo fallback. Single source of truth for the UI "Demo mode" badge.

An integration is "real" only when it is configured AND it has not failed. At startup (and on
`GET /api/status?probe=true`) every configured integration is probed with one cheap live call, so the badge
reflects what actually works, not just which env vars are set.
"""
import base64
import logging
import threading
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import UTC, datetime

from app.config import settings

log = logging.getLogger(__name__)


@dataclass
class Integration:
    name: str
    env_vars: list[str]
    configured: bool
    demo_fallback: str
    runtime_error: str | None = None
    verified_at: str | None = None
    extra: dict = field(default_factory=dict)

    @property
    def mode(self) -> str:
        if self.configured and not self.runtime_error:
            return "real"
        return "demo"


_runtime_errors: dict[str, str] = {}
_verified: dict[str, str] = {}
_probe_lock = threading.Lock()
_probe_thread: threading.Thread | None = None


def record_error(name: str, err: Exception | str) -> None:
    """Called by adapters when a configured integration fails and they fall back to demo mode."""
    _runtime_errors[name] = str(err)[:300]
    _verified.pop(name, None)


def clear_error(name: str) -> None:
    _runtime_errors.pop(name, None)
    _verified[name] = datetime.now(UTC).isoformat(timespec="seconds")


def _on(value: str | bool) -> bool:
    return bool(value) and not settings.force_demo_mode


def gemini_enabled() -> bool:
    if settings.google_genai_use_vertexai:
        return _on(settings.google_cloud_project)
    return _on(settings.gemini_api_key)


def earth_engine_enabled() -> bool:
    return _on(settings.earth_engine_project)


def translation_enabled() -> bool:
    return _on(settings.google_cloud_api_key)


def tts_enabled() -> bool:
    return _on(settings.google_cloud_api_key)


def stt_enabled() -> bool:
    return _on(settings.google_cloud_api_key)


def maps_enabled() -> bool:
    return _on(settings.maps_api_key)


def storage_enabled() -> bool:
    return _on(settings.gcs_bucket) and bool(settings.google_cloud_project)


def firestore_enabled() -> bool:
    return _on(settings.firebase_project_id)


def bigquery_enabled() -> bool:
    return _on(settings.google_cloud_project) and bool(settings.bigquery_dataset)


def sms_enabled() -> bool:
    return _on(settings.sms_sandbox_key) and ":" in settings.sms_sandbox_key and bool(settings.sms_sandbox_to)


def messaging_enabled() -> bool:
    return _on(settings.messaging_sandbox_token) and bool(settings.messaging_sandbox_chat_id)


def all_integrations() -> list[Integration]:
    gemini_via = "Vertex AI" if settings.google_genai_use_vertexai else "Gemini API"
    items = [
        Integration("gemini", ["GEMINI_API_KEY", "or GOOGLE_GENAI_USE_VERTEXAI+GOOGLE_CLOUD_PROJECT"], gemini_enabled(),
                    "Deterministic bulletin parser + template situation report/advisories (labelled demo)",
                    extra={"model": settings.gemini_model, "via": gemini_via}),
        Integration("earth_engine", ["EARTH_ENGINE_PROJECT (registered for Earth Engine)"], earth_engine_enabled(),
                    "Committed synthetic terrain grid + parametric rainfall in data/replays/"),
        Integration("maps_routes", ["MAPS_API_KEY"], maps_enabled(),
                    "Straight-line shelter distance only (no Google Routes drive time / Geocoding)"),
        Integration("translation", ["GOOGLE_CLOUD_API_KEY"], translation_enabled(),
                    "No machine back-translation; pre-approved en/or/bn templates only"),
        Integration("text_to_speech", ["GOOGLE_CLOUD_API_KEY"], tts_enabled(),
                    "Browser speech-synthesis preview"),
        Integration("speech_to_text", ["GOOGLE_CLOUD_API_KEY"], stt_enabled(),
                    "No audio read-back check"),
        Integration("cloud_storage", ["GCS_BUCKET", "GOOGLE_CLOUD_PROJECT"], storage_enabled(),
                    "Map renders, CAP XML and advisory audio are not archived"),
        Integration("bigquery", ["GOOGLE_CLOUD_PROJECT", "BIGQUERY_DATASET"], bigquery_enabled(),
                    "Audit/dispatch events kept in the local store only"),
        Integration("firestore", ["FIREBASE_PROJECT_ID (Firestore database created)"], firestore_enabled(),
                    "Local SQLite store"),
        Integration("sms", ["SMS_SANDBOX_KEY", "SMS_SANDBOX_FROM", "SMS_SANDBOX_TO"], sms_enabled(),
                    "Simulated SMS (dispatch log only)"),
        Integration("messaging", ["MESSAGING_SANDBOX_TOKEN", "MESSAGING_SANDBOX_CHAT_ID"], messaging_enabled(),
                    "Simulated messaging (dispatch log only)"),
        Integration("maps", ["NEXT_PUBLIC_MAPS_API_KEY (frontend)"], False,
                    "Leaflet + OpenStreetMap tiles (frontend decides from its own env)"),
    ]
    for it in items:
        it.runtime_error = _runtime_errors.get(it.name)
        it.verified_at = _verified.get(it.name)
    return items


# ---- live probes: one cheap call per configured integration -------------------------------------------------

def _probe_gemini() -> None:
    from app.ai import gemini

    gemini.client().models.get(model=settings.gemini_model)


def _probe_earth_engine() -> None:
    from app.geospatial import earth_engine

    earth_engine.probe()


def _probe_maps() -> None:
    from app import maps

    maps.geocode("Puri, Odisha, India")


def _probe_translation() -> None:
    import httpx

    r = httpx.get("https://translation.googleapis.com/language/translate/v2/languages",
                  params={"key": settings.google_cloud_api_key, "target": "en"}, timeout=15)
    r.raise_for_status()


def _probe_tts() -> None:
    import httpx

    r = httpx.get("https://texttospeech.googleapis.com/v1/voices",
                  params={"key": settings.google_cloud_api_key, "languageCode": "en-IN"}, timeout=15)
    r.raise_for_status()


def _probe_stt() -> None:
    import httpx

    silence = base64.b64encode(b"\x00\x00" * 1600).decode()  # 0.1 s of 16 kHz LINEAR16 silence
    r = httpx.post("https://speech.googleapis.com/v1/speech:recognize", params={"key": settings.google_cloud_api_key},
                   json={"config": {"encoding": "LINEAR16", "sampleRateHertz": 16000, "languageCode": "en-IN"},
                         "audio": {"content": silence}}, timeout=15)
    r.raise_for_status()


def _probe_storage() -> None:
    from app import media

    media.probe()


def _probe_bigquery() -> None:
    from app import store

    store.ensure_bigquery_tables()


def _probe_firestore() -> None:
    from app import store

    store.FirestoreStore(settings.firebase_project_id).probe()


PROBES: dict[str, tuple[Callable[[], bool], Callable[[], None]]] = {
    "gemini": (gemini_enabled, _probe_gemini),
    "earth_engine": (earth_engine_enabled, _probe_earth_engine),
    "maps_routes": (maps_enabled, _probe_maps),
    "translation": (translation_enabled, _probe_translation),
    "text_to_speech": (tts_enabled, _probe_tts),
    "speech_to_text": (stt_enabled, _probe_stt),
    "cloud_storage": (storage_enabled, _probe_storage),
    "bigquery": (bigquery_enabled, _probe_bigquery),
    "firestore": (firestore_enabled, _probe_firestore),
}


def _run_probe(name: str) -> None:
    enabled, fn = PROBES[name]
    if not enabled():
        return
    try:
        fn()
        clear_error(name)
    except Exception as exc:  # noqa: BLE001
        log.warning("integration %s probe failed: %s", name, exc)
        record_error(name, exc)


def probe_all() -> None:
    with _probe_lock, ThreadPoolExecutor(max_workers=len(PROBES)) as pool:
        list(pool.map(_run_probe, PROBES))


def start_probe() -> None:
    """Probe in the background at startup so the first request is not blocked."""
    global _probe_thread
    if settings.force_demo_mode:
        return
    _probe_thread = threading.Thread(target=probe_all, name="integration-probe", daemon=True)
    _probe_thread.start()


def status(probe: bool = False) -> dict:
    if probe and not settings.force_demo_mode:
        probe_all()
    elif _probe_thread is not None and _probe_thread.is_alive():
        _probe_thread.join(timeout=20)
    items = all_integrations()
    backend = [i for i in items if i.name != "maps"]
    return {
        "demo_mode": any(i.mode == "demo" for i in backend) or settings.force_demo_mode,
        "force_demo_mode": settings.force_demo_mode,
        "sample_data": True,
        "integrations": [
            {"name": i.name, "mode": i.mode, "env_vars": i.env_vars, "demo_fallback": i.demo_fallback,
             "runtime_error": i.runtime_error, "verified_at": i.verified_at, **i.extra}
            for i in items
        ],
    }
