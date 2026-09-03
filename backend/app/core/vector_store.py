"""
Per-dataset vector store using ChromaDB (local, persistent, no external API).

Why Chroma's default embedding function: it bundles a lightweight local
MiniLM-based ONNX model, so we don't need a separate embedding API key or
a heavy sentence-transformers+torch install. Good enough for schema/stats/
report-sized text chunks (this is metadata-level RAG, not row-level RAG —
we never embed raw data rows, only descriptions of them, matching the
original "don't send full rows to the LLM" design goal).

One Chroma collection per dataset_id, so datasets never leak context into
each other's chat sessions.
"""

from pathlib import Path
from typing import List

import chromadb

CHROMA_DIR = Path(__file__).resolve().parent.parent.parent / "vector_store"
CHROMA_DIR.mkdir(exist_ok=True)

_client = chromadb.PersistentClient(path=str(CHROMA_DIR))


def _collection_name(dataset_id: str) -> str:
    # Chroma collection names can't contain hyphens reliably across versions
    return f"dataset_{dataset_id.replace('-', '_')}"


def is_indexed(dataset_id: str) -> bool:
    try:
        _client.get_collection(_collection_name(dataset_id))
        return True
    except Exception:
        return False


def index_dataset(dataset_id: str, chunks: List[str]) -> None:
    """(Re)index a dataset's text chunks. Safe to call again after /analyze
    reruns — old collection is wiped and rebuilt so stale chunks don't linger."""
    name = _collection_name(dataset_id)
    try:
        _client.delete_collection(name)
    except Exception:
        pass

    if not chunks:
        return

    collection = _client.create_collection(name)
    ids = [f"{dataset_id}_{i}" for i in range(len(chunks))]
    collection.add(documents=chunks, ids=ids)


def query_dataset(dataset_id: str, query: str, top_k: int = 6) -> List[str]:
    try:
        collection = _client.get_collection(_collection_name(dataset_id))
    except Exception:
        return []

    result = collection.query(query_texts=[query], n_results=top_k)
    documents = result.get("documents", [[]])
    return documents[0] if documents else []
