import os

# When True, auto-discover every USDT perpetual pair common to both
# Gate.io and Phemex at startup.  When False, use the static PAIRS list.
DISCOVER_ALL = True

# Static pair list (used when DISCOVER_ALL is False)
PAIRS = [
    {"name": "RIVER", "gate": "RIVER_USDT", "phemex": "RIVERUSDT"},
    {"name": "SENT", "gate": "SENT_USDT", "phemex": "SENTUSDT"},
]

FETCH_INTERVAL_SECONDS = 60

REQUEST_TIMEOUT_SECONDS = 10

DATA_DIR = "data"

# Discord notifications (disabled – set a URL to re-enable)
DISCORD_WEBHOOK_URL = ""
