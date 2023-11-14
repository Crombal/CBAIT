"""Module for base trade model."""
from datetime import UTC, datetime

from binance import Client
from binance.enums import HistoricalKlinesType
from pydantic import BaseModel, ConfigDict

from src.utils.earliest_valid_timestamp_loader import get_earliest_valid_timestamp


class BaseTradeModel(BaseModel):
    """Base trade model.

    Attributes
    ----------
    client: Client
        Binance API client
    symbol: str
        symbol of the instrument
    interval: str
        interval of the instrument
    start: str | None
        start point in historical data
    end: str | None
        end point in historical data
    limit: int
        Default 1000; max 1000.
    klines_type: HistoricalKlinesType
        Type of klines data to retrieve.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    client: Client = None
    symbol: str = "BTCUSDT"
    interval: str = Client.KLINE_INTERVAL_1HOUR
    start: str | None = None
    end: str | None = None
    limit: int = 1000
    klines_type: HistoricalKlinesType = HistoricalKlinesType.SPOT

    def get_start_datetime(self: "BaseTradeModel") -> str:
        """Get start datetime.

        :return: start datetime
        :rtype: str
        """
        return (
            get_earliest_valid_timestamp(
                self.client,
                self.symbol,
                self.interval,
                self.klines_type,
            )
            if self.start is None
            else (datetime.strptime(self.start, "%Y-%m-%d %H:%M:%S").replace(tzinfo=UTC).strftime("%Y-%m-%dT%H:%M:%SZ"))
        )
