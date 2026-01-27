import logging
from datetime import datetime, timezone

import requests

from config import REQUEST_TIMEOUT_SECONDS
from models import TickerData
from exchanges.base import BaseExchange

logger = logging.getLogger(__name__)

BASE_URL = "https://api.phemex.com"


class PhemexExchange(BaseExchange):
    def __init__(self) -> None:
        # Cache: symbol -> funding interval in hours
        self._fi_cache: dict[str, float] = {}

    @property
    def name(self) -> str:
        return "phemex"

    def _fetch_funding_interval(self, symbol: str) -> float:
        """Fetch funding interval from /cfg/v2/products endpoint."""
        if symbol in self._fi_cache:
            return self._fi_cache[symbol]

        url = f"{BASE_URL}/cfg/v2/products"
        resp = requests.get(url, timeout=REQUEST_TIMEOUT_SECONDS)
        resp.raise_for_status()
        body = resp.json()

        # Search in perpProductsV2 for the matching symbol
        for product in body.get("data", {}).get("perpProductsV2", []):
            if product.get("symbol") == symbol:
                fi_seconds = product.get("fundingInterval", 0)
                if fi_seconds and fi_seconds > 0:
                    fi_hours = fi_seconds / 3600.0
                    self._fi_cache[symbol] = fi_hours
                    logger.info(
                        "Phemex %s funding interval: %ds (%.1fh)",
                        symbol, fi_seconds, fi_hours,
                    )
                    return fi_hours

        raise ValueError(
            f"Phemex API did not return fundingInterval for {symbol}"
        )

    def fetch_ticker(self, symbol: str) -> TickerData:
        fi_hours = self._fetch_funding_interval(symbol)

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
