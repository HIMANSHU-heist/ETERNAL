import pandas as pd


class FeatureStepError(Exception):
    pass


def apply_step(df: pd.DataFrame, step: dict) -> pd.DataFrame:
    t = step.get("type")
    required_keys = {
        "fillna": ["column", "strategy"],
        "drop_column": ["column"],
        "encode_categorical": ["column", "method"],
        "log_transform": ["column"],
        "bin_numeric": ["column", "new_column", "bins"],
        "create_ratio": ["new_column", "numerator", "denominator"],
    }

    for key in required_keys.get(t, []):
        if key not in step:
            raise FeatureStepError(
                f"Missing required key '{key}' for step type '{t}'"
            )

    for key in ("column", "numerator", "denominator"):
        col = step.get(key)
        if col and col not in df.columns:
            raise FeatureStepError(
                f"Column '{col}' not found for step type '{t}'"
            )

    try:
        if t == "fillna":
            col, strat = step["column"], step["strategy"]
            if strat == "mean":
                df[col] = df[col].fillna(df[col].mean())
            elif strat == "median":
                df[col] = df[col].fillna(df[col].median())
            elif strat == "mode":
                df[col] = df[col].fillna(df[col].mode()[0])
            elif strat == "constant":
                df[col] = df[col].fillna(step.get("value"))
        elif t == "drop_column":
            df = df.drop(columns=[step["column"]])
        elif t == "encode_categorical":
            col, method = step["column"], step["method"]
            if method == "onehot":
                df = pd.get_dummies(df, columns=[col])
            elif method == "label":
                df[col] = df[col].astype("category").cat.codes
            else:
                raise FeatureStepError(f"Unknown encoding method: '{method}'")
        elif t == "create_ratio":
            df[step["new_column"]] = df[step["numerator"]] / df[
                step["denominator"]
            ].replace(0, pd.NA)
        elif t == "bin_numeric":
            df[step["new_column"]] = pd.cut(df[step["column"]], bins=step["bins"])
        elif t == "log_transform":
            import numpy as np

            col = step["column"]
            df[col] = np.log1p(df[col].clip(lower=0))
        else:
            raise FeatureStepError(f"Unknown step type: '{t}'")
    except FeatureStepError:
        raise
    except Exception as e:
        raise FeatureStepError(f"Failed to apply step '{t}': {e}") from e

    return df


def apply_plan(df: pd.DataFrame, steps: list[dict]) -> pd.DataFrame:
    df = df.copy()
    for step in steps:
        df = apply_step(df, step)
    return df
