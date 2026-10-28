"""Command-line entry point: fetch NBP data for a date range and store it in bronze.

Examples:
    nbp-ingest --dataset rates_a --start 2024-01-01 --end 2024-03-31
    nbp-ingest --dataset gold --start 2013-01-02 --end 2024-12-31
"""

from __future__ import annotations

import argparse
import logging
from datetime import date

from nbp_lakehouse.config import Settings
from nbp_lakehouse.ingest.bronze_writer import write_bronze
from nbp_lakehouse.ingest.nbp_client import NbpClient

DATASETS = ("rates_a", "rates_b", "rates_c", "gold")


def ingest(dataset: str, start: date, end: date, settings: Settings, client: NbpClient) -> int:
    """Fetch one dataset and write it to bronze. Returns the number of records written."""
    if dataset == "gold":
        records = client.get_gold_prices(start, end)
    else:
        table = dataset.split("_")[1]
        records = client.get_exchange_rate_tables(table, start, end)

    path = write_bronze(records, dataset, start, end, settings.data_dir)
    logging.info("Wrote %d records to %s", len(records), path)
    return len(records)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Ingest NBP data into the bronze layer.")
    parser.add_argument("--dataset", choices=DATASETS, required=True)
    parser.add_argument("--start", type=date.fromisoformat, required=True)
    parser.add_argument("--end", type=date.fromisoformat, required=True)
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    settings = Settings.from_env()
    client = NbpClient(timeout=settings.http_timeout)
    ingest(args.dataset, args.start, args.end, settings, client)


if __name__ == "__main__":
    main()
