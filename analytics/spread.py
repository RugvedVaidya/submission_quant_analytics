import pandas as pd


def compute_spread(series_a: pd.Series,
                   series_b: pd.Series,
                   hedge_ratio: float):
    """
    Computes spread = series_a - hedge_ratio * series_b
    Series are time-aligned before computation.
    """

    if hedge_ratio is None:
        return None

    if series_a is None or series_b is None:
        return None

    # Align on timestamp
    df = pd.concat([series_a, series_b], axis=1, join="inner")
    df.columns = ["a", "b"]

    if df.empty:
        return None

    spread = df["a"] - hedge_ratio * df["b"]
    spread.dropna(inplace=True)

    return spread
