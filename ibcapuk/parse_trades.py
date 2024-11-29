"""
A module to parse trades from HTML IB statements into a CSV file.
Author: Emre Tezel
"""

import pandas as pd
from bs4 import BeautifulSoup
from ibcapuk.fx_data import FXData


INSTRUMENT_TYPES = ["Futures", "Stocks", "Forex", "Bonds", "Equity and Index Options"]


def convert_to_number_if_possible(s: str):
    """
    Returns a number if the string can be converted to a number, otherwise returns the string.

    Args:
        s: The string to check.

    Returns:
        True if the string is a number, False otherwise.
    """
    # Remove any commas from the string
    s = s.replace(",", "")

    try:
        return float(s)
    except ValueError:
        return s


def parse_trades(
    files: list[str], table_indexes: list[int], output_file: str = "trades.csv"
):
    """
    Parse trades from HTML IB statements into a CSV file.

    Args:
        files: The HTML files to parse.
        table_indexes: The index of the table to parse in each HTML file.
        output_file: The CSV file to write the parsed trades to.
    """
    dfs = []

    # For each file table index pair, parse the trades and append them to the trades list
    for file, index in zip(files, table_indexes):
        with open(file, "r") as f:
            soup = BeautifulSoup(f, "html.parser")

        table = soup.find_all("table")[index]
        trades = []

        # Iterate over the rows of the table. If the row spans over multiple columns then the row
        # either specified the currency of the following trades or the instrument type of the following trades.
        currency = None
        instrument_type = None
        columns = []

        for row in table.find_all("tr"):
            # Check to see whether the row includes the column headers.
            if row.find_all("th"):
                # If we have previously read columns, then this is the start of a new table for a new instrument type.
                # We need to add the previous instrument type and trades to the dataframe.
                if columns:
                    df = create_df(columns, trades)
                    dfs.append(df)
                    trades = []

                # Read the columns
                columns = [cell.get_text() for cell in row.find_all("th")]
                continue

            cells = row.find_all("td")

            if len(cells) == 1:
                # Does the value start with a supported instrument type?
                for instrument in INSTRUMENT_TYPES:
                    if cells[0].get_text().startswith(instrument):
                        instrument_type = instrument
                        break
                else:
                    # Otherwise, the value is a currency
                    currency = cells[0].get_text()
            else:
                # If the row starts with Total skip it
                if cells[0].get_text().startswith("Total"):
                    continue
                else:
                    trades.append(
                        [instrument_type, currency]
                        + [cell.get_text() for cell in cells[:2]]
                        + [
                            convert_to_number_if_possible(cell.get_text())
                            for cell in cells[2:]
                        ]
                    )

        # We still need to add the last instrument type to the dataframe
        df = create_df(columns, trades)
        dfs.append(df)

    # Concatenate the dataframes and write them to a CSV file, ignoring the index
    trades = pd.concat(dfs, axis=0, ignore_index=True)
    trades.columns = trades.columns.str.replace("\xa0", " ")

    # Only keep the following columns: "Instrument Type", "Currency", "Date/Time", "Quantity", "Notional Value",
    # "Comm/Fee", Symbol, Proceeds, "Comm in GBP"
    # Sometimes Notional Value column is not available if there are no futures trades, check.
    if "Notional Value" not in trades.columns:
        trades = trades[
            [
                "Instrument Type",
                "Currency",
                "Symbol",
                "Date/Time",
                "Quantity",
                "Proceeds",
                "Comm/Fee",
                "Comm in GBP",
            ]
        ]
    else:
        trades = trades[
            [
                "Instrument Type",
                "Currency",
                "Symbol",
                "Date/Time",
                "Quantity",
                "Notional Value",
                "Proceeds",
                "Comm/Fee",
                "Comm in GBP",
            ]
        ]

    # For Forex, Bonds and Stocks, copy the Proceeds column to the Notional Value column
    trades["Notional Value"] = trades.apply(
        lambda t: (
            t["Proceeds"]
            if t["Instrument Type"]
            in ["Forex", "Bonds", "Stocks", "Equity and Index Options", "Bonds"]
            else t["Notional Value"]
        ),
        axis=1,
    )

    # Remove the Proceeds column
    trades.drop("Proceeds", axis=1, inplace=True)

    # For each row look up the fx rate and add as a column
    fx_data = FXData()

    # Iterate over the rows of the dataframe. If the trade type is Forex and if one of the currencies is GBP,
    # then deduct the FX trade from quantity and notional otherwise look up the FX trade.
    for trade_id in trades.index:
        trade = trades.loc[trade_id]

        if trade["Instrument Type"] == "Forex":
            symbol = trade["Symbol"]

            if symbol[:3] == "GBP":
                trades.at[trade_id, "Notional Value GBP"] = -trade["Quantity"]
                trades.at[trade_id, "FX Rate"] = (
                    -trade["Quantity"] / trade["Notional Value"]
                )
            elif symbol[-3:] == "GBP":
                trades.at[trade_id, "Notional Value GBP"] = trade["Notional Value"]
                trades.at[trade_id, "FX Rate"] = (
                    -trade["Notional Value"] / trade["Quantity"]
                )
            else:
                fx_rate = fx_data.get_fx_rate(trade["Currency"], trade["Date/Time"])
                trades.at[trade_id, "FX Rate"] = fx_rate
                trades.at[trade_id, "Notional Value GBP"] = (
                    trade["Notional Value"] * fx_rate
                )
        else:
            fx_rate = fx_data.get_fx_rate(trade["Currency"], trade["Date/Time"])
            trades.at[trade_id, "FX Rate"] = fx_rate
            trades.at[trade_id, "Notional Value GBP"] = (
                trade["Notional Value"] * fx_rate
            )

    # For Stocks, Futures and Bonds, multiply the Comm/Fee column by the FX Rate and save it under Comm in GBP
    trades["Comm in GBP"] = trades.apply(
        lambda t: (
            t["Comm in GBP"]
            if t["Instrument Type"] == "Forex"
            else t["Comm/Fee"] * t["FX Rate"]
        ),
        axis=1,
    )

    # Finally replace any nan values in Comm/Fee column to 0
    trades["Comm/Fee"] = trades["Comm/Fee"].fillna(0)
    trades.to_csv(output_file, index=False)


def create_df(columns, trades):
    df = pd.DataFrame(trades, columns=["Instrument Type", "Currency"] + columns)

    # Convert the Date/Time column to a datetime object
    df["Date/Time"] = pd.to_datetime(df["Date/Time"], format="%Y-%m-%d, %H:%M:%S")

    # Remove columns which are \xa0
    df = df.loc[:, df.columns != "\xa0"]
    return df
