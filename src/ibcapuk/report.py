"""
A module for reporting UK Tax Year Gain/Loss for a given set of trades.
Author: Emre Tezel
"""

from datetime import datetime, timedelta
from fpdf import FPDF, XPos, YPos
from ibcapuk.disposal import Disposal
from tabulate import tabulate


def report(year: int, disposals: list[Disposal], file_name: str = None):
    """
    Report the UK Tax Year Gain/Loss for a given set of disposals.

    Args:
        year: This the year of the start of the tax year.
        disposals: The disposals to report.
        file_name: The name of the file to write the report to.
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
    costs = -sum(disposal.costs for disposal in disposals)
    gains = sum(disposal.gain for disposal in disposals)
    losses = -sum(disposal.loss for disposal in disposals)
    total_gains_losses = gains - losses

    if file_name is None:
        file_name = f"{year}TaxYearReport.pdf"

    pdf = FPDF(orientation="landscape", format="A4")
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Courier", size=10)

    # First create a line of 120 characters and print the start and end date of the tax year, including month and day
    # but no hour
    pdf.cell(text="-" * 130, new_x=XPos.LEFT, new_y=YPos.NEXT)

    # Subtract one day from the end date
    end_date -= timedelta(days=1)

    pdf.cell(
        text=f"Tax Year: {start_date.strftime('%d %B')} {start_date.year} - {end_date.strftime('%d %B')} "
        f"{end_date.year}",
        new_x=XPos.LEFT,
        new_y=YPos.NEXT,
    )

    table_str = tabulate(
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

    for line in table_str.split("\n"):
        pdf.cell(text=line, new_x=XPos.LEFT, new_y=YPos.NEXT)

    pdf.cell(text="-" * 130, new_x=XPos.LEFT, new_y=YPos.NEXT)

    # Next print the str representation of the disposals
    for disposal in disposals:
        for line in str(disposal).split("\n"):
            pdf.cell(text=line, new_x=XPos.LEFT, new_y=YPos.NEXT)

    pdf.output(file_name)
