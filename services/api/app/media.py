"""Cloud Storage archive (GCS_BUCKET) for map renders sent to Gemini, CAP XML and advisory audio (PRD §28).
Objects live under `cyclone-risk-network/` in the bucket. Demo mode: nothing is archived (returns None)."""
from functools import lru_cache

from app import integrations
from app.config import settings

PREFIX = "cyclone-risk-network"


@lru_cache
def _bucket():
    from google.cloud import storage

    return storage.Client(project=settings.google_cloud_project).bucket(settings.gcs_bucket)


def probe() -> None:
    from google.cloud import storage

    client = storage.Client(project=settings.google_cloud_project)
    list(client.list_blobs(settings.gcs_bucket, prefix=PREFIX, max_results=1))


def exists(path: str) -> bool:
    if not integrations.storage_enabled():
        return False
    try:
        return _bucket().blob(f"{PREFIX}/{path}").exists()
    except Exception as exc:  # noqa: BLE001
        integrations.record_error("cloud_storage", exc)
        return False


def download(path: str) -> bytes | None:
    if not integrations.storage_enabled():
        return None
    try:
        return _bucket().blob(f"{PREFIX}/{path}").download_as_bytes()
    except Exception as exc:  # noqa: BLE001
        integrations.record_error("cloud_storage", exc)
        return None


def upload(path: str, data: bytes | str, content_type: str) -> str | None:
    """Upload and return the gs:// URI, or None in demo mode / on failure (the caller carries on)."""
    if not integrations.storage_enabled():
        return None
    try:
        blob = _bucket().blob(f"{PREFIX}/{path}")
        blob.upload_from_string(data, content_type=content_type)
        integrations.clear_error("cloud_storage")
        return f"gs://{settings.gcs_bucket}/{PREFIX}/{path}"
    except Exception as exc:  # noqa: BLE001
        integrations.record_error("cloud_storage", exc)
        return None
