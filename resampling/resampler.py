class Resampler:
    """
    Thin wrapper around MarketState resampling.
    Exists only for semantic clarity.
    """

    def __init__(self, market_state):
        self.market_state = market_state

    def resample(self, symbol, timeframe):
        """
        timeframe: '1s', '1m', '5m'
        """
        return self.market_state.get_resampled(symbol, timeframe)
