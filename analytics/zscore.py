import numpy as np
import pandas as pd


def compute_zscore(spread_series: pd.Series, window: int = 50):
    """
    Computes z-score of the latest spread value.

    Parameters:
    - spread_series: pd.Series (indexed by time)
    - window: rolling window size (number of bars)

    Returns:
    - float or None
    """

    if spread_series is None or len(spread_series) < window:
        return None

    recent = spread_series.iloc[-window:]
    mean = recent.mean()
    std = recent.std()

    if std == 0 or np.isnan(std):
        return 0.0

    z = (recent.iloc[-1] - mean) / std
    return float(z)
