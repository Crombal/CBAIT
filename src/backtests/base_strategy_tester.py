"""Base class that prepare all requirements for other strategy tester classes."""

import logging
import warnings
from abc import abstractmethod
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from binance.client import Client
from pandas import Series

from src.entities.backtest_trade_model import BacktestTradeModel
from src.utils.logger import get_logger

warnings.filterwarnings("ignore")
plt.style.use("seaborn-v0_8")
pd.set_option("display.max_columns", 10)

logger: logging.Logger = get_logger()


class BaseStrategyTester:
    """Base class that prepare all requirements for other strategy tester classes.

    Attributes
    ----------
    client: Client
        binance client object
    model: BacktestTradeModel
        backtest trade model object
    trades_per_year: float
        number of trades per year


    Methods
    -------
    get_multiple:
        calculate the multiple of the strategy.

    get_cagr:
        calculate the CAGR of the strategy.

    get_annualized_mean:
        calculate the annualized mean of the strategy.

    get_annualized_std:
        calculate the annualized standard deviation of the strategy.

    get_sharpe:
        calculate the Sharpe Ratio of the strategy.

    get_prepared_data:
        abstract method to prepare the data for back-testing.

    get_backtest_results:
        abstract method to get the results of the back-testing.

    get_optimized_backtest_results:
        abstract method to get the results of the back-testing optimized for different parameter values.

    get_best_strategy:
        abstract method to get the best strategy calculated by the back-testing.

    plot_results:
        plots the cumulative performance of the trading strategy compared to buy-and-hold.

    show_performance:
        prints strategy performance.
    """

    client: Client
    model: BacktestTradeModel
    data: pd.DataFrame
    trades_per_year: float

    def __init__(
        self: "BaseStrategyTester",
        client: Client,
        backtest_trade_model: BacktestTradeModel,
    ) -> None:
        """Initialize the BaseStrategyTester class.

        :param client: binance client object
        :type client: Client

        :param backtest_trade_model: backtest trade model object
        :type backtest_trade_model: BacktestTradeModel
        """
        self.client = client
        self.model = backtest_trade_model
        self.data = backtest_trade_model.get_data()
        self.trades_per_year = backtest_trade_model.get_trades_per_year(self.data)

    @staticmethod
    def get_multiple(data: pd.DataFrame) -> float:
        """Calculate the multiple of the strategy.

        :param data: data to calculate the multiple
        :type data: pd.DataFrame

        :return: multiple of the strategy
        :rtype: float
        """
        return np.exp(data.sum())  # type: ignore[no-any-return]

    def get_cagr(self: "BaseStrategyTester", data: pd.DataFrame) -> float:
        """Calculate the CAGR of the strategy.

        :param data: data to calculate the CAGR
        :type data: pd.DataFrame

        :return: CAGR of the strategy
        :rtype: float
        """
        return (  # type: ignore[no-any-return]
            self.get_multiple(data) ** (1 / ((data.index[-1] - data.index[0]).days / self.model.trading_days_per_year))
            - 1
        )

    def get_annualized_mean(self: "BaseStrategyTester", data: pd.DataFrame) -> Series[Any]:
        """Calculate the annualized mean of the strategy.

        :param data: data to calculate the annualized mean
        :type data: pd.DataFrame

        :return: annualized mean of the strategy
        :rtype: Series
        """
        return data.mean() * self.trades_per_year

    def get_annualized_std(self: "BaseStrategyTester", data: pd.DataFrame) -> float:
        """Calculate the annualized standard deviation of the strategy.

        :param data: data to calculate the annualized standard deviation
        :type data: pd.DataFrame

        :return: annualized standard deviation of the strategy
        :rtype: float
        """
        return data.std() * np.sqrt(self.trades_per_year)  # type: ignore[no-any-return]

    def get_sharpe(self: "BaseStrategyTester", data: pd.DataFrame) -> object:
        """Calculate the Sharpe Ratio of the strategy.

        :param data: data to calculate the Sharpe Ratio
        :type data: pd.DataFrame

        :return: Sharpe Ratio
        :rtype: float
        """
        return np.nan if data.std() == 0 else self.get_annualized_mean(data) / self.get_annualized_std(data)

    @abstractmethod
    def get_prepared_data(self: "BaseStrategyTester") -> pd.DataFrame:
        """Prepare the data for back-testing.

        :return: prepared data for back-testing
        :rtype: pd.DataFrame
        """
        raise NotImplementedError

    @abstractmethod
    def get_backtest_results(self: "BaseStrategyTester") -> pd.DataFrame:
        """Get the results of the back-testing.

        :return: results of the back-testing
        :rtype: pd.DataFrame
        """
        raise NotImplementedError

    @abstractmethod
    def get_optimized_backtest_results(self: "BaseStrategyTester") -> pd.DataFrame:
        """Get the results of the back-testing optimized for different parameter values.

        :return: results of the back-testing optimized for different parameter values
        :rtype: pd.DataFrame
        """
        raise NotImplementedError

    @abstractmethod
    def get_best_strategy(self: "BaseStrategyTester") -> pd.DataFrame:
        """Get the best strategy calculated by the back-testing.

        :return: best strategy calculated by the back-testing
        :rtype: pd.DataFrame
        """
        raise NotImplementedError

    def plot_results(self: "BaseStrategyTester", data: pd.DataFrame) -> None:
        """Plot the cumulative performance of the trading strategy compared to buy-and-hold.

        :param data: data to plot
        :type data: pd.DataFrame
        """
        title = f"{self.model.symbol} | trade_costs = {self.model.get_trade_costs()}"
        columns = ["Cumulative Returns Buy&Hold", "Cumulative Returns Strategy"]
        data[columns].plot(title=title, figsize=(12, 8))

    def show_performance(self: "BaseStrategyTester", data: pd.DataFrame) -> None:
        """Print strategy performance.

        :param data: data to print
        :type data: pd.DataFrame
        """
        data = data.copy()
        strategy_multiple = round(self.get_multiple(data.strategy), 6)
        bh_multiple = round(self.get_multiple(data.returns), 6)
        outperform = round(strategy_multiple - bh_multiple, 6)
        cagr = round(self.get_cagr(data.strategy), 6)
        annualized_mean = round(self.get_annualized_mean(data.strategy), 6)
        annualized_std = round(self.get_annualized_std(data.strategy), 6)
        sharpe = round(self.get_sharpe(data.strategy), 6)  # type: ignore[call-overload]

        logger.info(
            "SIMPLE PRICE & VOLUME STRATEGY | INSTRUMENT = %s | THRESHOLDS = %s, %s\n"
            "PERFORMANCE MEASURES:\n"
            "Multiple (Strategy): %s\n"
            "Multiple (Buy-and-Hold): %s\n"
            "Out-/Underperformed: %s\n"
            "CAGR: %s\n"
            "Annualized Mean: %s\n"
            "Annualized Std: %s\n"
            "Sharpe Ratio: %s",
            self.model.symbol,
            np.round(self.model.return_thresh, 5),  # type: ignore[attr-defined]
            np.round(self.model.volume_thresh, 5),  # type: ignore[attr-defined]
            strategy_multiple,
            bh_multiple,
            outperform,
            cagr,
            annualized_mean,
            annualized_std,
            sharpe,
        )
