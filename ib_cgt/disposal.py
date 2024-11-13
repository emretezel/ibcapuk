"""
Module for disposal of an instrument.
Author: Emre Tezel
"""

from ib_cgt.trade import Trade
from tabulate import tabulate


class Disposal:
    """
    Class to represent the disposal of an instrument.
    """

    def __init__(self, disposal_trade: Trade, matching_trades: list[Trade]):
        """
        Initialize a disposal object.

        Args:
            disposal_trade: The trade representing the disposal.
            matching_trades: The trades that match the disposal.
        """
        self.disposal_trade = disposal_trade
        self.matching_trades = matching_trades

    @property
    def disposal_proceeds(self) -> float:
        """
        Calculate the disposal proceeds.

        Returns:
            The disposal proceeds.
        """
        return self.disposal_trade.notional_value_gbp

    @property
    def trade_type(self) -> str:
        """
        Get the trade type of the disposal trade.

        Returns:
            The trade type.
        """
        return self.disposal_trade.trade_type

    @property
    def costs(self) -> float:
        """
        Calculate the costs. For Futures use the same fx rate as the disposal trade, otherwise use the fx rate of the
        matching trade.

        Returns:
            The costs.
        """
        fx = (
            self.disposal_trade.fx
            if self.trade_type == "Futures"
            else self.matching_trades[0].fx
        )

        # First sum the notional values of the matching trades
        notional_values_gbp = sum(
            trade.notional_value for trade in self.matching_trades
        ) * (1 / fx)

        if self.trade_type == "Forex":
            fees_gbp = sum(trade.commission_gbp for trade in self.matching_trades)
        else:
            fees_gbp = sum(trade.commission for trade in self.matching_trades) * (
                1 / fx
            )

        fees_gbp += self.disposal_trade.commission_gbp
        return notional_values_gbp + fees_gbp

    @property
    def gain(self) -> float:
        """
        Calculate the gain.

        Returns:
            The gain.
        """
        return max(0.0, self.disposal_proceeds + self.costs)

    @property
    def loss(self) -> float:
        """
        Calculate the loss.

        Returns:
            The loss.
        """
        return min(0.0, self.disposal_proceeds + self.costs)

    def __str__(self):
        line = "-" * 120

        # Prepare data for disposal trade table
        disposal_trade_table = [
            [
                self.disposal_trade.trade_id,
                self.disposal_trade.trade_date,
                self.disposal_trade.quantity,
                self.disposal_trade.symbol,
                self.disposal_trade.currency,
                f"{self.disposal_trade.notional_value:,.2f}",
                f"{self.disposal_trade.notional_value_gbp:,.2f}",
                f"{self.disposal_trade.commission_gbp:,.2f}",
                f"{self.disposal_trade.fx:,.2f}",
            ]
        ]

        # Header for the disposal trade table
        headers = [
            "ID",
            "Date",
            "Qty",
            "Symbol",
            "Currency",
            "Proceeds",
            "GBP Proceeds",
            "Fees in GBP",
            "FX",
        ]

        # Format disposal trade table using tabulate
        disposal_trade_info = tabulate(
            disposal_trade_table, headers=headers, tablefmt="grid"
        )

        # Prepare data for matching trades table
        matching_trades_table = [
            [
                trade.trade_id,
                trade.trade_date,
                trade.quantity,
                trade.symbol,
                trade.currency,
                f"{trade.notional_value:,.2f}",
                f"{trade.notional_value_gbp:,.2f}",
                f"{trade.commission_gbp:,.2f}",
                f"{trade.fx:,.2f}",
            ]
            for trade in self.matching_trades
        ]

        # Format matching trades using tabulate
        matching_trades_info = tabulate(
            matching_trades_table, headers=headers, tablefmt="grid"
        )

        # Gain/loss info
        # If the trade type is Futures say at the end using FX at disposal date otherwise say
        # using FX rates of each trade date.
        gain_loss_info = f"Resulting in a gain/loss of {self.gain if self.gain > 0 else self.loss:,.2f} GBP, using "

        gain_loss_info += (
            f"the FX rate on the disposal date."
            if self.trade_type == "Futures"
            else f"corresponding FX rates on each trade date."
        )

        # Combine everything into the final output
        return (
            f"{line}\nDisposing {self.disposal_trade.trade_type} Trade:\n{disposal_trade_info}\n\nMatching Trades:\n{matching_trades_info}\n\n"
            f"{gain_loss_info}\n{line}"
        )
