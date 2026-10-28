from datetime import date

import pytest

from nbp_lakehouse.ingest.dates import date_chunks


def test_single_chunk_when_range_fits():
    chunks = list(date_chunks(date(2024, 1, 1), date(2024, 1, 31), 93))
    assert chunks == [(date(2024, 1, 1), date(2024, 1, 31))]


def test_range_is_split_without_gaps_or_overlaps():
    start, end = date(2024, 1, 1), date(2024, 12, 31)
    chunks = list(date_chunks(start, end, 93))

    assert chunks[0][0] == start
    assert chunks[-1][1] == end
    for (_, prev_end), (next_start, _) in zip(chunks, chunks[1:], strict=False):
        assert (next_start - prev_end).days == 1
    assert all((e - s).days + 1 <= 93 for s, e in chunks)


def test_single_day_range():
    assert list(date_chunks(date(2024, 5, 1), date(2024, 5, 1), 93)) == [
        (date(2024, 5, 1), date(2024, 5, 1))
    ]


def test_start_after_end_raises():
    with pytest.raises(ValueError):
        list(date_chunks(date(2024, 2, 1), date(2024, 1, 1), 93))


def test_invalid_max_days_raises():
    with pytest.raises(ValueError):
        list(date_chunks(date(2024, 1, 1), date(2024, 1, 2), 0))
