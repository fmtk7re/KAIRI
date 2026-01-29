"""Discover perpetual-futures symbols common to Gate.io and Phemex."""

import logging

from exchanges.gate import GateExchange
from exchanges.phemex import PhemexExchange

logger = logging.getLogger(__name__)


def discover_common_pairs() -> list[dict]:
    """Return a sorted list of pairs available on **both** exchanges.

    Each item has the shape::

        {"name": "BTC", "gate": "BTC_USDT", "phemex": "BTCUSDT"}
    """
    gate = GateExchange()
    phemex = PhemexExchange()

    gate_syms = gate.list_symbols()
    phemex_syms = phemex.list_symbols()

    gate_map = {s["base"]: s["symbol"] for s in gate_syms}
    phemex_map = {s["base"]: s["symbol"] for s in phemex_syms}

    common_bases = sorted(set(gate_map) & set(phemex_map))

    pairs = [
        {"name": base, "gate": gate_map[base], "phemex": phemex_map[base]}
        for base in common_bases
    ]

    logger.info(
        "Discovered %d common pairs (Gate=%d, Phemex=%d)",
        len(pairs),
        len(gate_syms),
        len(phemex_syms),
    )
    return pairs


# ------------------------------------------------------------------
# CLI helper – run ``python discover.py`` to inspect available pairs
# ------------------------------------------------------------------
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )
    pairs = discover_common_pairs()
    print(f"\nFound {len(pairs)} common pairs:\n")
    for p in pairs:
        print(f"  {p['name']:12s} | Gate: {p['gate']:20s} | Phemex: {p['phemex']}")
