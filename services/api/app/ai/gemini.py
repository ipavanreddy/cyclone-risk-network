"""Gemini orchestration: structured context in, schema-validated JSON out, versioned."""
import time
from datetime import UTC, datetime
from functools import lru_cache

from google import genai
from google.genai import errors as genai_errors
from google.genai import types
from pydantic import BaseModel

from app.config import REPO_ROOT, settings

PROMPTS_DIR = REPO_ROOT / "ai" / "prompts"
RETRIES = 3
BACKOFF_S = [2, 5, 10]


class AIProvenance(BaseModel):
    model_name: str
    model_version: str
    prompt_version: str
    generated_at: datetime


@lru_cache
def client() -> genai.Client:
    if settings.google_genai_use_vertexai:
        return genai.Client(
            vertexai=True,
            project=settings.google_cloud_project,
            location=settings.gemini_location,
        )
    return genai.Client(api_key=settings.gemini_api_key)


def load_prompt(name: str, version: str) -> str:
    """Load ai/prompts/{name}_{version}.md."""
    return (PROMPTS_DIR / f"{name}_{version}.md").read_text()


def generate_structured[T: BaseModel](
    prompt: str,
    schema: type[T],
    prompt_version: str,
    parts: list[types.Part] | None = None,
) -> tuple[T, AIProvenance]:
    """Call Gemini with a response schema and return the validated object plus provenance."""
    config = types.GenerateContentConfig(
        response_mime_type="application/json",
        response_schema=schema,
        automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
    )
    for attempt in range(RETRIES + 1):
        try:
            response = client().models.generate_content(
                model=settings.gemini_model, contents=[prompt, *(parts or [])], config=config)
            break
        except genai_errors.APIError as exc:
            # 429 (shared Vertex AI quota) and 5xx are transient: back off and retry before falling back.
            if attempt == RETRIES or not (exc.code == 429 or exc.code >= 500):
                raise
            time.sleep(BACKOFF_S[attempt])
    result = schema.model_validate_json(response.text)
    provenance = AIProvenance(
        model_name=settings.gemini_model,
        model_version=response.model_version or settings.gemini_model,
        prompt_version=prompt_version,
        generated_at=datetime.now(UTC),
    )
    return result, provenance
