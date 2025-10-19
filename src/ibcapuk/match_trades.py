"""
A modules that calculates the gain and loss of disposed instruments.
Author: Emre Tezel
"""

from collections.abc import Iterable

import numpy as np
import pandas as pd

from ibcapuk.disposal import Disposal
from ibcapuk.trade import Trade


def match_trades(
    trades_file: str, instrument_types: list[str], unmatched_file: str = "unmatched.csv"
) -> list[Disposal]:
    """
    Calculate the gain and loss of disposed instruments.

    Args:
        trades_file: The CSV file containing the trades.
        instrument_types: The type of instruments to calculate the gain and loss for.
        unmatched_file: The file to write the unmatched trades.
        :return: A list of disposals.
    """
    # Raise exception if instrument type contains Bonds
    if "Bonds" in instrument_types:
        raise ValueError("Bonds are not supported.")

    # Read the trades from the CSV file into a DataFrame. Parse the dates as dates.
    all_trades = pd.read_csv(trades_file, parse_dates=["Date/Time"])

    # Filter the trades by the instrument type
    all_trades = all_trades[all_trades["Instrument Type"].isin(instrument_types)]

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

        if _match_disposal_with_candidates(
            trade_id,
            filter_same_day_trades(all_trades, trade).index,
            all_trades,
            disposal_trades,
            matching_trades,
        ):
            if all_trades.at[trade_id, "Quantity"] == 0:
                disposals.append(create_disposal(disposal_trades, matching_trades))
                continue

        if _match_disposal_with_candidates(
            trade_id,
            filter_bed_and_breakfast_trades(all_trades, trade).index,
            all_trades,
            disposal_trades,
            matching_trades,
        ):
            if all_trades.at[trade_id, "Quantity"] == 0:
                disposals.append(create_disposal(disposal_trades, matching_trades))
                continue

        # Now we need to get the list of all the matching trades occurred in the past.
        section_104_trades = filter_section_104_trades(all_trades, trade)

        if not section_104_trades.empty:
            # Sum the quantity, notional value, commission, notional value GBP and commission GBP of the matching trades
            first_trade_id = collapse_section_104_trades(all_trades, section_104_trades)

            _match_disposal_with_candidates(
                trade_id,
                [first_trade_id],
                all_trades,
                disposal_trades,
                matching_trades,
            )

        # If disposal trades list is not empty, aggregate the disposal trades.
        if disposal_trades:
            disposal = create_disposal(disposal_trades, matching_trades)
            disposals.append(disposal)

    # Save unmatched trades to a file
    unmatched_trades = all_trades[all_trades["Quantity"] != 0]
    unmatched_trades.to_csv(unmatched_file, index=False)
    return disposals


def create_disposal(
    disposal_trades: list[Trade], matching_trades: list[Trade]
) -> Disposal:
    aggregated_trade = aggregate_disposal_trades(disposal_trades)

    # Create a disposal trade object with the matching trades
    disposal = Disposal(aggregated_trade, matching_trades)
    return disposal


def aggregate_disposal_trades(disposal_trades: list[Trade]) -> Trade:
    aggregated_trade = disposal_trades[0]

    for trade in disposal_trades[1:]:
        aggregated_trade += trade

    return aggregated_trade


def collapse_section_104_trades(
    all_trades: pd.DataFrame, section_104_trades: pd.DataFrame
) -> int:
    # If section 104 trades contain only one trade, then there is nothing to collapse
    if len(section_104_trades) == 1:
        return section_104_trades.index[0]

    total_quantity = section_104_trades["Quantity"].sum()
    total_notional_value = section_104_trades["Notional Value"].sum()
    total_commission = section_104_trades["Comm/Fee"].sum()
    total_notional_value_gbp = section_104_trades["Notional Value GBP"].sum()
    total_commission_gbp = section_104_trades["Comm in GBP"].sum()

    first_trade_id = section_104_trades.index[0]

    # Delete all but the first matching trade from the all trade dataframe
    for matching_trade_id in section_104_trades.index[1:]:
        all_trades.drop(matching_trade_id, inplace=True)

    # For the first matching trade, update the quantity, notional value, commission, notional value GBP and
    # commission GBP to the total values
    all_trades.at[first_trade_id, "Quantity"] = total_quantity
    all_trades.at[first_trade_id, "Notional Value"] = total_notional_value
    all_trades.at[first_trade_id, "Comm/Fee"] = total_commission
    all_trades.at[first_trade_id, "Notional Value GBP"] = total_notional_value_gbp
    all_trades.at[first_trade_id, "Comm in GBP"] = total_commission_gbp

    # Update the fx rate by dividing the total notional value to the total notional value GBP
    all_trades.at[first_trade_id, "FX Rate"] = (
        total_notional_value_gbp / total_notional_value
        if total_notional_value != 0
        else 0
    )

    return first_trade_id


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


def _match_disposal_with_candidates(
    disposal_trade_id: int,
    matching_trade_ids: Iterable[int],
    all_trades: pd.DataFrame,
    disposal_trades: list[Trade],
    matching_trades: list[Trade],
) -> bool:
    """
    Match a disposal trade against the provided candidate trade ids, updating the tracking collections.
    Returns True when at least one match is made.
    """
    matched = False

    for matching_trade_id in matching_trade_ids:
        disposal_trade, matching_trade = process_matching_trade(
            disposal_trade_id, matching_trade_id, all_trades
        )
        disposal_trades.append(disposal_trade)
        matching_trades.append(matching_trade)
        matched = True

        if all_trades.at[disposal_trade_id, "Quantity"] == 0:
            break

    return matched


def process_matching_trade(
    disposal_trade_id: int, matching_trade_id: int, all_trades: pd.DataFrame
) -> tuple[Trade, Trade]:
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

    # Create a matching trade object
    matching_trade = _create_partial_trade(
        matching_trade_row, matching_trade_id, quantity_to_match
    )

    # Create a disposal trade object
    disposal_trade = _create_partial_trade(
        disposal_trade_row, disposal_trade_id, quantity_to_match
    )

    _update_remaining_trade(
        all_trades, disposal_trade_id, disposal_trade_row, quantity_to_match
    )
    _update_remaining_trade(
        all_trades, matching_trade_id, matching_trade_row, quantity_to_match
    )
    return disposal_trade, matching_trade


def _create_partial_trade(
    trade_row: pd.Series, trade_id: int, quantity_to_match: float
) -> Trade:
    """
    Create a Trade scaled to the matched quantity from an existing trade row.
    """
    scale = quantity_to_match / abs(trade_row["Quantity"])

    return Trade(
        trade_row["Instrument Type"],
        trade_id,
        trade_row["Symbol"],
        trade_row["Currency"],
        trade_row["Date/Time"],
        quantity_to_match * np.sign(trade_row["Quantity"]),
        trade_row["Notional Value"] * scale,
        trade_row["Comm/Fee"] * scale,
        trade_row["Notional Value GBP"] * scale,
        trade_row["Comm in GBP"] * scale,
    )


def _update_remaining_trade(
    all_trades: pd.DataFrame,
    trade_id: int,
    trade_row: pd.Series,
    quantity_to_match: float,
) -> None:
    """
    Update the residual quantity and financial totals of a trade after matching.
    """
    signed_match = quantity_to_match * np.sign(trade_row["Quantity"])
    remaining_quantity = trade_row["Quantity"] - signed_match
    original_quantity = trade_row["Quantity"]
    all_trades.at[trade_id, "Quantity"] = remaining_quantity

    if original_quantity == 0:
        scale = 0
    else:
        scale = remaining_quantity / original_quantity

    for column in ("Notional Value", "Comm/Fee", "Notional Value GBP", "Comm in GBP"):
        all_trades.at[trade_id, column] *= scale
