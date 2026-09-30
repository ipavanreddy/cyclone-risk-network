"""Gemini-or-demo orchestration. Real Gemini when configured; otherwise a deterministic, labelled fallback."""
from collections.abc import Callable
from datetime import UTC, datetime

from google.genai import types
from pydantic import BaseModel

from app import integrations
from app.ai import gemini
from app.ai.gemini import AIProvenance

DEMO_MODEL_NAME = "demo-deterministic (Gemini not configured)"
DEMO_MODEL_VERSION = "tatraksha-demo-v1"


def demo_provenance(prompt_version: str) -> AIProvenance:
    return AIProvenance(model_name=DEMO_MODEL_NAME, model_version=DEMO_MODEL_VERSION,
                        prompt_version=prompt_version, generated_at=datetime.now(UTC))


def run[T: BaseModel](
    prompt_name: str,
    version: str,
    context: str,
    schema: type[T],
    fallback: Callable[[], T],
    parts: list[types.Part] | None = None,
) -> tuple[T, AIProvenance, str]:
    """Returns (result, provenance, mode) where mode is "gemini" or "demo"."""
    prompt_version = f"{prompt_name}_{version}"
    if integrations.gemini_enabled():
        try:
            prompt = gemini.load_prompt(prompt_name, version) + "\n\n" + context
            result, prov = gemini.generate_structured(prompt, schema, prompt_version, parts)
            integrations.clear_error("gemini")
            return result, prov, "gemini"
        except Exception as exc:  # noqa: BLE001 - any failure falls back to the labelled demo path
            integrations.record_error("gemini", exc)
    return fallback(), demo_provenance(prompt_version), "demo"
