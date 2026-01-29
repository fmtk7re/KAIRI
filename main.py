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
from notify import build_gap_message, send_discord
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
    try:
        gate_tickers = EXCHANGES["gate"].fetch_all_tickers()
    except Exception:
        logger.exception("Gate bulk fetch failed")
        gate_tickers = {}

    try:
        phemex_tickers = EXCHANGES["phemex"].fetch_all_tickers()
    except Exception:
        logger.exception("Phemex bulk fetch failed")
        phemex_tickers = {}

    common = sorted(set(gate_tickers) & set(phemex_tickers))
    logger.info("Saving %d common pairs", len(common))

    for base in common:
        gt = gate_tickers[base]
        pt = phemex_tickers[base]
        try:
            save_ticker(gt, base)
            save_ticker(pt, base)
        except Exception:
            logger.exception("Failed to save %s", base)


def fetch_all_static() -> None:
    """Original per-pair fetch using the static PAIRS list."""
    for pair in config.PAIRS:
        pair_name = pair["name"]
        tickers = {}
        for ex_name, ex in EXCHANGES.items():
            symbol = pair.get(ex_name, "")
            if not symbol:
                continue
            try:
                ticker = ex.fetch_ticker(symbol)
                save_ticker(ticker, pair_name)
                tickers[ex_name] = ticker
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
                logger.exception("Failed to fetch %s from %s", pair_name, ex_name)

        gate = tickers.get("gate")
        phemex = tickers.get("phemex")
        if gate and phemex:
            message = build_gap_message(gate, phemex, pair_name)
            logger.info("Gap report [%s]:\n%s", pair_name, message)
            send_discord(message)


def fetch_all() -> None:
    if config.DISCOVER_ALL:
        fetch_all_bulk()
    else:
        fetch_all_static()


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
        pairs = discover_common_pairs()
        save_pairs_json(pairs)
        logger.info(
            "DISCOVER_ALL mode: %d common pairs found (interval=%ds, duration=%s)",
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

    # Run once immediately at startup
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
