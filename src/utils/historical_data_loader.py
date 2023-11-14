"""Module to load historical data via Binance API."""
import logging
from functools import lru_cache
from pathlib import Path

import pandas as pd
from binance.client import Client

from src.entities.base_trade_model import BaseTradeModel
from src.utils.logger import get_logger

logger: logging.Logger = get_logger()


class HistoricalDataLoader:
    """Class to load historical data via Binance API."""

    client: Client

    def __init__(self: "HistoricalDataLoader", client: Client) -> None:
        """HistoricalDataLoader constructor.

        :param client: Binance API client
        :type client: Client
        """
        self.client: Client = client

    def export_historical_data_to_csv(
        self: "HistoricalDataLoader",
        base_trade_model: BaseTradeModel,
    ) -> None:
        """Export historical data to csv file.

        :param base_trade_model: base trade model
        :type base_trade_model: BaseTradeModel
        """
        filename: Path = self._get_csv_filename(base_trade_model)
        data_dir_path: Path = self._get_data_dir_path(base_trade_model)

        self._create_data_dir(data_dir_path)

        historical_data: pd.DataFrame = self._load_historical_data(base_trade_model)
        historical_data.to_csv(f"{data_dir_path}/{filename}")

        logger.info("Exported historical data to %s/%s", data_dir_path, filename)

    def get_historical_data_from_csv(
        self: "HistoricalDataLoader",
        base_trade_model: BaseTradeModel,
    ) -> pd.DataFrame:
        """Get historical data from csv file.

        :param base_trade_model: base trade model
        :type base_trade_model: BaseTradeModel

        :return: pd.DataFrame of values DOHLCV (Date, Open, High, Low, Close, Volume)
        :rtype: pd.DataFrame
        """
        filename = self._get_csv_filename(base_trade_model)
        data_dir_path = self._get_data_dir_path(base_trade_model)

        historical_data = pd.read_csv(f"{data_dir_path}/{filename}")
        historical_data["Date"] = pd.to_datetime(historical_data["Date"])

        return historical_data.set_index("Date")

    def get_historical_data_from_api(
        self: "HistoricalDataLoader",
        base_trade_model: BaseTradeModel,
    ) -> pd.DataFrame:
        """Get historical data from Binance as Pandas DataFrame.

        :param base_trade_model: base trade model
        :type base_trade_model: BaseTradeModel

        :return: pd.DataFrame of values DOHLCV (Date, Open, High, Low, Close, Volume)
        :rtype: pd.DataFrame
        """
        return self._load_historical_data(base_trade_model)

    def _load_historical_data(
        self: "HistoricalDataLoader",
        base_trade_model: BaseTradeModel,
    ) -> pd.DataFrame:
        """Load Historical Klines from Binance (spot or futures) to Pandas DataFrame.

        See dateparser docs for valid start and end string formats https://dateparser.readthedocs.io/en/latest/

        If using offset strings for dates add "UTC" to date string e.g. "now UTC", "11 hours ago UTC"

        :param base_trade_model: base trade model
        :type base_trade_model: BaseTradeModel

        :return: pd.DataFrame of values DOHLCV (Date, Open, High, Low, Close, Volume)
        :rtype: pd.DataFrame
        """
        historical_klines: list[dict[str, str]] = self.client.get_historical_klines(
            symbol=base_trade_model.symbol,
            interval=base_trade_model.interval,
            start_str=base_trade_model.get_start_datetime(),
            end_str=base_trade_model.end,
            limit=base_trade_model.limit,
            klines_type=base_trade_model.klines_type,
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

    @staticmethod
    @lru_cache
    def _get_csv_filename(base_trade_model: BaseTradeModel) -> Path:
        """Generate csv file name.

        :param base_trade_model: base trade model
        :type base_trade_model: BaseTradeModel

        :return: csv file name
        :rtype: Path
        """
        return Path(f"{base_trade_model.get_start_datetime()}_{base_trade_model.end}.csv")

    @staticmethod
    @lru_cache
    def _get_data_dir_path(base_trade_model: BaseTradeModel) -> Path:
        """Generate data directory path.

        :param base_trade_model: base trade model
        :type base_trade_model: BaseTradeModel

        :return: data directory path
        :rtype: str
        """
        return Path(
            f"data/"
            f"{base_trade_model.klines_type.name}/"
            f"{base_trade_model.symbol}/"
            f"{base_trade_model.interval}",
        )

    @staticmethod
    def _create_data_dir(data_dir_path: Path) -> None:
        """Create data directory if not exists.

        :param data_dir_path: path where data directory will be created
        :type data_dir_path: Path
        """
        Path(data_dir_path).mkdir(parents=True, exist_ok=True)
