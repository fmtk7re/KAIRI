import logging
from typing import Optional

import requests

from config import DISCORD_WEBHOOK_URL
from models import TickerData

logger = logging.getLogger(__name__)


def _pct_diff(a: str, b: str) -> Optional[float]:
    """Calculate percentage difference: (a - b) / b * 100."""
    try:
        fa, fb = float(a), float(b)
    except (ValueError, TypeError):
        return None
    if fb == 0:
        return None
    return (fa - fb) / fb * 100.0


def _fmt_pct(val: Optional[float]) -> str:
    if val is None:
        return "N/A"
    sign = "+" if val >= 0 else ""
    return f"{sign}{val:.4f}%"


def build_gap_message(gate: TickerData, phemex: TickerData) -> str:
    """Build a human-readable gap report (Gate - Phemex)."""
    last_gap = _pct_diff(gate.last_price, phemex.last_price)
    mark_gap = _pct_diff(gate.mark_price, phemex.mark_price)
    index_gap = _pct_diff(gate.index_price, phemex.index_price)
    fr_8h_diff = gate.funding_rate_8h - phemex.funding_rate_8h

    ts = gate.timestamp.strftime("%Y-%m-%d %H:%M:%S UTC")

    lines = [
        f"**RIVER Perpetual Futures Monitor** - {ts}",
        "",
        "```",
        f"{'':>12} {'Gate':>14} {'Phemex':>14} {'Gap':>10}",
        f"{'Last':>12} {gate.last_price:>14} {phemex.last_price:>14} {_fmt_pct(last_gap):>10}",
        f"{'Mark':>12} {gate.mark_price:>14} {phemex.mark_price:>14} {_fmt_pct(mark_gap):>10}",
        f"{'Index':>12} {gate.index_price:>14} {phemex.index_price:>14} {_fmt_pct(index_gap):>10}",
        "",
        f"{'FR (raw)':>12} {gate.funding_rate:>14} {phemex.funding_rate:>14}",
        f"{'FR intv':>12} {gate.funding_interval_hours:>13.0f}h {phemex.funding_interval_hours:>13.0f}h",
        f"{'FR (8h)':>12} {gate.funding_rate_8h:>14.8f} {phemex.funding_rate_8h:>14.8f} {_fmt_pct_raw(fr_8h_diff):>10}",
        "```",
    ]
    return "\n".join(lines)


def _fmt_pct_raw(val: float) -> str:
    """Format a raw rate difference as percentage points."""
    sign = "+" if val >= 0 else ""
    return f"{sign}{val:.8f}"


def send_discord(message: str) -> None:
    """Send a message to Discord via webhook."""
    if not DISCORD_WEBHOOK_URL:
        return
    try:
        resp = requests.post(
            DISCORD_WEBHOOK_URL,
            json={"content": message},
            timeout=10,
        )
        if resp.status_code >= 400:
            logger.warning("Discord webhook returned %d: %s", resp.status_code, resp.text)
    except Exception:
        logger.exception("Failed to send Discord notification")
