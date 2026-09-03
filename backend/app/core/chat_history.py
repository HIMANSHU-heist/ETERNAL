"""
Per-file_id chat history, so the LLM remembers earlier turns in the same
"conversation with your data" session.
"""

from typing import Dict, List

_history: Dict[str, List[dict]] = {}

MAX_TURNS_KEPT = 12  # keep last N messages to control token usage


def append(file_id: str, role: str, content: str) -> None:
    _history.setdefault(file_id, []).append({"role": role, "content": content})
    _history[file_id] = _history[file_id][-MAX_TURNS_KEPT:]


def get(file_id: str) -> List[dict]:
    return _history.get(file_id, [])


def clear(file_id: str) -> None:
    _history.pop(file_id, None)
