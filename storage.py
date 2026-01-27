import os
from datetime import datetime, timezone

from config import DATA_DIR
from models import TickerData


def _get_csv_path() -> str:
    os.makedirs(DATA_DIR, exist_ok=True)
    date_str = datetime.now(timezone.utc).strftime("%Y%m%d")
    return os.path.join(DATA_DIR, f"{date_str}_river_futures.csv")


def save_ticker(ticker: TickerData) -> None:
    path = _get_csv_path()
    write_header = not os.path.exists(path)

    with open(path, "a") as f:
        if write_header:
            f.write(TickerData.csv_header() + "\n")
        f.write(ticker.to_csv_row() + "\n")
