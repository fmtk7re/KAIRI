import os

SYMBOLS = {
    "gate": "RIVER_USDT",
    "phemex": "RIVERUSDT",
}

FETCH_INTERVAL_SECONDS = 60

REQUEST_TIMEOUT_SECONDS = 10

DATA_DIR = "data"

# Fallback funding interval (hours) when not available from API
DEFAULT_FUNDING_INTERVAL_HOURS = {
    "gate": 8.0,
    "phemex": 8.0,
}

# Discord webhook URL (set via environment variable DISCORD_WEBHOOK_URL)
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL", "")
