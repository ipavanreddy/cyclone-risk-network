"""Which integrations are real vs demo fallback. Single source of truth for the UI "Demo mode" badge."""
from dataclasses import dataclass, field

from app.config import settings


@dataclass
class Integration:
    name: str
    env_vars: list[str]
    configured: bool
    demo_fallback: str
    runtime_error: str | None = None
    extra: dict = field(default_factory=dict)

    @property
    def mode(self) -> str:
        if self.configured and not self.runtime_error:
            return "real"
        return "demo"


_runtime_errors: dict[str, str] = {}


def record_error(name: str, err: Exception | str) -> None:
    """Called by adapters when a configured integration fails and they fall back to demo mode."""
    _runtime_errors[name] = str(err)[:300]


def clear_error(name: str) -> None:
    _runtime_errors.pop(name, None)


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


def firestore_enabled() -> bool:
    return _on(settings.firebase_project_id)


def bigquery_enabled() -> bool:
    return _on(settings.google_cloud_project)


def sms_enabled() -> bool:
    return _on(settings.sms_sandbox_key) and ":" in settings.sms_sandbox_key and bool(settings.sms_sandbox_to)


def messaging_enabled() -> bool:
    return _on(settings.messaging_sandbox_token) and bool(settings.messaging_sandbox_chat_id)


def all_integrations() -> list[Integration]:
    items = [
        Integration("gemini", ["GEMINI_API_KEY", "or GOOGLE_GENAI_USE_VERTEXAI+GOOGLE_CLOUD_PROJECT"], gemini_enabled(),
                    "Deterministic bulletin parser + template situation report/advisories (labelled demo)",
                    extra={"model": settings.gemini_model}),
        Integration("earth_engine", ["EARTH_ENGINE_PROJECT", "GOOGLE_APPLICATION_CREDENTIALS"], earth_engine_enabled(),
                    "Committed synthetic terrain grid + parametric rainfall in data/replays/"),
        Integration("translation_tts", ["GOOGLE_CLOUD_API_KEY"], translation_enabled(),
                    "Pre-approved templates (en/or/bn) + browser speech synthesis preview"),
        Integration("firestore", ["FIREBASE_PROJECT_ID"], firestore_enabled(), "Local SQLite store"),
        Integration("bigquery", ["GOOGLE_CLOUD_PROJECT", "BIGQUERY_DATASET"], bigquery_enabled(),
                    "Audit/dispatch events kept in the local store only"),
        Integration("sms", ["SMS_SANDBOX_KEY", "SMS_SANDBOX_FROM", "SMS_SANDBOX_TO"], sms_enabled(),
                    "Simulated SMS (dispatch log only)"),
        Integration("messaging", ["MESSAGING_SANDBOX_TOKEN", "MESSAGING_SANDBOX_CHAT_ID"], messaging_enabled(),
                    "Simulated messaging (dispatch log only)"),
        Integration("maps", ["NEXT_PUBLIC_MAPS_API_KEY (frontend)"], False,
                    "Leaflet + OpenStreetMap tiles (frontend decides from its own env)"),
    ]
    for it in items:
        it.runtime_error = _runtime_errors.get(it.name)
    return items


def status() -> dict:
    items = all_integrations()
    backend = [i for i in items if i.name != "maps"]
    return {
        "demo_mode": any(i.mode == "demo" for i in backend) or settings.force_demo_mode,
        "force_demo_mode": settings.force_demo_mode,
        "sample_data": True,
        "integrations": [
            {"name": i.name, "mode": i.mode, "env_vars": i.env_vars, "demo_fallback": i.demo_fallback,
             "runtime_error": i.runtime_error, **i.extra}
            for i in items
        ],
    }
