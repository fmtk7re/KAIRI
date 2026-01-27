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
        url = f"{BASE_URL}/futures/usdt/tickers"
        params = {"contract": symbol}
        resp = requests.get(url, params=params, timeout=REQUEST_TIMEOUT_SECONDS)
        resp.raise_for_status()
        data = resp.json()

        if isinstance(data, list):
            if not data:
                raise ValueError(f"Gate.io returned empty list for {symbol}")
            data = data[0]

        return TickerData(
            exchange=self.name,
            symbol=symbol,
            timestamp=datetime.now(timezone.utc),
            last_price=data.get("last", ""),
            mark_price=data.get("mark_price", ""),
            index_price=data.get("index_price", ""),
            funding_rate=data.get("funding_rate", ""),
        )
