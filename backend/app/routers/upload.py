import uuid
from pathlib import Path

from fastapi import APIRouter, UploadFile, File, HTTPException

from app.core.dataset_registry_store import register_dataset
from app.core.doc_converter import (
    convert_to_csv,
    ConversionError,
    CONVERTIBLE_EXTENSIONS,
)
from app.core.file_loader import (
    load_dataframe,
    get_schema_summary,
    UnsupportedFileTypeError,
)
from app.core.registry import register_file

router = APIRouter()

UPLOAD_DIR = Path(__file__).resolve().parent.parent.parent / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

DATASET_REGISTRY: dict[str, str] = {}

# Backend application limit
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB

ALLOWED_EXTENSIONS = {
    ".csv",
    ".xlsx",
    ".xls",
    ".json",
    ".parquet",
    ".tsv",
} | CONVERTIBLE_EXTENSIONS


@router.post("/upload")
async def upload_dataset(file: UploadFile = File(...)):
    """
    Upload a dataset and return its dataset_id + schema summary.
    """

    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="No filename provided.",
        )

    ext = Path(file.filename).suffix.lower()

    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Unsupported file type '{ext}'. "
                "Allowed: CSV, XLSX, XLS, JSON, Parquet, TSV, PDF, DOCX, TXT."
            ),
        )

    # Read uploaded file
    content = await file.read()

    # Validate size
    if len(content) > MAX_FILE_SIZE:
        size_mb = len(content) / (1024 * 1024)
        raise HTTPException(
            status_code=413,
            detail=(
                f"File is too large ({size_mb:.1f} MB). "
                f"Maximum allowed size is 50 MB."
            ),
        )

    if len(content) == 0:
        raise HTTPException(
            status_code=422,
            detail="The uploaded file is empty.",
        )

    dataset_id = str(uuid.uuid4())
    saved_path = UPLOAD_DIR / f"{dataset_id}{ext}"

    # Save file
    try:
        with open(saved_path, "wb") as f:
            f.write(content)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Could not save uploaded file: {e}",
        )

    if ext in CONVERTIBLE_EXTENSIONS:
        original_path = saved_path
        try:
            saved_path = convert_to_csv(str(original_path), UPLOAD_DIR)
            ext = ".csv"
            original_path.unlink(missing_ok=True)
        except ConversionError as e:
            original_path.unlink(missing_ok=True)
            saved_path.unlink(missing_ok=True)
            raise HTTPException(status_code=422, detail=str(e))

    # Parse dataset
    try:
        df = load_dataframe(str(saved_path))

        if df.empty:
            raise HTTPException(
                status_code=422,
                detail="The uploaded dataset contains no rows.",
            )

        if len(df.columns) == 0:
            raise HTTPException(
                status_code=422,
                detail="The uploaded dataset contains no columns.",
            )

    except HTTPException:
        saved_path.unlink(missing_ok=True)
        raise

    except UnsupportedFileTypeError as e:
        saved_path.unlink(missing_ok=True)
        raise HTTPException(
            status_code=400,
            detail=str(e),
        )

    except Exception as e:
        saved_path.unlink(missing_ok=True)

        error_message = str(e)

        if "No columns to parse" in error_message:
            detail = (
                "Could not parse the CSV. "
                "The file appears to be empty or has no readable columns."
            )
        else:
            detail = f"Could not parse file: {error_message}"

        raise HTTPException(
            status_code=422,
            detail=detail,
        )

    # Register dataset
    DATASET_REGISTRY[dataset_id] = str(saved_path)

    schema = get_schema_summary(df)

    register_file(
        dataset_id,
        filepath=str(saved_path),
        schema_summary=schema,
    )

    register_dataset(
        file_id=dataset_id,
        filename=file.filename,
        num_rows=schema.get("num_rows") if isinstance(schema, dict) else getattr(schema, "num_rows", None),
        num_columns=schema.get("num_columns") if isinstance(schema, dict) else getattr(schema, "num_columns", None),
    )

    return {
        "dataset_id": dataset_id,
        "filename": file.filename,
        "schema": schema,
    }


@router.get("/datasets")
def get_all_datasets():
    """Returns metadata for every uploaded dataset — powers the sidebar list."""
    from app.core.dataset_registry_store import list_datasets

    return {"datasets": list_datasets()}


@router.get("/dataset/{dataset_id}/preview")
async def preview_dataset(dataset_id: str, rows: int = 10):
    """Return the first N rows of an uploaded dataset."""

    if dataset_id not in DATASET_REGISTRY:
        raise HTTPException(
            status_code=404,
            detail="Dataset not found",
        )

    if rows < 1 or rows > 100:
        raise HTTPException(
            status_code=400,
            detail="rows must be between 1 and 100",
        )

    df = load_dataframe(DATASET_REGISTRY[dataset_id])

    preview = df.head(rows).fillna("null").to_dict(orient="records")

    return {
        "dataset_id": dataset_id,
        "rows_returned": len(preview),
        "data": preview,
    }
