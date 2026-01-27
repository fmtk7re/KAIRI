import logging
from datetime import datetime, timezone

import requests

from config import DEFAULT_FUNDING_INTERVAL_HOURS, REQUEST_TIMEOUT_SECONDS
from models import TickerData
from exchanges.base import BaseExchange

logger = logging.getLogger(__name__)

BASE_URL = "https://api.phemex.com"


class PhemexExchange(BaseExchange):
    @property
    def name(self) -> str:
        return "phemex"

    def fetch_ticker(self, symbol: str) -> TickerData:
        url = f"{BASE_URL}/md/v2/ticker/24hr"
        params = {"symbol": symbol}
        resp = requests.get(url, params=params, timeout=REQUEST_TIMEOUT_SECONDS)
        resp.raise_for_status()
        body = resp.json()

        if body.get("error") is not None:
            raise ValueError(
                f"Phemex API error: {body.get('error')}"
            )

        data = body.get("result", {})

        fi_hours = DEFAULT_FUNDING_INTERVAL_HOURS.get(self.name, 8.0)

        return TickerData(
            exchange=self.name,
            symbol=symbol,
            timestamp=datetime.now(timezone.utc),
            last_price=data.get("closeRp", ""),
            mark_price=data.get("markPriceRp", ""),
            index_price=data.get("indexPriceRp", ""),
            funding_rate=data.get("fundingRateRr", ""),
            funding_interval_hours=fi_hours,
        )
