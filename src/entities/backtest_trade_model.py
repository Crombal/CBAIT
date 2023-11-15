"""Module for backtest trade model."""
import numpy as np
import pandas as pd

from src.entities.base_trade_model import BaseTradeModel


class BacktestTradeModel(BaseTradeModel):
    """Backtest trade model.

    Attributes
    ----------
    historical_data: pd.DataFrame
        raw historical data of the instrument to be back-tested
    trade_commission: float
        trading commission per trade
    approximated_spread_and_slippage: float
        approximated spread and slippage per trade
    trading_days_per_year: float
        number of trading days per year

    Methods
    -------
    get_data:
        add the Returns column to the historical data and returns it.

    get_trade_costs:
        calculate the approximated total trade costs per trade and returns it.

    get_trades_per_year:
        calculate the number of trades per year and returns it.
    """

    historical_data: pd.DataFrame
    trade_commission: float = 0.001
    approximated_spread_and_slippage: float = 0.0001
    trading_days_per_year: float = 365.25

    def get_data(self: "BacktestTradeModel") -> pd.DataFrame:
        """Add the Returns column to the historical data.

        :return: prepared historical data of the instrument to be back-tested
        :rtype: pd.DataFrame
        """
        data = self.historical_data.loc[self.get_start_datetime() : self.end].copy()  # type: ignore[misc]
        data["Returns"] = np.log(data.Close / data.Close.shift(1))
        return data

    def get_trade_costs(self: "BacktestTradeModel") -> float:
        """Calculate the approximated total trade costs per trade.

        :return: approximated total trade costs per trade
        :rtype: float
        """
        return np.log(1 - self.trade_commission) + np.log(  # type: ignore[no-any-return]
            1 - self.approximated_spread_and_slippage,
        )

    def get_trades_per_year(self: "BacktestTradeModel", data: pd.DataFrame) -> float:
        """Calculate the number of trades per year.

        :param data: prepared historical data of the instrument to be back-tested
        :type data: pd.DataFrame

        :return: number of trades per year
        :rtype: float
        """
        return data.Close.count() / (  # type: ignore[no-any-return]
            (data.index[-1] - data.index[0]).days / self.trading_days_per_year
        )
