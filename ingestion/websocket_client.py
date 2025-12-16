import asyncio
import json
import websockets
from datetime import datetime
from ingestion.normalizer import normalize_trade


class BinanceWebSocketClient:
    """
    Binance Futures trade stream client.
    One connection per symbol.
    """

    BASE_URL = "wss://fstream.binance.com/ws"

    def __init__(self, symbols, on_tick_callback, reconnect_delay=5):
        self.symbols = symbols
        self.on_tick = on_tick_callback
        self.reconnect_delay = reconnect_delay

    async def _connect_symbol(self, symbol):
        url = f"{self.BASE_URL}/{symbol}@trade"

        while True:
            try:
                async with websockets.connect(url, ping_interval=20) as ws:
                    print(f"[CONNECTED] {symbol}")
                    async for message in ws:
                        data = json.loads(message)

                        if data.get("e") == "trade":
                            tick = normalize_trade(data)

                            # Push tick without blocking event loop
                            asyncio.get_running_loop().run_in_executor(
                                None, self.on_tick, tick
                            )

            except Exception as e:
                print(f"[DISCONNECTED] {symbol}: {e}")
                await asyncio.sleep(self.reconnect_delay)

    async def start(self):
        tasks = [self._connect_symbol(symbol) for symbol in self.symbols]
        await asyncio.gather(*tasks)
