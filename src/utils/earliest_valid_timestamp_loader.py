"""Script for loading the earliest valid timestamp from a exchange."""

from datetime import UTC, datetime
from functools import lru_cache

from binance.client import Client
from binance.enums import HistoricalKlinesType


@lru_cache
def get_earliest_valid_timestamp(client: Client, symbol: str, interval: str, klines_type: HistoricalKlinesType) -> str:
    """Get the earliest valid timestamp from a exchange.

    :return: earliest valid timestamp
    :rtype: int
    """
    return datetime.fromtimestamp(
        client._get_earliest_valid_timestamp(symbol, interval, klines_type) / 1000,  # noqa: SLF001
        tz=UTC,
    ).strftime("%Y-%m-%dT%H:%M:%SZ")
