import time
import requests
import pandas as pd
import numpy as np
import streamlit as st
import plotly.graph_objects as go

# =================================================
# Page Config
# =================================================
st.set_page_config(page_title="Pair Trading Dashboard", layout="wide")
st.title("📊 Real-Time Pair Trading Analytics")

import os
BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")

# =================================================
# Session State (Trade Log)
# =================================================
if "trade_log" not in st.session_state:
    st.session_state.trade_log = []

# =================================================
# Helper Functions
# =================================================
def api_get(path, params=None):
    r = requests.get(f"{BACKEND_URL}{path}", params=params, timeout=5)
    r.raise_for_status()
    return r.json()

def compute_signal_score(z, corr, p_value, z_thresh):
    if z is None or corr is None or p_value is None:
        return None

    z_comp = min(abs(z) / z_thresh, 1.0)
    corr_comp = min(corr / 0.8, 1.0)
    adf_comp = min((0.05 - p_value) / 0.05, 1.0) if p_value < 0.05 else 0.0

    score = 100 * (0.5 * z_comp + 0.3 * corr_comp + 0.2 * adf_comp)
    return round(score, 1)

def compute_half_life(spread: pd.Series):
    if spread is None or len(spread) < 10:
        return None

    spread_lag = spread.shift(1).dropna()
    delta = spread.diff().dropna()

    beta = np.polyfit(spread_lag, delta, 1)[0]
    if beta >= 0:
        return None

    half_life = -np.log(2) / beta
    return round(half_life, 2)

# =================================================
# Sidebar Controls
# =================================================
st.sidebar.markdown("## ⚙️ Strategy Controls")

symbol_a = st.sidebar.selectbox("Symbol A", ["btcusdt"])
symbol_b = st.sidebar.selectbox("Symbol B", ["ethusdt"])

timeframe = st.sidebar.selectbox(
    "Timeframe",
    ["1m", "5m"],
    index=0
)

window = st.sidebar.slider("Rolling Window (bars)", 5, 100, 5)
z_thresh = st.sidebar.slider("Z-Score Threshold", 1.0, 3.0, 2.0)
refresh = st.sidebar.slider("Refresh (seconds)", 2, 30, 5)

# =================================================
# Streamlit-safe Refresh
# =================================================
if "last_refresh" not in st.session_state:
    st.session_state.last_refresh = time.time()

if time.time() - st.session_state.last_refresh > refresh:
    st.session_state.last_refresh = time.time()
    st.rerun()

# =================================================
# Fetch Backend Data
# =================================================
try:
    bars_a = api_get("/bars", {"symbol": symbol_a, "timeframe": timeframe})
    bars_b = api_get("/bars", {"symbol": symbol_b, "timeframe": timeframe})
    zdata = api_get("/analytics/zscore", {
        "symbol_a": symbol_a,
        "symbol_b": symbol_b,
        "timeframe": timeframe,
        "window": window
    })
    cdata = api_get("/analytics/correlation", {
        "symbol_a": symbol_a,
        "symbol_b": symbol_b,
        "timeframe": timeframe,
        "window": window
    })
    adfdata = api_get("/analytics/adf", {
        "symbol_a": symbol_a,
        "symbol_b": symbol_b,
        "timeframe": timeframe
    })
    alert = api_get("/alerts/zscore", {
        "symbol_a": symbol_a,
        "symbol_b": symbol_b,
        "timeframe": timeframe,
        "window": window
    })
except Exception as e:
    st.error(f"Backend not reachable: {e}")
    st.stop()

# =================================================
# DataFrames
# =================================================
df_a = pd.DataFrame(bars_a["data"])
df_b = pd.DataFrame(bars_b["data"])

if df_a.empty or df_b.empty:
    st.warning("Waiting for data...")
    st.stop()

df_a.index = pd.to_datetime(df_a.index)
df_b.index = pd.to_datetime(df_b.index)
df = df_a.join(df_b, lsuffix="_a", rsuffix="_b", how="inner")

# =================================================
# System Status
# =================================================
st.markdown("### 🟢 System Status")
if len(df) < window:
    st.info(f"⏳ Warming up: {len(df)}/{window} bars collected")
else:
    st.success("✅ Analytics fully active")

# =================================================
# Metrics
# =================================================
hedge = zdata.get("hedge_ratio")

signal_score = compute_signal_score(
    zdata.get("zscore"),
    cdata.get("correlation"),
    adfdata.get("p_value"),
    z_thresh
)

spread_series = None
half_life = None
if hedge is not None:
    spread_series = df["close_a"] - hedge * df["close_b"]
    half_life = compute_half_life(spread_series)

st.markdown("## 📌 Key Statistics")
c1, c2, c3, c4, c5, c6 = st.columns(6)

c1.metric("Hedge Ratio (β)", f"{hedge:.4f}" if hedge else "N/A")
c2.metric("Z-Score", f"{zdata['zscore']:.2f}" if zdata["zscore"] else "N/A")
c3.metric("Correlation", f"{cdata['correlation']:.2f}" if cdata["correlation"] else "N/A")
c4.metric("ADF p-value", f"{adfdata['p_value']:.4f}" if adfdata["p_value"] else "N/A")
c5.metric("Signal Quality", f"{signal_score}/100" if signal_score else "N/A")
c6.metric("Half-Life (bars)", f"{half_life}" if half_life else "N/A")

# =================================================
# Alert + Trade Log Append
# =================================================
if alert["triggered"] and signal_score is not None:
    direction = "BUY Spread" if zdata["zscore"] < 0 else "SELL Spread"

    last_signal = (
        st.session_state.trade_log[-1]["Signal"]
        if st.session_state.trade_log else None
    )

    if last_signal != direction:
        st.session_state.trade_log.append({
            "Time": pd.Timestamp.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
            "Pair": f"{symbol_a.upper()} / {symbol_b.upper()}",
            "Signal": direction,
            "Z-Score": round(zdata["zscore"], 2),
            "Hedge Ratio": round(hedge, 4),
            "Signal Score": signal_score,
            "Half-Life": half_life,
            "Timeframe": timeframe
        })

    st.error(
        f"🚨 **PAIR TRADING SIGNAL**\n\n"
        f"Direction: **{direction}**  \n"
        f"Z-Score: {zdata['zscore']:.2f}  \n"
        f"Signal Quality: **{signal_score}/100**"
    )

# =================================================
# Price Chart
# =================================================
st.markdown("## 📈 Market Prices")
price_fig = go.Figure()
price_fig.add_trace(go.Scatter(x=df.index, y=df["close_a"], name=symbol_a.upper()))
price_fig.add_trace(go.Scatter(x=df.index, y=df["close_b"], name=symbol_b.upper()))
price_fig.update_layout(title="Prices")
st.plotly_chart(price_fig, use_container_width=True)

# =================================================
# Spread Chart
# =================================================
st.markdown("## 🔄 Spread Analysis")
spread_fig = go.Figure()

if spread_series is not None and len(df) >= window:
    mean = spread_series.rolling(window).mean()
    std = spread_series.rolling(window).std()

    spread_fig.add_trace(go.Scatter(x=df.index, y=spread_series, name="Spread"))
    spread_fig.add_trace(go.Scatter(x=df.index, y=mean, name="Mean", line=dict(dash="dash")))
    spread_fig.add_trace(go.Scatter(x=df.index, y=mean + std, name="+1σ", line=dict(dash="dot")))
    spread_fig.add_trace(go.Scatter(x=df.index, y=mean - std, name="-1σ", line=dict(dash="dot")))

spread_fig.update_layout(title="Spread with Mean Reversion Bands")
st.plotly_chart(spread_fig, use_container_width=True)

# =================================================
# Z-Score Chart
# =================================================
st.markdown("## 📊 Z-Score & Signals")
z_fig = go.Figure()

if spread_series is not None and len(df) >= window:
    z_series = (spread_series - spread_series.rolling(window).mean()) / spread_series.rolling(window).std()

    z_fig.add_trace(go.Scatter(x=df.index, y=z_series, name="Z-Score"))
    z_fig.add_hline(y=z_thresh, line_dash="dash")
    z_fig.add_hline(y=-z_thresh, line_dash="dash")
    z_fig.add_hline(y=0, line_dash="dot")

z_fig.update_layout(title="Z-Score with Entry Signals")
st.plotly_chart(z_fig, use_container_width=True)

# =================================================
# Footer
# =================================================
st.markdown("---")
st.caption("Quant-grade pair trading dashboard • Backend-driven analytics")
