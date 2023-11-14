"""Module for backtest trade model."""

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
    """

    historical_data: pd.DataFrame
    trade_commission: float = 0.001
    approximated_spread_and_slippage: float = 0.0001
    trading_days_per_year: float = 365.25
