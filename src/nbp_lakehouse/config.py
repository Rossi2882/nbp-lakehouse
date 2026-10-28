"""Project configuration and NBP API constants."""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import date
from pathlib import Path

NBP_API_BASE_URL = "https://api.nbp.pl/api"

# NBP API limits a single query to a maximum date range.
MAX_DAYS_EXCHANGE_RATES = 93
MAX_DAYS_GOLD = 367

# Earliest dates with data available in the API.
EXCHANGE_RATES_START = date(2002, 1, 2)
GOLD_PRICES_START = date(2013, 1, 2)

# Exchange rate tables: A – average rates (major currencies),
# B – average rates (other currencies), C – bid/ask rates.
EXCHANGE_RATE_TABLES = ("A", "B", "C")


@dataclass(frozen=True)
class Settings:
    data_dir: Path
    http_timeout: float

    @classmethod
    def from_env(cls) -> Settings:
        return cls(
            data_dir=Path(os.getenv("NBP_DATA_DIR", "./data")),
            http_timeout=float(os.getenv("NBP_HTTP_TIMEOUT", "30")),
        )
