"""Date helpers for splitting requests into ranges accepted by the NBP API."""

from __future__ import annotations

from collections.abc import Iterator
from datetime import date, timedelta


def date_chunks(start: date, end: date, max_days: int) -> Iterator[tuple[date, date]]:
    """Split the inclusive range [start, end] into consecutive chunks of at most ``max_days`` days.

    >>> list(date_chunks(date(2024, 1, 1), date(2024, 1, 5), 2))
    [(datetime.date(2024, 1, 1), datetime.date(2024, 1, 2)), \
(datetime.date(2024, 1, 3), datetime.date(2024, 1, 4)), \
(datetime.date(2024, 1, 5), datetime.date(2024, 1, 5))]
    """
    if max_days < 1:
        raise ValueError("max_days must be at least 1")
    if start > end:
        raise ValueError(f"start ({start}) must not be after end ({end})")

    chunk_start = start
    while chunk_start <= end:
        chunk_end = min(chunk_start + timedelta(days=max_days - 1), end)
        yield chunk_start, chunk_end
        chunk_start = chunk_end + timedelta(days=1)
