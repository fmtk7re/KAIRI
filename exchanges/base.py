from abc import ABC, abstractmethod

from models import TickerData


class BaseExchange(ABC):
    @property
    @abstractmethod
    def name(self) -> str: ...

    @abstractmethod
    def fetch_ticker(self, symbol: str) -> TickerData: ...

    @abstractmethod
    def list_symbols(self) -> list[dict]:
        """Return list of dicts with keys: base, symbol.

        ``base`` is the normalised token name (e.g. "BTC"),
        ``symbol`` is the exchange-native symbol (e.g. "BTC_USDT" / "BTCUSDT").
        """
        ...

    def fetch_all_tickers(self) -> dict[str, TickerData]:
        """Fetch tickers for every listed symbol.

        Returns a dict keyed by *base* name.  Subclasses should override
        with a bulk-fetch implementation when the exchange API allows it.
        """
        raise NotImplementedError
