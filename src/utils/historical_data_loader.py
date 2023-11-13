"""Module to load historical data via Binance API."""
import logging
from datetime import UTC, datetime
from functools import lru_cache
from pathlib import Path
from typing import NamedTuple

import pandas as pd
from binance.client import Client, HistoricalKlinesType

from src.utils.logger import get_logger

logger: logging.Logger = get_logger()


class HistoricalDataLoaderConfig(NamedTuple):
    """HistoricalDataLoader config."""

    symbol: str = "BTCUSDT"
    interval: str = Client.KLINE_INTERVAL_1HOUR
    start: str | None = None
    end: str | None = None
    limit: int = 1000
    klines_type: HistoricalKlinesType = HistoricalKlinesType.SPOT


class HistoricalDataLoader:
    """Class to load historical data via Binance API."""

    client: Client = None

    def __init__(self: "HistoricalDataLoader", client: Client) -> None:
        """HistoricalDataLoader constructor.

        :param client: Binance API client
        :type client: Client
        """
        self.client: Client = client

    def export_historical_data_to_csv(
        self: "HistoricalDataLoader",
        historical_data_loader_config: HistoricalDataLoaderConfig,
    ) -> None:
        """Export historical data to csv file.

        :param historical_data_loader_config: config for loading historical data
        :type historical_data_loader_config: HistoricalDataLoaderConfig
        """
        filename: Path = self._get_csv_filename(historical_data_loader_config)
        data_dir_path: Path = self._get_data_dir_path(historical_data_loader_config)

        self._create_data_dir(data_dir_path)

        historical_data: pd.DataFrame = self._load_historical_data(historical_data_loader_config)
        historical_data.to_csv(f"{data_dir_path}/{filename}")

        logger.info("Exported historical data to %s/%s", data_dir_path, filename)

    def get_historical_data_from_csv(
        self: "HistoricalDataLoader",
        historical_data_loader_config: HistoricalDataLoaderConfig,
    ) -> pd.DataFrame:
        """Get historical data from csv file.

        :param historical_data_loader_config: config for loading historical data
        :type historical_data_loader_config: HistoricalDataLoaderConfig

        :return: pd.DataFrame of values DOHLCV (Date, Open, High, Low, Close, Volume)
        :rtype: pd.DataFrame
        """
        filename = self._get_csv_filename(historical_data_loader_config)
        data_dir_path = self._get_data_dir_path(historical_data_loader_config)

        historical_data = pd.read_csv(f"{data_dir_path}/{filename}")
        historical_data["Date"] = pd.to_datetime(historical_data["Date"])

        return historical_data.set_index("Date")

    def get_historical_data_from_api(
        self: "HistoricalDataLoader",
        historical_data_loader_config: HistoricalDataLoaderConfig,
    ) -> pd.DataFrame:
        """Get historical data from Binance as Pandas DataFrame.

        :param historical_data_loader_config: config for loading historical data
        :type historical_data_loader_config: HistoricalDataLoaderConfig

        :return: pd.DataFrame of values DOHLCV (Date, Open, High, Low, Close, Volume)
        :rtype: pd.DataFrame
        """
        return self._load_historical_data(historical_data_loader_config)

    def _load_historical_data(
        self: "HistoricalDataLoader",
        historical_data_loader_config: HistoricalDataLoaderConfig,
    ) -> pd.DataFrame:
        """Load Historical Klines from Binance (spot or futures) to Pandas DataFrame.

        See dateparser docs for valid start and end string formats https://dateparser.readthedocs.io/en/latest/

        If using offset strings for dates add "UTC" to date string e.g. "now UTC", "11 hours ago UTC"

        :param historical_data_loader_config: config for loading historical data
        :type historical_data_loader_config: HistoricalDataLoaderConfig

        :return: pd.DataFrame of values DOHLCV (Date, Open, High, Low, Close, Volume)
        :rtype: pd.DataFrame
        """
        historical_klines: list[dict[str, str]] = self.client.get_historical_klines(
            symbol=historical_data_loader_config.symbol,
            interval=historical_data_loader_config.interval,
            start_str=historical_data_loader_config.start,
            end_str=historical_data_loader_config.end,
            limit=historical_data_loader_config.limit,
            klines_type=historical_data_loader_config.klines_type,
        )

        columns_names: list[str] = [
            "Open Time",
            "Open",
            "High",
            "Low",
            "Close",
            "Volume",
            "Close Time",
            "Quote Asset Volume",
            "Number of Trades",
            "Taker buy base asset volume",
            "Taker buy quote asset volume",
            "Ignore",
        ]

        raw_historical_data: pd.DataFrame = pd.DataFrame(historical_klines, columns=columns_names)
        raw_historical_data["Date"] = pd.to_datetime(raw_historical_data.iloc[:, 0], unit="ms")

        historical_data = raw_historical_data[["Date", "Open", "High", "Low", "Close", "Volume"]].copy()
        historical_data = historical_data.set_index("Date")

        for column in historical_data.columns:
            historical_data[column] = pd.to_numeric(historical_data[column], errors="coerce")

        return historical_data

    def _get_csv_filename(
        self: "HistoricalDataLoader",
        historical_data_loader_config: HistoricalDataLoaderConfig,
    ) -> Path:
        """Generate csv file name.

        :param historical_data_loader_config: config for loading historical data
        :type historical_data_loader_config: HistoricalDataLoaderConfig

        :return: csv file name
        :rtype: Path
        """
        start_datetime = (
            (
                datetime.fromtimestamp(
                    self.client._get_earliest_valid_timestamp(  # noqa: SLF001
                        historical_data_loader_config.symbol,
                        historical_data_loader_config.interval,
                        historical_data_loader_config.klines_type,
                    )
                    / 1000,
                    tz=UTC,
                ).strftime("%Y-%m-%dT%H:%M:%SZ")
            )
            if historical_data_loader_config.start is None
            else (
                datetime.strptime(historical_data_loader_config.start, "%Y-%m-%d %H:%M:%S")
                .replace(tzinfo=UTC)
                .strftime("%Y-%m-%dT%H:%M:%SZ")
            )
        )

        end_datetime = "latest" if historical_data_loader_config.end is None else historical_data_loader_config.end

        return Path(f"{start_datetime}_{end_datetime}.csv")

    @staticmethod
    @lru_cache
    def _get_data_dir_path(historical_data_loader_config: HistoricalDataLoaderConfig) -> Path:
        """Generate data directory path.

        :param historical_data_loader_config: config for loading historical data
        :type historical_data_loader_config: HistoricalDataLoaderConfig

        :return: data directory path
        :rtype: str
        """
        return Path(
            f"data/"
            f"{historical_data_loader_config.klines_type.name}/"
            f"{historical_data_loader_config.symbol}/"
            f"{historical_data_loader_config.interval}",
        )

    @staticmethod
    def _create_data_dir(data_dir_path: Path) -> None:
        """Create data directory if not exists.

        :param data_dir_path: path where data directory will be created
        :type data_dir_path: Path
        """
        Path(data_dir_path).mkdir(parents=True, exist_ok=True)
