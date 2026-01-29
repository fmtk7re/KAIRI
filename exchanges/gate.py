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

    # ------------------------------------------------------------------
    # Single-symbol fetch (original)
    # ------------------------------------------------------------------

    def fetch_ticker(self, symbol: str) -> TickerData:
        url = f"{BASE_URL}/futures/usdt/contracts/{symbol}"
        resp = requests.get(url, timeout=REQUEST_TIMEOUT_SECONDS)
        resp.raise_for_status()
        data = resp.json()

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

    # ------------------------------------------------------------------
    # Bulk helpers
    # ------------------------------------------------------------------

    def _fetch_all_contracts(self) -> list[dict]:
        """GET /futures/usdt/contracts  – returns every USDT-M contract."""
        url = f"{BASE_URL}/futures/usdt/contracts"
        resp = requests.get(url, timeout=REQUEST_TIMEOUT_SECONDS)
        resp.raise_for_status()
        return resp.json()

    def list_symbols(self) -> list[dict]:
        contracts = self._fetch_all_contracts()
        symbols: list[dict] = []
        for c in contracts:
            name = c.get("name", "")
            if name.endswith("_USDT"):
                base = name[:-5]
                symbols.append({"base": base, "symbol": name})
        return symbols

    def fetch_all_tickers(self) -> dict[str, TickerData]:
        """Fetch every USDT-M perpetual in a single API call."""
        contracts = self._fetch_all_contracts()
        now = datetime.now(timezone.utc)
        result: dict[str, TickerData] = {}

        for data in contracts:
            symbol = data.get("name", "")
            if not symbol.endswith("_USDT"):
                continue
            fi_seconds = data.get("funding_interval", 0)
            if not fi_seconds or fi_seconds <= 0:
                continue
            lp = data.get("last_price", "")
            if not lp or lp == "0":
                continue

            base = symbol[:-5]
            result[base] = TickerData(
                exchange=self.name,
                symbol=symbol,
                timestamp=now,
                last_price=lp,
                mark_price=data.get("mark_price", ""),
                index_price=data.get("index_price", ""),
                funding_rate=data.get("funding_rate", ""),
                funding_interval_hours=fi_seconds / 3600.0,
            )

        logger.info("Gate: fetched %d USDT-M contracts", len(result))
        return result
