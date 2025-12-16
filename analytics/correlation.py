import pandas as pd


def rolling_correlation(series_a: pd.Series,
                        series_b: pd.Series,
                        window: int = 50):
    """
    Computes latest rolling correlation between two price series.
    """

    if series_a is None or series_b is None:
        return None

    # Align time indices
    df = pd.concat([series_a, series_b], axis=1, join="inner")
    df.columns = ["a", "b"]

    if len(df) < window:
        return None

    corr = df["a"].rolling(window).corr(df["b"]).iloc[-1]

    if pd.isna(corr):
        return None

    return float(corr)
