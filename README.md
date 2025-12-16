## How to Run

1. Install dependencies:
   pip install -r requirements.txt

2. Start backend and live ingestion:
   python app.py

3. Start dashboard:
   streamlit run ui/dashboard.py

The backend runs FastAPI for analytics and alerting while ingesting real-time data from Binance WebSocket. The Streamlit dashboard consumes backend APIs for visualization.

## Project Structure 

quant_analytics/
│
├── ingestion/
│   └── websocket_client.py     # Binance WebSocket client
│
├── state/
│   └── market_state.py         
│
├── analytics/
│   ├── hedge_ratio.py          
│   ├── spread.py              
│   ├── zscore.py               
│   ├── correlation.py        
│   └── adf_test.py        
│
├── alerts/
│   └── rules.py         
│
├── backend/
│   └── api.py               
│
├── ui/
│   └── dashboard.py            
│
├── app.py                      
├── requirements.txt
└── README.md


## Project Explanation

1. Data Ingestion
    Live tick data is streamed from Binance Futures WebSocket
    Data is normalized into {timestamp, symbol, price, quantity}
    Stored in:
        1. SQLite (persistent)
        2. In-memory rolling buffers (fast analytics)

2. Resampling
    Tick data is resampled into configurable intervals:
    1s, 1m, 5m
    OHLC bars are generated backend-side

3. Analytics Engine (Backend)
    All analytics are computed in Python backend:

    Metric	Description
    Hedge Ratio - OLS regression for pair hedging
    Spread - Price difference adjusted by hedge ratio
    Z-Score	- Standardized deviation of spread
    Correlation - Rolling correlation between assets
    ADF Test - Stationarity check for mean reversion
    Signal Quality Score - Composite confidence metric (0–100)
    Half-Life - Speed of mean reversion (bars)

    Analytics only activate after sufficient data is collected, ensuring statistical validity.

4. Alerting Logic
    Alerts are triggered only when:
    Spread is stationary (ADF p-value < 0.05)
    Z-score exceeds threshold
    Correlation is sufficiently high
    This prevents false or unstable signals.

5. Dashboard (Frontend)
    The Streamlit dashboard provides:
    Live prices for both assets
    Spread with mean-reversion bands
    Z-score with entry thresholds
    Key metrics (hedge ratio, confidence score, half-life)
    System warm-up status
    The frontend does not perform analytics — it only consumes backend APIs.

6. Key Design Choices
    Backend-first analytics for correctness
    In-memory + persistent storage for performance & durability
    Warm-up gating to avoid unstable statistics