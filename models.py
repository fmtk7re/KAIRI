from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass
class TickerData:
    exchange: str
    symbol: str
    timestamp: datetime
    last_price: str
    mark_price: str
    index_price: str
    funding_rate: str
    funding_interval_hours: float

    @property
    def funding_rate_8h(self) -> float:
        """Funding rate normalized to 8-hour basis."""
        try:
            raw = float(self.funding_rate)
        except (ValueError, TypeError):
            return 0.0
        if self.funding_interval_hours <= 0:
            return 0.0
        return raw * (8.0 / self.funding_interval_hours)

    @staticmethod
    def csv_header() -> str:
        return "timestamp,exchange,symbol,last_price,mark_price,index_price,funding_rate,funding_interval_h,funding_rate_8h"

    def to_csv_row(self) -> str:
        ts = self.timestamp.strftime("%Y-%m-%dT%H:%M:%S%z")
        return (
            f"{ts},{self.exchange},{self.symbol},"
            f"{self.last_price},{self.mark_price},{self.index_price},"
            f"{self.funding_rate},{self.funding_interval_hours},{self.funding_rate_8h:.8f}"
        )
