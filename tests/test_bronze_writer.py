import json
from datetime import date, datetime, timezone

from nbp_lakehouse.ingest.bronze_writer import write_bronze


def test_writes_envelope_with_metadata(tmp_path):
    records = [{"data": "2024-01-02", "cena": 262.94}]
    ingested_at = datetime(2024, 1, 3, 8, 0, tzinfo=timezone.utc)

    path = write_bronze(
        records, "gold", date(2024, 1, 1), date(2024, 1, 31), tmp_path, ingested_at=ingested_at
    )

    assert path == tmp_path / "bronze/gold/ingest_date=2024-01-03/gold_20240101_20240131.json"
    content = json.loads(path.read_text(encoding="utf-8"))
    assert content["record_count"] == 1
    assert content["records"] == records
    assert content["range_start"] == "2024-01-01"
    assert content["ingested_at"] == "2024-01-03T08:00:00+00:00"


def test_empty_result_is_still_written(tmp_path):
    path = write_bronze([], "rates_a", date(2024, 1, 6), date(2024, 1, 7), tmp_path)

    assert json.loads(path.read_text(encoding="utf-8"))["record_count"] == 0
