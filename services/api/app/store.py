"""Document store adapter: Firestore when FIREBASE_PROJECT_ID is set (and the database exists), else local
SQLite (demo). Audit/dispatch events are also streamed to BigQuery when GOOGLE_CLOUD_PROJECT is set; the tables
(schemas in infrastructure/bigquery/) are created inside the existing dataset on first use."""
import json
import sqlite3
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from functools import lru_cache
from pathlib import Path
from typing import Protocol

from app import integrations
from app.config import REPO_ROOT, settings


class Store(Protocol):
    kind: str

    def put(self, collection: str, doc_id: str, doc: dict) -> None: ...
    def get(self, collection: str, doc_id: str) -> dict | None: ...
    def list(self, collection: str, **where: str) -> list[dict]: ...


class SQLiteStore:
    kind = "sqlite (local demo)"

    def __init__(self, path: str):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._db = sqlite3.connect(path, check_same_thread=False)
        self._db.execute("CREATE TABLE IF NOT EXISTS docs (collection TEXT, id TEXT, seq INTEGER, body TEXT, "
                         "PRIMARY KEY (collection, id))")

    def put(self, collection: str, doc_id: str, doc: dict) -> None:
        with self._lock:
            cur = self._db.execute("SELECT seq FROM docs WHERE collection=? AND id=?", (collection, doc_id)).fetchone()
            seq = cur[0] if cur else (self._db.execute("SELECT COALESCE(MAX(seq),0)+1 FROM docs").fetchone()[0])
            self._db.execute("INSERT OR REPLACE INTO docs VALUES (?,?,?,?)",
                             (collection, doc_id, seq, json.dumps(doc, default=str)))
            self._db.commit()

    def get(self, collection: str, doc_id: str) -> dict | None:
        with self._lock:
            row = self._db.execute("SELECT body FROM docs WHERE collection=? AND id=?", (collection, doc_id)).fetchone()
        return json.loads(row[0]) if row else None

    def list(self, collection: str, **where: str) -> list[dict]:
        with self._lock:
            rows = self._db.execute("SELECT body FROM docs WHERE collection=? ORDER BY seq", (collection,)).fetchall()
        docs = [json.loads(r[0]) for r in rows]
        return [d for d in docs if all(d.get(k) == v for k, v in where.items() if v is not None)]


class FirestoreStore:
    kind = "firestore"

    def __init__(self, project: str):
        import firebase_admin
        from firebase_admin import firestore

        app = firebase_admin.initialize_app(options={"projectId": project}) if not firebase_admin._apps else None
        self._db = firestore.client(app)

    def probe(self) -> None:
        """Raises if the Firestore database does not exist / is not reachable."""
        self._db.collection("_probe").document("status").get()

    def put(self, collection: str, doc_id: str, doc: dict) -> None:
        body = json.loads(json.dumps(doc, default=str))
        body["_written_at"] = datetime.now(UTC).isoformat()
        self._db.collection(collection).document(doc_id).set(body)

    def get(self, collection: str, doc_id: str) -> dict | None:
        snap = self._db.collection(collection).document(doc_id).get()
        return snap.to_dict() if snap.exists else None

    def list(self, collection: str, **where: str) -> list[dict]:
        q = self._db.collection(collection)
        for k, v in where.items():
            if v is not None:
                q = q.where(k, "==", v)
        docs = [d.to_dict() for d in q.stream()]
        return sorted(docs, key=lambda d: d.get("_written_at", ""))


_store: Store | None = None


def get_store() -> Store:
    global _store
    if _store is None:
        if integrations.firestore_enabled():
            try:
                fs = FirestoreStore(settings.firebase_project_id)
                fs.probe()
                _store = fs
                integrations.clear_error("firestore")
            except Exception as exc:  # noqa: BLE001
                integrations.record_error("firestore", exc)
        if _store is None:
            _store = SQLiteStore(settings.store_path)
    return _store


def reset_store() -> None:
    """Tests: drop the cached store so a new STORE_PATH takes effect."""
    global _store
    _store = None


def audit(event: str, actor: str, role: str, details: dict) -> dict:
    """Append-only audit log (PRD §35): what, when, by whom. Mirrored to BigQuery when configured."""
    now = datetime.now(UTC).isoformat()
    row = {"event": event, "actor": actor, "role": role, "at": now, "details": details}
    get_store().put("audit_log", f"{now}-{event}-{details.get('id', '')}", row)
    bigquery_log("audit_log", {"event": event, "actor": actor, "role": role, "event_time": now,
                               "details": json.dumps(details, default=str)})
    return row


SCHEMA_DIR = REPO_ROOT / "infrastructure" / "bigquery"
BQ_TABLES = ("audit_log", "dispatch_log")
_bq_pool = ThreadPoolExecutor(max_workers=2, thread_name_prefix="bq")


@lru_cache
def _bq_client():
    from google.cloud import bigquery

    return bigquery.Client(project=settings.google_cloud_project)


@lru_cache
def ensure_bigquery_tables() -> bool:
    """Create the event tables inside the existing dataset if missing (never creates the dataset)."""
    from google.cloud import bigquery

    client = _bq_client()
    client.get_dataset(f"{settings.google_cloud_project}.{settings.bigquery_dataset}")
    for table in BQ_TABLES:
        schema = [bigquery.SchemaField(f["name"], f["type"], mode=f.get("mode", "NULLABLE"),
                                       description=f.get("description"))
                  for f in json.loads((SCHEMA_DIR / f"{table}.schema.json").read_text())]
        t = bigquery.Table(f"{settings.google_cloud_project}.{settings.bigquery_dataset}.{table}", schema=schema)
        t.time_partitioning = bigquery.TimePartitioning(field="event_time")
        client.create_table(t, exists_ok=True)
    return True


def _bigquery_insert(table: str, row: dict) -> None:
    try:
        ensure_bigquery_tables()
        errors = _bq_client().insert_rows_json(
            f"{settings.google_cloud_project}.{settings.bigquery_dataset}.{table}", [row])
        if errors:
            raise RuntimeError(errors)
        integrations.clear_error("bigquery")
    except Exception as exc:  # noqa: BLE001
        integrations.record_error("bigquery", exc)


def bigquery_log(table: str, row: dict) -> None:
    """Stream one event row to BigQuery in the background (never blocks or fails the request)."""
    if integrations.bigquery_enabled():
        _bq_pool.submit(_bigquery_insert, table, row)
