import json
import os
from datetime import datetime, timezone

from config import DATA_DIR
from models import TickerData


def _get_csv_path(pair_name: str) -> str:
    os.makedirs(DATA_DIR, exist_ok=True)
    date_str = datetime.now(timezone.utc).strftime("%Y%m%d")
    return os.path.join(DATA_DIR, f"{date_str}_{pair_name.lower()}_futures.csv")


def save_ticker(ticker: TickerData, pair_name: str) -> None:
    path = _get_csv_path(pair_name)
    write_header = not os.path.exists(path)

    with open(path, "a") as f:
        if write_header:
            f.write(TickerData.csv_header() + "\n")
        f.write(ticker.to_csv_row() + "\n")


def save_pairs_json(pairs: list[dict]) -> None:
    """Write discovered common pairs to data/pairs.json.

    The dashboard reads this file so it does not need to call
    the exchange APIs itself just to build the symbol list.
    """
    os.makedirs(DATA_DIR, exist_ok=True)
    path = os.path.join(DATA_DIR, "pairs.json")
    with open(path, "w") as f:
        json.dump(pairs, f, separators=(",", ":"))
