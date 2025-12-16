import asyncio
import threading
import uvicorn
from ingestion.websocket_client import BinanceWebSocketClient
from backend.api import app, market_state


def handle_tick(tick):
    market_state.add_tick(tick)


async def start_ws():
    client = BinanceWebSocketClient(
        symbols=["btcusdt", "ethusdt"],
        on_tick_callback=handle_tick
    )
    await client.start()


def start_api():
    """
    Run FastAPI using uvicorn in a dedicated thread.
    """
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )


if __name__ == "__main__":
    # Start API server
    api_thread = threading.Thread(
        target=start_api,
        daemon=True
    )
    api_thread.start()

    # Start WebSocket ingestion
    try:
        asyncio.run(start_ws())
    except KeyboardInterrupt:
        print("Shutting down...")
