"""
Lightweight JSON-file-backed index of uploaded datasets.
This keeps the sidebar dataset list stable across restarts without duplicating
live in-memory context from app/core/registry.py.
"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock

DEFAULT_PATH = Path(__file__).resolve().parent.parent.parent / "app_data" / "dataset_index.json"
REGISTRY_PATH = Path(os.getenv("DATASET_REGISTRY_PATH", str(DEFAULT_PATH)))
_lock = Lock()


def _ensure_parent() -> None:
    REGISTRY_PATH.parent.mkdir(parents=True, exist_ok=True)


def _load() -> dict:
    _ensure_parent()
    if not REGISTRY_PATH.exists():
        return {}

    try:
        raw = REGISTRY_PATH.read_text(encoding="utf-8")
        data = json.loads(raw)
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def _save(data: dict) -> None:
    _ensure_parent()
    REGISTRY_PATH.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")


def register_dataset(file_id: str, filename: str, num_rows: int | None = None, num_columns: int | None = None) -> dict:
    with _lock:
        registry = _load()
        now = datetime.now(timezone.utc).isoformat()
        entry = {
            "file_id": file_id,
            "filename": filename,
            "num_rows": num_rows,
            "num_columns": num_columns,
            "created_at": registry.get(file_id, {}).get("created_at", now),
            "updated_at": now,
        }
        registry[file_id] = entry
        _save(registry)
        return entry


def list_datasets() -> list[dict]:
    with _lock:
        registry = _load()
        items = list(registry.values())
        return sorted(items, key=lambda item: item.get("updated_at", ""), reverse=True)


def get_dataset_meta(file_id: str) -> dict | None:
    with _lock:
        registry = _load()
        return registry.get(file_id)


def remove_dataset(file_id: str) -> None:
    with _lock:
        registry = _load()
        registry.pop(file_id, None)
        _save(registry)
