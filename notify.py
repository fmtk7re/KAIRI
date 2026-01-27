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

    ts = gate.timestamp.strftime("%Y-%m-%d %H:%M UTC")

    lines = [
        f"**RIVER Monitor** | {ts}",
        "```",
        "[Gate]",
        f" Last:  {gate.last_price}",
        f" Mark:  {gate.mark_price}",
        f" Index: {gate.index_price}",
        f" FR: {gate.funding_rate}",
        f"   ({gate.funding_interval_hours:.0f}h -> 8h: {gate.funding_rate_8h:.8f})",
        "",
        "[Phemex]",
        f" Last:  {phemex.last_price}",
        f" Mark:  {phemex.mark_price}",
        f" Index: {phemex.index_price}",
        f" FR: {phemex.funding_rate}",
        f"   ({phemex.funding_interval_hours:.0f}h -> 8h: {phemex.funding_rate_8h:.8f})",
        "",
        "[Gap] Gate - Phemex",
        f" Last:  {_fmt_pct(last_gap)}",
        f" Mark:  {_fmt_pct(mark_gap)}",
        f" Index: {_fmt_pct(index_gap)}",
        f" FR8h:  {_fmt_pct_raw(fr_8h_diff)}",
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
