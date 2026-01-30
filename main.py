import argparse
import logging
import signal
import sys
import time

import schedule

import config
from discover import discover_common_pairs
from exchanges.gate import GateExchange
from exchanges.phemex import PhemexExchange
from storage import save_pairs_json, save_ticker

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

EXCHANGES = {
    "gate": GateExchange(),
    "phemex": PhemexExchange(),
}


# ------------------------------------------------------------------
# Fetch strategies
# ------------------------------------------------------------------

def fetch_all_bulk() -> None:
    """Bulk-fetch every common pair (Gate: 1 call, Phemex: threaded)."""
    t0 = time.monotonic()

    try:
        gate_tickers = EXCHANGES["gate"].fetch_all_tickers()
    except Exception:
        logger.exception("Gate bulk fetch failed")
        gate_tickers = {}

    t1 = time.monotonic()

    try:
        phemex_tickers = EXCHANGES["phemex"].fetch_all_tickers()
    except Exception:
        logger.exception("Phemex bulk fetch failed")
        phemex_tickers = {}

    t2 = time.monotonic()

    common = sorted(set(gate_tickers) & set(phemex_tickers))

    saved = 0
    for base in common:
        gt = gate_tickers[base]
        pt = phemex_tickers[base]
        try:
            save_ticker(gt, base)
            save_ticker(pt, base)
            saved += 1
        except Exception:
            logger.exception("Failed to save %s", base)

    t3 = time.monotonic()
    logger.info(
        "Cycle done: gate=%.1fs phemex=%.1fs save=%.1fs | "
        "gate=%d phemex=%d common=%d saved=%d | total=%.1fs",
        t1 - t0, t2 - t1, t3 - t2,
        len(gate_tickers), len(phemex_tickers), len(common), saved,
        t3 - t0,
    )


def fetch_all_static() -> None:
    """Original per-pair fetch using the static PAIRS list."""
    for pair in config.PAIRS:
        pair_name = pair["name"]
        for ex_name, ex in EXCHANGES.items():
            symbol = pair.get(ex_name, "")
            if not symbol:
                continue
            try:
                ticker = ex.fetch_ticker(symbol)
                save_ticker(ticker, pair_name)
                logger.info(
                    "%s %s | last=%s fr8h=%.8f",
                    ticker.exchange, ticker.symbol,
                    ticker.last_price, ticker.funding_rate_8h,
                )
            except Exception:
                logger.exception("Failed to fetch %s from %s", pair_name, ex_name)


def fetch_all() -> None:
    try:
        if config.DISCOVER_ALL:
            fetch_all_bulk()
        else:
            fetch_all_static()
    except Exception:
        logger.exception("fetch_all() crashed – will retry next cycle")


# ------------------------------------------------------------------
# Entry point
# ------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Perpetual futures data collector")
    parser.add_argument(
        "--duration",
        type=int,
        default=0,
        help="Max run duration in seconds (0 = unlimited)",
    )
    args = parser.parse_args()

    signal.signal(signal.SIGINT, lambda *_: sys.exit(0))
    signal.signal(signal.SIGTERM, lambda *_: sys.exit(0))

    if config.DISCOVER_ALL:
        try:
            pairs = discover_common_pairs()
            save_pairs_json(pairs)
        except Exception:
            logger.exception(
                "Symbol discovery failed – falling back to static PAIRS"
            )
            pairs = config.PAIRS
        logger.info(
            "DISCOVER_ALL mode: %d pairs (interval=%ds, duration=%s)",
            len(pairs),
            config.FETCH_INTERVAL_SECONDS,
            f"{args.duration}s" if args.duration else "unlimited",
        )
    else:
        pair_names = ", ".join(p["name"] for p in config.PAIRS)
        logger.info(
            "Static mode: pairs=%s, interval=%ds, duration=%s",
            pair_names,
            config.FETCH_INTERVAL_SECONDS,
            f"{args.duration}s" if args.duration else "unlimited",
        )

    # Run once immediately (crash-proof)
    fetch_all()

    schedule.every(config.FETCH_INTERVAL_SECONDS).seconds.do(fetch_all)

    start = time.monotonic()
    while True:
        if args.duration and (time.monotonic() - start) >= args.duration:
            logger.info("Duration limit reached. Stopping.")
            break
        schedule.run_pending()
        time.sleep(1)


if __name__ == "__main__":
    main()
