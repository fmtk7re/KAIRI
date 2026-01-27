import logging
from datetime import datetime, timezone

import requests

from config import REQUEST_TIMEOUT_SECONDS
from models import TickerData
from exchanges.base import BaseExchange

logger = logging.getLogger(__name__)

BASE_URL = "https://api.gateio.ws/api/v4"


class GateExchange(BaseExchange):
    @property
    def name(self) -> str:
        return "gate"

    def fetch_ticker(self, symbol: str) -> TickerData:
        # Contract endpoint returns prices + funding_interval in one call
        url = f"{BASE_URL}/futures/usdt/contracts/{symbol}"
        resp = requests.get(url, timeout=REQUEST_TIMEOUT_SECONDS)
        resp.raise_for_status()
        data = resp.json()

        # funding_interval is in seconds; convert to hours
        fi_seconds = data.get("funding_interval", 0)
        if not fi_seconds or fi_seconds <= 0:
            raise ValueError(
                f"Gate API did not return funding_interval for {symbol}"
            )
        fi_hours = fi_seconds / 3600.0

        return TickerData(
            exchange=self.name,
            symbol=symbol,
            timestamp=datetime.now(timezone.utc),
            last_price=data.get("last_price", ""),
            mark_price=data.get("mark_price", ""),
            index_price=data.get("index_price", ""),
            funding_rate=data.get("funding_rate", ""),
            funding_interval_hours=fi_hours,
        )
