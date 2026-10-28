import re
from datetime import date

import pytest
import responses

from nbp_lakehouse.ingest.nbp_client import NbpApiError, NbpClient

BASE = "https://api.nbp.pl/api"

SAMPLE_TABLE = {
    "table": "A",
    "no": "001/A/NBP/2024",
    "effectiveDate": "2024-01-02",
    "rates": [{"currency": "euro", "code": "EUR", "mid": 4.3434}],
}
SAMPLE_GOLD = {"data": "2024-01-02", "cena": 262.94}


@pytest.fixture
def client():
    return NbpClient(retries=0)


@responses.activate
def test_returns_exchange_rate_tables(client):
    responses.get(f"{BASE}/exchangerates/tables/A/2024-01-01/2024-01-31/", json=[SAMPLE_TABLE])

    result = client.get_exchange_rate_tables("a", date(2024, 1, 1), date(2024, 1, 31))

    assert result == [SAMPLE_TABLE]
    assert responses.calls[0].request.params == {"format": "json"}


@responses.activate
def test_long_range_is_split_into_multiple_requests(client):
    # 2024 has 366 days -> 4 chunks of max 93 days
    responses.get(re.compile(rf"{BASE}/exchangerates/tables/A/.*"), json=[SAMPLE_TABLE])

    result = client.get_exchange_rate_tables("A", date(2024, 1, 1), date(2024, 12, 31))

    assert len(responses.calls) == 4
    assert len(result) == 4


@responses.activate
def test_404_means_no_data(client):
    responses.get(
        f"{BASE}/exchangerates/tables/A/2024-01-06/2024-01-07/",
        status=404,
        body="404 NotFound - Not Found - Brak danych",
    )

    assert client.get_exchange_rate_tables("A", date(2024, 1, 6), date(2024, 1, 7)) == []


@responses.activate
def test_server_error_raises(client):
    responses.get(f"{BASE}/cenyzlota/2024-01-01/2024-01-31/", status=500, body="error")

    with pytest.raises(NbpApiError):
        client.get_gold_prices(date(2024, 1, 1), date(2024, 1, 31))


@responses.activate
def test_returns_gold_prices(client):
    responses.get(f"{BASE}/cenyzlota/2024-01-01/2024-01-31/", json=[SAMPLE_GOLD])

    assert client.get_gold_prices(date(2024, 1, 1), date(2024, 1, 31)) == [SAMPLE_GOLD]


def test_unknown_table_raises(client):
    with pytest.raises(ValueError):
        client.get_exchange_rate_tables("X", date(2024, 1, 1), date(2024, 1, 31))
