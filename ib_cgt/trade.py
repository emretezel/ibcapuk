"""
Module for trade of an instrument.
Author: Emre Tezel
"""

import pandas as pd


class Trade:
    """
    Class to represent the trade of an instrument.
    """

    def __init__(
        self,
        trade_id: int,
        symbol: str,
        currency: str,
        trade_date: pd.Timestamp,
        quantity: int,
        notional_value: float,
        commission: float,
        notional_value_gbp: float,
        commission_gbp: float,
    ):
        """
        Initialize a trade object.

        Args:
            trade_id: The ID of the trade.
            symbol: The symbol of the instrument.
            currency: The currency of the instrument.
            trade_date: The date of the trade.
            quantity: The quantity of the instrument traded.
            notional_value: The notional value of the trade.
            commission: The commission paid for the trade.
            notional_value_gbp: The notional value of the trade in GBP.
            commission_gbp: The commission paid for the trade in GBP.
        """
        self.trade_id = trade_id
        self.symbol = symbol
        self.currency = currency
        self.trade_date = trade_date
        self.quantity = quantity
        self.notional_value = notional_value
        self.commission = commission
        self.notional_value_gbp = notional_value_gbp
        self.commission_gbp = commission_gbp

    def __add__(self, other):
        """
        Add two trades together.

        Args:
            other: The other trade to add.

        Returns:
            A new trade object with the sum of the notional values and commissions.
        """
        if self.symbol != other.symbol:
            raise ValueError("Cannot add trades with different symbols.")

        return Trade(
            trade_id=self.trade_id,
            symbol=self.symbol,
            currency=self.currency,
            trade_date=self.trade_date,
            quantity=self.quantity + other.quantity,
            notional_value=self.notional_value + other.notional_value,
            commission=self.commission + other.commission,
            notional_value_gbp=self.notional_value_gbp + other.notional_value_gbp,
            commission_gbp=self.commission_gbp + other.commission_gbp,
        )

    def __str__(self):
        return (
            f"Trade ID: {self.trade_id}, Symbol: {self.symbol}, Date: {self.trade_date}, Quantity: {self.quantity}, "
            f"Notional Value: {self.notional_value}, Commission: {self.commission}"
        )