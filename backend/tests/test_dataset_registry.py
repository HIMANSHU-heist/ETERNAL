import pytest

from app.core.dataset_registry_store import register_dataset, list_datasets


def test_register_dataset_persists_metadata(tmp_path, monkeypatch):
    store_path = tmp_path / "datasets.json"
    monkeypatch.setenv("DATASET_REGISTRY_PATH", str(store_path))

    import importlib
    import app.core.dataset_registry_store as registry_store

    importlib.reload(registry_store)

    registry_store.register_dataset("file-123", "demo.csv", 200, 5)
    datasets = registry_store.list_datasets()

    assert datasets[0]["file_id"] == "file-123"
    assert datasets[0]["filename"] == "demo.csv"
    assert datasets[0]["num_rows"] == 200
    assert datasets[0]["num_columns"] == 5

    reloaded = importlib.reload(registry_store)
    assert reloaded.list_datasets()[0]["file_id"] == "file-123"


def test_apply_plan_transforms_dataframe():
    from app.core.feature_engineering import apply_plan
    import pandas as pd

    df = pd.DataFrame({"value": [1.0, None, 3.0], "category": ["a", "b", "a"]})

    transformed = apply_plan(
        df,
        [
            {"type": "fillna", "column": "value", "strategy": "mean"},
            {"type": "encode_categorical", "column": "category", "method": "onehot"},
        ],
    )

    assert transformed["value"].notna().all()
    assert "category_a" in transformed.columns
    assert "category_b" in transformed.columns


def test_upload_module_supports_convertible_extensions():
    from app.core.doc_converter import CONVERTIBLE_EXTENSIONS
    from app.routers import upload

    assert ".pdf" in CONVERTIBLE_EXTENSIONS
    assert ".txt" in CONVERTIBLE_EXTENSIONS
    assert ".csv" in upload.ALLOWED_EXTENSIONS


def test_invalid_encode_method_raises_feature_step_error():
    from app.core.feature_engineering import apply_step, FeatureStepError
    import pandas as pd

    df = pd.DataFrame({"color": ["red", "blue"]})

    try:
        apply_step(df, {"type": "encode_categorical", "column": "color", "method": "one_hot"})
        assert False, "Expected FeatureStepError for invalid encoding method"
    except FeatureStepError as exc:
        assert "Unknown encoding method" in str(exc)


def test_pdf_converter_handles_multiple_tables_and_raises_conversion_error(monkeypatch, tmp_path):
    import types

    import pandas as pd

    from app.core.doc_converter import convert_to_csv, ConversionError

    class FakePage:
        def __init__(self, tables):
            self._tables = tables

        def extract_tables(self):
            return self._tables

    class FakePdf:
        def __init__(self, tables):
            self.pages = [FakePage(tables)]

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    class FakePdfPlumber:
        @staticmethod
        def open(path):
            return FakePdf([
                [["A", "B"], [1, 2], [3, 4]],
                [["A", "B"], [5, 6]],
            ])

    monkeypatch.setitem(
        __import__("sys").modules,
        "pdfplumber",
        types.SimpleNamespace(open=FakePdfPlumber.open),
    )

    df = convert_to_csv("/tmp/example.pdf", tmp_path)
    loaded = pd.read_csv(df)
    assert list(loaded.columns) == ["A", "B"]
    assert loaded.to_dict(orient="records") == [
        {"A": 1, "B": 2},
        {"A": 3, "B": 4},
        {"A": 5, "B": 6},
    ]

    def fake_fail(_path):
        raise ValueError("bad pdf")

    monkeypatch.setattr("app.core.doc_converter._pdf_to_df", fake_fail)
    with pytest.raises(ConversionError):
        convert_to_csv("/tmp/example.pdf", tmp_path)


def test_pdf_converter_rejects_incompatible_table_columns(monkeypatch, tmp_path):
    import types

    from app.core.doc_converter import convert_to_csv, ConversionError

    class FakePage:
        def __init__(self, tables):
            self._tables = tables

        def extract_tables(self):
            return self._tables

    class FakePdf:
        def __init__(self, tables):
            self.pages = [FakePage(tables)]

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    class FakePdfPlumber:
        @staticmethod
        def open(path):
            return FakePdf([
                [["Name", "Age"], ["Alice", 30]],
                [["Product", "Price"], ["Widget", 9.99]],
            ])

    monkeypatch.setitem(
        __import__("sys").modules,
        "pdfplumber",
        types.SimpleNamespace(open=FakePdfPlumber.open),
    )

    with pytest.raises(ConversionError, match="different columns|incompatible"):
        convert_to_csv("/tmp/example.pdf", tmp_path)
