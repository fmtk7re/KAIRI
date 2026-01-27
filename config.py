import os

SYMBOLS = {
    "gate": "RIVER_USDT",
    "phemex": "RIVERUSDT",
}

FETCH_INTERVAL_SECONDS = 60

REQUEST_TIMEOUT_SECONDS = 10

DATA_DIR = "data"

# Discord webhook URL (set via environment variable DISCORD_WEBHOOK_URL)
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL", "")
