from datetime import datetime, timezone

def normalize_trade(data):
    return {
        "ts": datetime.fromtimestamp(
            data["E"] / 1000, tz=timezone.utc
        ).isoformat(),
        "symbol": data["s"].lower(),
        "price": float(data["p"]),
        "qty": float(data["q"])
    }
