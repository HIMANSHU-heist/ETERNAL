"""
In-memory registry that maps file_id -> dataset context.

Stores:
- filepath
- schema_summary
- analysis_results
- report
"""

from typing import Dict, Optional

_registry: Dict[str, dict] = {}


def register_file(file_id: str, filepath: str, schema_summary: dict) -> None:
    _registry[file_id] = {
        "filepath": filepath,
        "schema_summary": schema_summary,
        "analysis_results": [],
        "report": "",
    }


def get_file_context(file_id: str) -> Optional[dict]:
    return _registry.get(file_id)


def save_analysis_result(
    file_id: str,
    analysis_results: list,
    report: str = "",
) -> None:
    if file_id in _registry:
        _registry[file_id]["analysis_results"] = analysis_results
        _registry[file_id]["report"] = report


def list_files() -> Dict[str, dict]:
    return _registry