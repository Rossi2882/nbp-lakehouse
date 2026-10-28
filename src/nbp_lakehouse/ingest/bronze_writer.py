"""Writes raw API responses to the bronze layer, unchanged, with ingestion metadata."""

from __future__ import annotations

import json
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any


def write_bronze(
    records: list[dict[str, Any]],
    dataset: str,
    start: date,
    end: date,
    data_dir: Path,
    ingested_at: datetime | None = None,
) -> Path:
    """Save raw records as JSON in ``bronze/<dataset>/ingest_date=YYYY-MM-DD/``.

    The payload is stored as-is inside an envelope with metadata, so the bronze layer
    always keeps the original source data and can be reprocessed later.
    """
    ingested_at = ingested_at or datetime.now(timezone.utc)
    target_dir = data_dir / "bronze" / dataset / f"ingest_date={ingested_at:%Y-%m-%d}"
    target_dir.mkdir(parents=True, exist_ok=True)

    target = target_dir / f"{dataset}_{start:%Y%m%d}_{end:%Y%m%d}.json"
    envelope = {
        "dataset": dataset,
        "range_start": start.isoformat(),
        "range_end": end.isoformat(),
        "ingested_at": ingested_at.isoformat(),
        "record_count": len(records),
        "records": records,
    }
    target.write_text(json.dumps(envelope, ensure_ascii=False, indent=2), encoding="utf-8")
    return target
