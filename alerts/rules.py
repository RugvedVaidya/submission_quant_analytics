def zscore_alert(z: float,
                 p_value: float,
                 corr: float,
                 z_thresh: float = 2.0,
                 corr_thresh: float = 0.5,
                 p_thresh: float = 0.05):
    """
    Determines whether a statistical arbitrage alert should trigger.

    Conditions:
    - Spread is stationary (ADF p-value < p_thresh)
    - Absolute z-score exceeds z_thresh
    - Rolling correlation exceeds corr_thresh

    Returns:
    - True if alert conditions satisfied
    - False otherwise
    """

    if z is None or p_value is None or corr is None:
        return False

    if p_value >= p_thresh:
        return False

    if abs(z) < z_thresh:
        return False

    if corr < corr_thresh:
        return False

    return True
