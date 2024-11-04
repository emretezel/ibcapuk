"""
Module for disposal of an instrument.
Author: Emre Tezel
"""

from ib_cgt.trade import Trade


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

    def __str__(self):
        """
        Return a string representation of the disposal.

        Returns:
            A string representation of the disposal.
        """
        # Return a string representation of the disposal trade as well as all the matching trades individually
        # Insert lines at the beginning and end of the string
        matching_trades_str = "\n".join(str(trade) for trade in self.matching_trades)
        return f"***\nDisposal Trade: {self.disposal_trade}\nMatching Trades:\n{matching_trades_str}\n***"
