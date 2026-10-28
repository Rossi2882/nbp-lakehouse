"""HTTP client for the public NBP Web API (https://api.nbp.pl)."""

from __future__ import annotations

import logging
from datetime import date
from typing import Any

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from nbp_lakehouse.config import (
    EXCHANGE_RATE_TABLES,
    MAX_DAYS_EXCHANGE_RATES,
    MAX_DAYS_GOLD,
    NBP_API_BASE_URL,
)
from nbp_lakehouse.ingest.dates import date_chunks

logger = logging.getLogger(__name__)


class NbpApiError(RuntimeError):
    """Raised when the NBP API returns an unexpected response."""


def _build_session(retries: int) -> requests.Session:
    session = requests.Session()
    retry = Retry(
        total=retries,
        backoff_factor=1.0,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=("GET",),
    )
    session.mount("https://", HTTPAdapter(max_retries=retry))
    session.headers.update({"Accept": "application/json"})
    return session


class NbpClient:
    """Fetches exchange rate tables and gold prices, splitting long ranges automatically."""

    def __init__(
        self,
        base_url: str = NBP_API_BASE_URL,
        timeout: float = 30.0,
        retries: int = 3,
        session: requests.Session | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = session or _build_session(retries)

    def _get(self, path: str) -> list[dict[str, Any]]:
        url = f"{self.base_url}/{path}"
        logger.debug("GET %s", url)
        try:
            response = self.session.get(url, params={"format": "json"}, timeout=self.timeout)
        except requests.RequestException as exc:
            # Network errors and exhausted retries (e.g. repeated 5xx) end up here.
            raise NbpApiError(f"Request to {url} failed: {exc}") from exc

        # NBP returns 404 when there is no data in the range (weekends, holidays).
        if response.status_code == 404:
            logger.info("No data for %s", url)
            return []
        if response.status_code != 200:
            raise NbpApiError(f"NBP API returned {response.status_code} for {url}: {response.text}")

        payload = response.json()
        if not isinstance(payload, list):
            raise NbpApiError(f"Unexpected payload type from {url}: {type(payload).__name__}")
        return payload

    def get_exchange_rate_tables(self, table: str, start: date, end: date) -> list[dict[str, Any]]:
        """Return all exchange rate tables of the given type published between start and end."""
        table = table.upper()
        if table not in EXCHANGE_RATE_TABLES:
            raise ValueError(f"Unknown table {table!r}, expected one of {EXCHANGE_RATE_TABLES}")

        results: list[dict[str, Any]] = []
        for chunk_start, chunk_end in date_chunks(start, end, MAX_DAYS_EXCHANGE_RATES):
            results.extend(
                self._get(
                    f"exchangerates/tables/{table}/{chunk_start:%Y-%m-%d}/{chunk_end:%Y-%m-%d}/"
                )
            )
        return results

    def get_gold_prices(self, start: date, end: date) -> list[dict[str, Any]]:
        """Return daily gold prices (PLN per 1 g of 1000 fineness gold) between start and end."""
        results: list[dict[str, Any]] = []
        for chunk_start, chunk_end in date_chunks(start, end, MAX_DAYS_GOLD):
            results.extend(self._get(f"cenyzlota/{chunk_start:%Y-%m-%d}/{chunk_end:%Y-%m-%d}/"))
        return results
