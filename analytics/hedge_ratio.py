import pandas as pd
import statsmodels.api as sm


def compute_hedge_ratio(series_a: pd.Series,
                        series_b: pd.Series):
    """
    Computes hedge ratio using OLS regression:
    series_a = alpha + beta * series_b + epsilon

    Returns:
    - beta (hedge ratio) or None
    """

    if series_a is None or series_b is None:
        return None

    # Align time series
    df = pd.concat([series_a, series_b], axis=1, join="inner")
    df.columns = ["a", "b"]

    if len(df) < 5:
        return None

    X = sm.add_constant(df["b"])
    y = df["a"]

    model = sm.OLS(y, X).fit()

    return float(model.params["b"])
