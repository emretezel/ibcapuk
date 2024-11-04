"""
A modules that calculates the gain and loss of disposed instruments.
Author: Emre Tezel
"""

import pandas as pd
from ib_cgt.trade import Trade
import numpy as np
from ib_cgt.disposal import Disposal


def calculate_gain_and_loss(
    trades_file: str, instrument_type: str, output_file: str = "gain_and_loss.txt"
):
    """
    Calculate the gain and loss of disposed instruments.

    Args:
        trades_file: The CSV file containing the trades.
        instrument_type: The type of instrument to calculate the gain and loss for.
        output_file: The CSV file to write the gain and loss to.
    """
    # Raise exception if instrument type is not Futures
    if instrument_type != "Futures":
        raise ValueError("Only Futures are supported at the moment.")

    # Read the trades from the CSV file into a DataFrame. Parse the dates as dates.
    all_trades = pd.read_csv(trades_file, parse_dates=["Date/Time"])

    # Filter the trades by the instrument type
    all_trades = all_trades[all_trades["Instrument Type"] == instrument_type]

    # Sort the data frame by symbol and date in ascending order
    all_trades = all_trades.sort_values(by=["Symbol", "Date/Time"])

    # Make a deep copy of the all trades index.
    all_trade_ids = all_trades.index.copy()
    disposals = []

    # Start iterating over the trades
    for trade_id in all_trade_ids:
        trade = all_trades.loc[trade_id]

        if trade["Quantity"] == 0:
            # This trade has already been fully matched with another disposal trade
            continue

        disposal_trades = []
        matching_trades = []

        # First check whether there is another trade with the same symbol on the same date but with the opposite
        # trade action. Ignore the time part of the date.
        same_day_matching_trades = filter_same_day_trades(all_trades, trade)

        # If there are any matching trades, then try to match any/all of them with the disposal trade
        if len(same_day_matching_trades) > 0:
            for matching_trade_id in same_day_matching_trades.index:
                disposal_trade, matching_trade = process_matching_trade(
                    trade_id, matching_trade_id, all_trades
                )

                disposal_trades.append(disposal_trade)
                matching_trades.append(matching_trade)

                if all_trades.at[trade_id, "Quantity"] == 0:
                    break

        # If we have fully matched the disposal trade, then continue to the next trade
        if all_trades.at[trade_id, "Quantity"] == 0:
            disposal = create_disposal(disposal_trades, matching_trades)
            disposals.append(disposal)
            continue

        # Next check to see whether in the next 30 days there are trades that can be matched with the disposal trade.
        # This is the bed and breakfast rule.
        next_30_days_matching_trades = filter_bed_and_breakfast_trades(
            all_trades, trade
        )

        if len(next_30_days_matching_trades) > 0:
            for matching_trade_id in next_30_days_matching_trades.index:
                disposal_trade, matching_trade = process_matching_trade(
                    trade_id, matching_trade_id, all_trades
                )

                disposal_trades.append(disposal_trade)
                matching_trades.append(matching_trade)

                if all_trades.at[trade_id, "Quantity"] == 0:
                    break

        # If we have fully matched the disposal trade, then continue to the next trade
        if all_trades.at[trade_id, "Quantity"] == 0:
            disposal = create_disposal(disposal_trades, matching_trades)
            disposals.append(disposal)
            continue

        # Now we need to get the list of all the matching trades occurred in the past.
        section_104_trades = filter_section_104_trades(all_trades, trade)

        if len(section_104_trades) > 0:
            # Sum the quantity, notional value, commission, notional value GBP and commission GBP of the matching trades
            collapse_section_104_trades(all_trades, section_104_trades)

            disposal_trade, matching_trade = process_matching_trade(
                trade_id, section_104_trades.index[0], all_trades
            )

            disposal_trades.append(disposal_trade)
            matching_trades.append(matching_trade)

        # If disposal trades list is not empty, aggregate the disposal trades.
        if disposal_trades:
            disposal = create_disposal(disposal_trades, matching_trades)
            disposals.append(disposal)

    # Write all disposals to a CSV file
    with open(output_file, "w") as f:
        for disposal in disposals:
            f.write(str(disposal) + "\n")


def create_disposal(disposal_trades, matching_trades):
    trade = disposal_trades[0]
    for trade in disposal_trades[1:]:
        trade += trade
    # Create a disposal trade object with the matching trades
    disposal = Disposal(trade, matching_trades)
    return disposal


def collapse_section_104_trades(all_trades, section_104_trades):
    total_quantity = section_104_trades["Quantity"].sum()
    total_notional_value = section_104_trades["Notional Value"].sum()
    total_commission = section_104_trades["Comm/Fee"].sum()
    total_notional_value_gbp = section_104_trades["Notional Value GBP"].sum()
    total_commission_gbp = section_104_trades["Comm in GBP"].sum()

    # Delete all but the first matching trade from the all trade dataframe
    for matching_trade_id in section_104_trades.index[1:]:
        all_trades.drop(matching_trade_id, inplace=True)

    # For the first matching trade, update the quantity, notional value, commission, notional value GBP and
    # commission GBP to the total values
    all_trades.at[section_104_trades.index[0], "Quantity"] = total_quantity
    all_trades.at[section_104_trades.index[0], "Notional Value"] = total_notional_value
    all_trades.at[section_104_trades.index[0], "Comm/Fee"] = total_commission

    all_trades.at[section_104_trades.index[0], "Notional Value GBP"] = (
        total_notional_value_gbp
    )

    all_trades.at[section_104_trades.index[0], "Comm in GBP"] = total_commission_gbp

    # Update the fx rate by dividing the total notional value to the total notional value GBP
    all_trades.at[section_104_trades.index[0], "FX Rate"] = (
        total_notional_value_gbp / total_notional_value
    )


def filter_section_104_trades(all_trades, disposal_trade):
    section_104_matching_trades = all_trades[
        (all_trades["Symbol"] == disposal_trade["Symbol"])
        & (
            all_trades["Date/Time"].dt.normalize()
            < disposal_trade["Date/Time"].normalize()
        )
        & (np.sign(all_trades["Quantity"]) != np.sign(disposal_trade["Quantity"]))
        & (all_trades["Quantity"] != 0)
    ]

    return section_104_matching_trades


def filter_bed_and_breakfast_trades(all_trades, disposal_trade):
    next_30_days_matching_trades = all_trades[
        (all_trades["Symbol"] == disposal_trade["Symbol"])
        & (
            all_trades["Date/Time"].dt.normalize()
            > disposal_trade["Date/Time"].normalize()
        )
        & (
            all_trades["Date/Time"].dt.normalize()
            <= disposal_trade["Date/Time"].normalize() + pd.Timedelta(days=30)
        )
        & (np.sign(all_trades["Quantity"]) != np.sign(disposal_trade["Quantity"]))
        & (all_trades["Quantity"] != 0)
    ]

    return next_30_days_matching_trades


def filter_same_day_trades(all_trades, disposal_trade):
    same_day_matching_trades = all_trades[
        (all_trades["Symbol"] == disposal_trade["Symbol"])
        & (
            all_trades["Date/Time"].dt.normalize()
            == disposal_trade["Date/Time"].normalize()
        )
        & (np.sign(all_trades["Quantity"]) != np.sign(disposal_trade["Quantity"]))
        & (all_trades["Quantity"] != 0)
    ]

    return same_day_matching_trades


def process_matching_trade(
    disposal_trade_id: int, matching_trade_id: int, all_trades: pd.DataFrame
) -> (Trade, Trade):
    """
    Process a matching trade. Decrease the quantity of both the disposal trade and the matching trade by the
    minimum of their quantities. Update the notional value, commission, notional value GBP and commission GBP of the
    disposal trade and the matching trade.
    :param disposal_trade_id:
    :param matching_trade_id:
    :param all_trades:
    :return: A tuple of the disposal trade and the matching trade
    """
    disposal_trade_row = all_trades.loc[disposal_trade_id]
    matching_trade_row = all_trades.loc[matching_trade_id]

    # Calculate the quantity to match
    quantity_to_match = min(
        abs(disposal_trade_row["Quantity"]), abs(matching_trade_row["Quantity"])
    )

    scale = quantity_to_match / abs(matching_trade_row["Quantity"])

    # Create a matching trade object
    matching_trade = Trade(
        matching_trade_id,
        matching_trade_row["Symbol"],
        matching_trade_row["Currency"],
        matching_trade_row["Date/Time"],
        quantity_to_match * np.sign(matching_trade_row["Quantity"]),
        matching_trade_row["Notional Value"] * scale,
        matching_trade_row["Comm/Fee"] * scale,
        matching_trade_row["Notional Value GBP"] * scale,
        matching_trade_row["Comm in GBP"] * scale,
    )

    scale = quantity_to_match / abs(disposal_trade_row["Quantity"])

    # Create a disposal trade object
    disposal_trade = Trade(
        disposal_trade_id,
        disposal_trade_row["Symbol"],
        disposal_trade_row["Currency"],
        disposal_trade_row["Date/Time"],
        quantity_to_match * np.sign(disposal_trade_row["Quantity"]),
        disposal_trade_row["Notional Value"] * scale,
        disposal_trade_row["Comm/Fee"] * scale,
        disposal_trade_row["Notional Value GBP"] * scale,
        disposal_trade_row["Comm in GBP"] * scale,
    )

    # Update quantity, notional value and commission of the disposal trade in the trades dataframe
    remaining_disposal_trade_quantity = disposal_trade_row[
        "Quantity"
    ] - quantity_to_match * np.sign(disposal_trade_row["Quantity"])

    scale = remaining_disposal_trade_quantity / disposal_trade_row["Quantity"]
    all_trades.at[disposal_trade_id, "Quantity"] = remaining_disposal_trade_quantity
    all_trades.at[disposal_trade_id, "Notional Value"] *= scale
    all_trades.at[disposal_trade_id, "Comm/Fee"] *= scale
    all_trades.at[disposal_trade_id, "Notional Value GBP"] *= scale
    all_trades.at[disposal_trade_id, "Comm in GBP"] *= scale

    # Update quantity, notional value and commission of the matching trade in the trades dataframe
    remaining_matching_trade_quantity = matching_trade_row[
        "Quantity"
    ] - quantity_to_match * np.sign(matching_trade_row["Quantity"])

    scale = remaining_matching_trade_quantity / matching_trade_row["Quantity"]
    all_trades.at[matching_trade_id, "Quantity"] = remaining_matching_trade_quantity
    all_trades.at[matching_trade_id, "Notional Value"] *= scale
    all_trades.at[matching_trade_id, "Comm/Fee"] *= scale
    all_trades.at[matching_trade_id, "Notional Value GBP"] *= scale
    all_trades.at[matching_trade_id, "Comm in GBP"] *= scale
    return disposal_trade, matching_trade


if __name__ == "__main__":
    calculate_gain_and_loss("trades.csv", "Futures")
