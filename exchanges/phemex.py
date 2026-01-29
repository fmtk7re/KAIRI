import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from typing import Optional

import requests

from config import REQUEST_TIMEOUT_SECONDS
from models import TickerData
from exchanges.base import BaseExchange

logger = logging.getLogger(__name__)

BASE_URL = "https://api.phemex.com"

# Max parallel requests when bulk-fetching individual tickers
_BULK_WORKERS = 10


class PhemexExchange(BaseExchange):
    def __init__(self) -> None:
        # Cache: symbol -> funding interval in hours
        self._fi_cache: dict[str, float] = {}

    @property
    def name(self) -> str:
        return "phemex"

    # ------------------------------------------------------------------
    # Funding-interval helpers
    # ------------------------------------------------------------------

    def _fetch_all_products(self) -> list[dict]:
        """Fetch /public/products and return perpProductsV2 list."""
        url = f"{BASE_URL}/public/products"
        resp = requests.get(url, timeout=REQUEST_TIMEOUT_SECONDS)
        resp.raise_for_status()
        body = resp.json()
        data = body.get("data", body)
        return data.get("perpProductsV2", [])

    def _ensure_fi_cache(self) -> None:
        """Populate the funding-interval cache from /public/products."""
        if self._fi_cache:
            return
        for p in self._fetch_all_products():
            sym = p.get("symbol", "")
            fi = p.get("fundingInterval", 0)
            if sym and fi and fi > 0:
                self._fi_cache[sym] = fi / 3600.0

    def _fetch_funding_interval(self, symbol: str) -> float:
        """Fetch funding interval from /public/products endpoint."""
        if symbol in self._fi_cache:
            return self._fi_cache[symbol]

        url = f"{BASE_URL}/public/products"
        resp = requests.get(url, timeout=REQUEST_TIMEOUT_SECONDS)
        resp.raise_for_status()
        body = resp.json()

        data = body.get("data", body)
        for product in data.get("perpProductsV2", []):
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

    # ------------------------------------------------------------------
    # Single-symbol fetch (original)
    # ------------------------------------------------------------------

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

    # ------------------------------------------------------------------
    # Bulk helpers
    # ------------------------------------------------------------------

    def list_symbols(self) -> list[dict]:
        products = self._fetch_all_products()
        symbols: list[dict] = []
        for p in products:
            sym = p.get("symbol", "")
            if not sym.endswith("USDT"):
                continue
            base = sym[:-4]
            # Cache the funding interval while we're at it
            fi = p.get("fundingInterval", 0)
            if fi and fi > 0:
                self._fi_cache[sym] = fi / 3600.0
            symbols.append({"base": base, "symbol": sym})
        return symbols

    def _safe_fetch_ticker(self, symbol: str) -> Optional[TickerData]:
        """fetch_ticker wrapper that returns None instead of raising."""
        try:
            return self.fetch_ticker(symbol)
        except Exception as exc:
            logger.debug("Phemex skip %s: %s", symbol, exc)
            return None

    def fetch_all_tickers(self) -> dict[str, TickerData]:
        """Fetch tickers for all USDT perpetual symbols (threaded)."""
        # Pre-populate funding-interval cache in one call
        symbols = self.list_symbols()
        result: dict[str, TickerData] = {}

        with ThreadPoolExecutor(max_workers=_BULK_WORKERS) as pool:
            future_map = {
                pool.submit(self._safe_fetch_ticker, s["symbol"]): s
                for s in symbols
            }
            for future in as_completed(future_map):
                s = future_map[future]
                ticker = future.result()
                if ticker is not None:
                    result[s["base"]] = ticker

        logger.info("Phemex: fetched %d / %d tickers", len(result), len(symbols))
        return result
