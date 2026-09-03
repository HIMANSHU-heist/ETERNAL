"""
Universal file loader.
Handles CSV, Excel (.xlsx/.xls), JSON, Parquet, TSV.
Always returns a pandas DataFrame so the rest of the app doesn't
need to care what format the user uploaded.
"""

import pandas as pd
from pathlib import Path


SUPPORTED_EXTENSIONS = {".csv", ".xlsx", ".xls", ".json", ".parquet", ".tsv"}


class UnsupportedFileTypeError(Exception):
    pass


def load_dataframe(file_path: str) -> pd.DataFrame:
    """Load any supported file into a pandas DataFrame."""
    path = Path(file_path)
    ext = path.suffix.lower()

    if ext not in SUPPORTED_EXTENSIONS:
        raise UnsupportedFileTypeError(
            f"'{ext}' is not supported. Supported types: {sorted(SUPPORTED_EXTENSIONS)}"
        )

    if ext == ".csv":
        return pd.read_csv(path)
    elif ext == ".tsv":
        return pd.read_csv(path, sep="\t")
    elif ext in (".xlsx", ".xls"):
        return pd.read_excel(path)
    elif ext == ".json":
        return pd.read_json(path)
    elif ext == ".parquet":
        return pd.read_parquet(path)

    # Should never reach here
    raise UnsupportedFileTypeError(f"No loader implemented for {ext}")


def get_schema_summary(df: pd.DataFrame) -> dict:
    """
    Produce a compact summary of the dataset's structure.
    This is what gets sent to the LLM later — NOT the raw data
    (keeps token usage low and avoids sending full datasets to an API).
    """
    summary = {
        "num_rows": int(df.shape[0]),
        "num_columns": int(df.shape[1]),
        "columns": [],
    }

    for col in df.columns:
        col_data = df[col]
        col_info = {
            "name": col,
            "dtype": str(col_data.dtype),
            "num_missing": int(col_data.isna().sum()),
            "num_unique": int(col_data.nunique()),
        }

        if pd.api.types.is_numeric_dtype(col_data):
            col_info["min"] = float(col_data.min()) if not col_data.empty else None
            col_info["max"] = float(col_data.max()) if not col_data.empty else None
            col_info["mean"] = float(col_data.mean()) if not col_data.empty else None
        else:
            # Show a few sample values for categorical/text columns
            samples = col_data.dropna().unique()[:5].tolist()
            col_info["sample_values"] = [str(s) for s in samples]

        summary["columns"].append(col_info)

    return summary
