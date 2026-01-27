from abc import ABC, abstractmethod

from models import TickerData


class BaseExchange(ABC):
    @property
    @abstractmethod
    def name(self) -> str: ...

    @abstractmethod
    def fetch_ticker(self, symbol: str) -> TickerData: ...
