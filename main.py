import argparse
import logging
import signal
import sys
import time

import schedule

from config import FETCH_INTERVAL_SECONDS, SYMBOLS
from exchanges.gate import GateExchange
from exchanges.phemex import PhemexExchange
from notify import build_gap_message, send_discord
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
    tickers = {}
    for ex in EXCHANGES:
        symbol = SYMBOLS.get(ex.name, "")
        if not symbol:
            continue
        try:
            ticker = ex.fetch_ticker(symbol)
            save_ticker(ticker)
            tickers[ex.name] = ticker
            logger.info(
                "%s %s | last=%s mark=%s index=%s fr=%s (intv=%gh, fr8h=%.8f)",
                ticker.exchange,
                ticker.symbol,
                ticker.last_price,
                ticker.mark_price,
                ticker.index_price,
                ticker.funding_rate,
                ticker.funding_interval_hours,
                ticker.funding_rate_8h,
            )
        except Exception:
            logger.exception("Failed to fetch from %s", ex.name)

    # Calculate and report gap if both exchanges returned data
    gate = tickers.get("gate")
    phemex = tickers.get("phemex")
    if gate and phemex:
        message = build_gap_message(gate, phemex)
        logger.info("Gap report:\n%s", message)
        send_discord(message)


def main() -> None:
    parser = argparse.ArgumentParser(description="RIVER perpetual futures data collector")
    parser.add_argument(
        "--duration",
        type=int,
        default=0,
        help="Max run duration in seconds (0 = unlimited)",
    )
    args = parser.parse_args()

    signal.signal(signal.SIGINT, lambda *_: sys.exit(0))
    signal.signal(signal.SIGTERM, lambda *_: sys.exit(0))

    logger.info(
        "Starting RIVER perpetual futures data collector (interval=%ds, duration=%s)",
        FETCH_INTERVAL_SECONDS,
        f"{args.duration}s" if args.duration else "unlimited",
    )

    # Run once immediately at startup
    fetch_all()

    schedule.every(FETCH_INTERVAL_SECONDS).seconds.do(fetch_all)

    start = time.monotonic()
    while True:
        if args.duration and (time.monotonic() - start) >= args.duration:
            logger.info("Duration limit reached. Stopping.")
            break
        schedule.run_pending()
        time.sleep(1)


if __name__ == "__main__":
    main()
