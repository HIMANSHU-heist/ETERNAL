"""
Turns a dataset's schema summary, real analysis results, and generated report
into small text chunks suitable for vector indexing.

Design principle carried over from the original architecture idea: we index
METADATA (column descriptions, computed stats, report excerpts) — never raw
data rows. This keeps chunks small, keeps the vector store cheap, and avoids
ever leaking raw row-level data through embeddings.
"""

from typing import List, Optional


def build_chunks(
    schema_summary: dict,
    analysis_results: Optional[list] = None,
    report: Optional[str] = None,
) -> List[str]:
    chunks: List[str] = []

    chunks.append(
        f"Dataset overview: {schema_summary.get('num_rows')} rows, "
        f"{schema_summary.get('num_columns')} columns."
    )

    for col in schema_summary.get("columns", []):
        parts = [
            f"Column '{col.get('name')}' (dtype={col.get('dtype')})",
            f"missing values={col.get('num_missing', 0)}",
            f"unique values={col.get('num_unique', 'n/a')}",
        ]
        if "min" in col and "max" in col:
            parts.append(f"range=[{col.get('min')}, {col.get('max')}], mean={col.get('mean')}")
        if "sample_values" in col:
            parts.append(f"sample values={col.get('sample_values')}")
        chunks.append(". ".join(parts) + ".")

    if analysis_results:
        for item in analysis_results:
            step = item.get("step", {})
            if item.get("status") == "ok":
                chunks.append(
                    f"Analysis step '{step.get('type')}' "
                    f"({step.get('description', '')}): result = {item.get('result')}"
                )
            else:
                chunks.append(
                    f"Analysis step '{step.get('type')}' failed: {item.get('error', 'unknown error')}"
                )

    if report:
        for paragraph in report.split("\n\n"):
            paragraph = paragraph.strip()
            if paragraph:
                chunks.append(f"Report excerpt: {paragraph}")

    return chunks
