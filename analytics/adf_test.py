import pandas as pd
from statsmodels.tsa.stattools import adfuller


def adf_test(spread: pd.Series, min_length: int = 30):
    """
    Performs Augmented Dickey-Fuller test on spread series.

    Returns:
    - adf_stat (float or None)
    - p_value (float or None)
    """

    if spread is None:
        return None, None

    spread = spread.dropna()

    if len(spread) < min_length:
        return None, None

    adf_stat, p_value, _, _, _, _ = adfuller(spread)

    return float(adf_stat), float(p_value)
