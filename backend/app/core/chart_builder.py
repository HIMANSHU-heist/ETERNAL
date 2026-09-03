"""
Computes REAL chart-ready data from the actual dataframe for a given chart
spec. No LLM involvement here — every number comes from pandas, same
"no hallucination" guarantee as the Analyst agent (analyst.py).
"""

import numpy as np
import pandas as pd

MAX_SCATTER_POINTS = 400
MAX_CATEGORIES = 20


def build_chart_data(df: pd.DataFrame, spec: dict) -> dict:
    chart_type = spec.get("chart_type")
    column = spec.get("column")
    column2 = spec.get("column2")

    if chart_type in ("pie", "bar") and column:
        if column not in df.columns:
            raise ValueError(f"Column '{column}' not found")
        counts = df[column].value_counts().head(MAX_CATEGORIES)
        return {
            "chart_type": chart_type,
            "labels": counts.index.astype(str).tolist(),
            "values": [float(v) for v in counts.values],
            "x_label": column,
            "y_label": "count",
        }

    if chart_type == "histogram" and column:
        if column not in df.columns:
            raise ValueError(f"Column '{column}' not found")
        series = pd.to_numeric(df[column], errors="coerce").dropna()
        bins = pd.cut(series, bins=10)
        counts = bins.value_counts().sort_index()
        labels = [f"{interval.left:.1f}-{interval.right:.1f}" for interval in counts.index]
        return {
            "chart_type": "histogram",
            "labels": labels,
            "values": [float(v) for v in counts.values],
            "x_label": column,
            "y_label": "count",
        }

    if chart_type == "line" and column:
        if column not in df.columns:
            raise ValueError(f"Column '{column}' not found")
        series = pd.to_numeric(df[column], errors="coerce").dropna().reset_index(drop=True)
        if len(series) > 300:
            step = max(1, len(series) // 300)
            series = series.iloc[::step]
        return {
            "chart_type": "line",
            "labels": [str(i) for i in range(len(series))],
            "values": [float(v) for v in series.values],
            "x_label": "index",
            "y_label": column,
        }

    if chart_type == "scatter" and column and column2:
        if column not in df.columns or column2 not in df.columns:
            raise ValueError(f"Column '{column}' or '{column2}' not found")
        sample = df[[column, column2]].apply(pd.to_numeric, errors="coerce").dropna()
        if len(sample) > MAX_SCATTER_POINTS:
            sample = sample.sample(MAX_SCATTER_POINTS, random_state=42)
        return {
            "chart_type": "scatter",
            "points": [
                {"x": float(row[column]), "y": float(row[column2])}
                for _, row in sample.iterrows()
            ],
            "x_label": column,
            "y_label": column2,
        }

    if chart_type == "grouped_bar" and column and column2:
        if column not in df.columns or column2 not in df.columns:
            raise ValueError(f"Column '{column}' or '{column2}' not found")

        numeric = pd.to_numeric(df[column2], errors="coerce")
        clean_numeric = numeric.dropna()

        bin_size = spec.get("bin_size")
        if not bin_size:
            # LLM ने bin_size दिली नाही → actual range वरून सुयोग्य bin_size काढा
            # जेणेकरून साधारण 6-8 bins तयार होतील
            data_range = clean_numeric.max() - clean_numeric.min()
            raw_bin = data_range / 7
            magnitude = 10 ** (len(str(int(raw_bin))) - 1)
            bin_size = max(1, round(raw_bin / magnitude) * magnitude)

        min_val = int(np.floor(clean_numeric.min() / bin_size) * bin_size)
        max_val = int(np.ceil(clean_numeric.max() / bin_size) * bin_size)
        edges = list(range(min_val, max_val + bin_size, bin_size))
        labels = [f"{edges[i]}-{edges[i + 1]}" for i in range(len(edges) - 1)]

        binned = pd.cut(numeric, bins=edges, labels=labels, right=False, include_lowest=True)

        cat_series = df[column].dropna()
        top_categories = cat_series.value_counts().head(6).index
        mask = df[column].isin(top_categories)

        cross = pd.crosstab(binned[mask], df.loc[mask, column])

        categories = cross.columns.astype(str).tolist()
        series = {cat: [float(v) for v in cross[cat].tolist()] for cat in cross.columns}

        return {
            "chart_type": "grouped_bar",
            "labels": cross.index.astype(str).tolist(),
            "categories": categories,
            "series": series,
            "x_label": column2,
            "y_label": "count",
            "group_label": column,
        }

    if chart_type == "heatmap":
        numeric_cols = spec.get("columns") or df.select_dtypes(include="number").columns.tolist()
        numeric_cols = [c for c in numeric_cols if c in df.columns][:10]
        if len(numeric_cols) < 2:
            numeric_cols = df.select_dtypes(include="number").columns.tolist()[:10]
        corr = df[numeric_cols].corr(numeric_only=True).round(3)
        return {"chart_type": "heatmap", "matrix": corr.to_dict()}

    raise ValueError(f"Unsupported or incomplete chart spec: {spec}")