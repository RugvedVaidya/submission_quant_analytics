from collections import deque, defaultdict
import threading
import sqlite3
import pandas as pd
from datetime import datetime


class MarketState:
    """
    Central in-memory + persistent market state.
    Owns:
    - Raw tick storage
    - SQLite persistence
    - Resampled data cache
    """

    def __init__(self, max_ticks=10_000, db_path="ticks.db"):
        self.max_ticks = max_ticks
        self.data = defaultdict(lambda: deque(maxlen=self.max_ticks))
        self.lock = threading.Lock()

        # --- SQLite persistence ---
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self._init_db()

        # --- Resampled cache ---
        self.resampled = {
            "1s": {},
            "1m": {},
            "5m": {}
        }

    # -----------------------------
    # DB SETUP
    # -----------------------------
    def _init_db(self):
        with self.conn:
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS ticks (
                    ts TEXT,
                    symbol TEXT,
                    price REAL,
                    qty REAL
                )
            """)

    # -----------------------------
    # INGESTION
    # -----------------------------
    def add_tick(self, tick):
        """
        tick = {
            "ts": ISO8601 string,
            "symbol": str,
            "price": float,
            "qty": float
        }
        """
        symbol = tick["symbol"]

        with self.lock:
            self.data[symbol].append(tick)

            # Persist tick
            self.conn.execute(
                "INSERT INTO ticks VALUES (?, ?, ?, ?)",
                (tick["ts"], symbol, tick["price"], tick["qty"])
            )
            self.conn.commit()

    # -----------------------------
    # RAW ACCESS
    # -----------------------------
    def get_ticks(self, symbol):
        with self.lock:
            return list(self.data.get(symbol, []))

    def get_latest_tick(self, symbol):
        with self.lock:
            if symbol in self.data and self.data[symbol]:
                return self.data[symbol][-1]
            return None

    def get_symbols(self):
        with self.lock:
            return list(self.data.keys())

    # -----------------------------
    # RESAMPLING
    # -----------------------------
    def get_resampled(self, symbol, timeframe):
        """
        timeframe: '1s', '1m', '5m'
        Returns OHLCV DataFrame
        """
        if symbol not in self.data:
            return None

        with self.lock:
            ticks = list(self.data[symbol])

        if not ticks:
            return None

        df = pd.DataFrame(ticks)
        df["ts"] = pd.to_datetime(df["ts"], utc=True, format="ISO8601")
        df.set_index("ts", inplace=True)

        rule = {
            "1s": "1S",
            "1m": "1T",
            "5m": "5T"
        }[timeframe]

        ohlcv = df["price"].resample(rule).ohlc()
        ohlcv["volume"] = df["qty"].resample(rule).sum()
        ohlcv.dropna(inplace=True)

        self.resampled[timeframe][symbol] = ohlcv
        return ohlcv

    # -----------------------------
    # ANALYTICS HELPERS
    # -----------------------------
    def get_price_series(self, symbol, timeframe="1s"):
        rs = self.get_resampled(symbol, timeframe)
        if rs is None:
            return None
        return rs["close"]

    def get_latest_price(self, symbol):
        tick = self.get_latest_tick(symbol)
        return tick["price"] if tick else None
