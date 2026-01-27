import logging
import signal
import sys
import time

import schedule

from config import FETCH_INTERVAL_SECONDS, SYMBOLS
from exchanges.gate import GateExchange
from exchanges.phemex import PhemexExchange
from storage import save_ticker

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

EXCHANGES = [
    GateExchange(),
    PhemexExchange(),
]


def fetch_all() -> None:
    for ex in EXCHANGES:
        symbol = SYMBOLS.get(ex.name, "")
        if not symbol:
            continue
        try:
            ticker = ex.fetch_ticker(symbol)
            save_ticker(ticker)
            logger.info(
                "%s %s | last=%s mark=%s index=%s fr=%s",
                ticker.exchange,
                ticker.symbol,
                ticker.last_price,
                ticker.mark_price,
                ticker.index_price,
                ticker.funding_rate,
            )
        except Exception:
            logger.exception("Failed to fetch from %s", ex.name)


def main() -> None:
    signal.signal(signal.SIGINT, lambda *_: sys.exit(0))
    signal.signal(signal.SIGTERM, lambda *_: sys.exit(0))

    logger.info(
        "Starting RIVER perpetual futures data collector (interval=%ds)",
        FETCH_INTERVAL_SECONDS,
    )

    # Run once immediately at startup
    fetch_all()

    schedule.every(FETCH_INTERVAL_SECONDS).seconds.do(fetch_all)

    while True:
        schedule.run_pending()
        time.sleep(1)


if __name__ == "__main__":
    main()
