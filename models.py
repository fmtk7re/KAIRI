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

    @staticmethod
    def csv_header() -> str:
        return "timestamp,exchange,symbol,last_price,mark_price,index_price,funding_rate"

    def to_csv_row(self) -> str:
        ts = self.timestamp.strftime("%Y-%m-%dT%H:%M:%S%z")
        return f"{ts},{self.exchange},{self.symbol},{self.last_price},{self.mark_price},{self.index_price},{self.funding_rate}"
