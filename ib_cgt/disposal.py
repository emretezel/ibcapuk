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
    def costs(self) -> float:
        """
        Calculate the costs. Add the fees in GBP for all the matching trades and the disposal trade.

        Returns:
            The costs.
        """
        return (
            sum(
                trade.notional_value_gbp + trade.commission_gbp
                for trade in self.matching_trades
            )
            + self.disposal_trade.commission_gbp
        )

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
        gain_loss_info = (
            f"Resulting gain/loss: {self.gain if self.gain > 0 else self.loss:,.2f} GBP"
        )

        # Combine everything into the final output
        return (
            f"{line}\nDisposing Trade:\n{disposal_trade_info}\n\nMatching Trades:\n{matching_trades_info}\n\n"
            f"{gain_loss_info}\n{line}"
        )
