"""
In-memory registry that maps file_id -> dataset context.

Stores:
- filepath
- schema_summary
- analysis_results / report / plan (the cached analysis)
- analyzed  -> has /analyze ever been run successfully for this file_id
- dirty     -> has the underlying CSV changed (feature engineering) since
               the last successful /analyze
"""

from typing import Dict, Optional

_registry: Dict[str, dict] = {}


def register_file(file_id: str, filepath: str, schema_summary: dict) -> None:
    _registry[file_id] = {
        "filepath": filepath,
        "schema_summary": schema_summary,
        "analysis_results": [],
        "report": "",
        "plan": [],
        "analyzed": False,
        "dirty": False,
    }


def get_file_context(file_id: str) -> Optional[dict]:
    return _registry.get(file_id)


def save_analysis_result(
    file_id: str,
    analysis_results: list,
    report: str = "",
    plan: Optional[list] = None,
) -> None:
    if file_id in _registry:
        _registry[file_id]["analysis_results"] = analysis_results
        _registry[file_id]["report"] = report
        _registry[file_id]["plan"] = plan or _registry[file_id].get("plan", [])
        _registry[file_id]["analyzed"] = True
        _registry[file_id]["dirty"] = False


def update_dataset_file(file_id: str, filepath: str, schema_summary: dict) -> None:
    """
    Called after feature-engineering steps are applied IN PLACE to a
    dataset's CSV. Keeps the same file_id (so chat history / sidebar /
    previous analysis all still point at the right dataset) but marks it
    dirty so the UI knows the old analysis/report is stale.
    """
    if file_id in _registry:
        _registry[file_id]["filepath"] = filepath
        _registry[file_id]["schema_summary"] = schema_summary
        _registry[file_id]["dirty"] = True


def list_files() -> Dict[str, dict]:
    return _registry