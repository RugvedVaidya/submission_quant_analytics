from fastapi import FastAPI
from state.market_state import MarketState
from analytics.hedge_ratio import compute_hedge_ratio
from analytics.spread import compute_spread
from analytics.zscore import compute_zscore
from analytics.correlation import rolling_correlation
from analytics.adf_test import adf_test
from alerts.rules import zscore_alert

app = FastAPI(title="Quant Analytics Backend")

# Global shared state
market_state = MarketState()


# ---------------------------------------------------
# BASIC DATA
# ---------------------------------------------------
@app.get("/symbols")
def get_symbols():
    return {"symbols": market_state.get_symbols()}


@app.get("/price")
def get_latest_price(symbol: str):
    price = market_state.get_latest_price(symbol)
    return {"symbol": symbol, "price": price}


@app.get("/bars")
def get_bars(symbol: str, timeframe: str = "1m"):
    """
    timeframe: 1s | 1m | 5m
    """
    df = market_state.get_resampled(symbol, timeframe)

    if df is None:
        return {"bars": 0, "data": {}}

    return {
        "bars": len(df),
        "data": df.tail(100).to_dict()
    }


# ---------------------------------------------------
# ANALYTICS
# ---------------------------------------------------
@app.get("/analytics/zscore")
def zscore(symbol_a: str,
           symbol_b: str,
           timeframe: str = "1m",
           window: int = 50):

    s1 = market_state.get_price_series(symbol_a, timeframe)
    s2 = market_state.get_price_series(symbol_b, timeframe)

    hedge = compute_hedge_ratio(s1, s2)
    spread = compute_spread(s1, s2, hedge)
    z = compute_zscore(spread, window)

    return {
        "hedge_ratio": hedge,
        "zscore": z
    }


@app.get("/analytics/correlation")
def correlation(symbol_a: str,
                symbol_b: str,
                timeframe: str = "1m",
                window: int = 50):

    s1 = market_state.get_price_series(symbol_a, timeframe)
    s2 = market_state.get_price_series(symbol_b, timeframe)

    corr = rolling_correlation(s1, s2, window)
    return {"correlation": corr}


@app.get("/analytics/adf")
def adf(symbol_a: str,
        symbol_b: str,
        timeframe: str = "1m"):

    s1 = market_state.get_price_series(symbol_a, timeframe)
    s2 = market_state.get_price_series(symbol_b, timeframe)

    hedge = compute_hedge_ratio(s1, s2)
    spread = compute_spread(s1, s2, hedge)

    adf_stat, p_value = adf_test(spread)

    return {
        "adf_stat": adf_stat,
        "p_value": p_value
    }


# ---------------------------------------------------
# ALERTS
# ---------------------------------------------------
@app.get("/alerts/zscore")
def alert(symbol_a: str,
          symbol_b: str,
          timeframe: str = "1m",
          window: int = 50):

    s1 = market_state.get_price_series(symbol_a, timeframe)
    s2 = market_state.get_price_series(symbol_b, timeframe)

    hedge = compute_hedge_ratio(s1, s2)
    spread = compute_spread(s1, s2, hedge)

    z = compute_zscore(spread, window)
    corr = rolling_correlation(s1, s2, window)
    _, p_value = adf_test(spread)

    triggered = zscore_alert(z, p_value, corr)

    return {
        "triggered": triggered,
        "zscore": z,
        "correlation": corr,
        "p_value": p_value
    }
