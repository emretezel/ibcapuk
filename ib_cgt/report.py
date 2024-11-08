"""
A module for reporting UK Tax Year Gain/Loss for a given set of trades.
Author: Emre Tezel
"""

from datetime import datetime

from ib_cgt.disposal import Disposal
from tabulate import tabulate


def report(year: int, disposals: list[Disposal]):
    """
    Report the UK Tax Year Gain/Loss for a given set of disposals.

    Args:
        year: This the year of the start of the tax year.
        disposals: The disposals to report.
    """
    # First filter all the disposals where the disposal date is on or after 6th of April of the year,
    # and before 6th of April of the next year
    start_date = datetime(year, 4, 6)
    end_date = datetime(year + 1, 4, 6)

    disposals = [
        disposal
        for disposal in disposals
        if start_date <= disposal.disposal_trade.trade_date < end_date
    ]

    number_disposals = len(disposals)
    disposal_proceeds = sum(disposal.disposal_proceeds for disposal in disposals)
    costs = sum(disposal.costs for disposal in disposals)
    gains = sum(disposal.gain for disposal in disposals)
    losses = sum(disposal.loss for disposal in disposals)
    total_gains_losses = gains + losses

    # Create a file named with the tax year + "TaxYearReport.txt"
    with open(f"{year}TaxYearReport.txt", "w") as f:
        # First create a line of 120 characters and print the start and end date of the tax year, including month and day
        # but no hour
        f.write("-" * 120 + "\n")
        f.write(
            f"Tax Year: {start_date.strftime('%d %B')} {start_date.year} - {end_date.strftime('%d %B')} "
            f"{end_date.year}\n"
        )
        f.write("-" * 120 + "\n")

        # Next print the str representation of the disposals
        for disposal in disposals:
            f.write(str(disposal) + "\n")

        # Finally print a table with the number of disposals, disposal proceeds, costs, gains, losses and
        # total gains/losses
        f.write("\n")
        f.write(
            # Align column values to the right
            tabulate(
                [
                    ["Number of Disposals", number_disposals],
                    ["Disposal Proceeds", f"{disposal_proceeds:,.2f}"],
                    ["Costs", f"{costs:,.2f}"],
                    ["Gains", f"{gains:,.2f}"],
                    ["Losses", f"{losses:,.2f}"],
                    ["Total Gains/Losses", f"{total_gains_losses:,.2f}"],
                ],
                tablefmt="plain",
                colalign=("left", "right"),
            )
        )
