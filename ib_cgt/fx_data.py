"""
A module to load FX data from a CSV file.
Author: Emre Tezel
"""

import pandas as pd
from pathlib import Path


class FXData:
    """
    Class to represent FX data.
    """

    def __init__(self):
        # Load all the csv files in the fx folder as separate dataframes.
        # Put them an in a dictionary with the first three characters of the filename as the key.
        # The first column of each dataframe is the date, make it the index.
        self.fx_data = {}

        for file in Path("fx").glob("*.csv"):
            key = file.stem[:3]
            self.fx_data[key] = pd.read_csv(file, parse_dates=["DATETIME"])

            # Remove the time part of the date and then set it back to datetime and then as index
            self.fx_data[key]["DATETIME"] = self.fx_data[key]["DATETIME"].dt.normalize()
            self.fx_data[key].set_index("DATETIME", inplace=True)

    def get_fx_rate(self, currency: str, date: pd.Timestamp) -> float:
        """
        Get the FX rate for a currency on a given date.

        Args:
            currency: The currency to get the rate for.
            date: The date to get the rate for.

        Returns:
            The FX rate for the currency on the date.
        """
        # Normalize the date
        date = date.normalize()

        # First get the fx rate to USD
        if currency == "USD":
            to_usd = 1.0
        elif currency == "GBP":
            return 1.0
        else:
            # Get the USD to currency rate at the date or the closest date before the date
            fxs = self.fx_data[currency].loc[:date, "PRICE"]

            # if fxs is empty, return first value of the series otherwise return the last value
            to_usd = (
                fxs.iloc[-1]
                if not fxs.empty
                else self.fx_data[currency].iloc[0]["PRICE"]
            )

        # Then get the GBP to USD rate
        to_gbp = self.fx_data["GBP"].loc[:date, "PRICE"].iloc[-1]

        # Calculate the rate from the currency to GBP
        rate = to_usd / to_gbp
        return rate
