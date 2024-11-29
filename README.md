# ibcapuk
A package for calculating capital gains and losses based on Interactive Broker statements for UK residents.

## Disclaimer
This software is provided "as is" and is intended for educational and informational purposes only. 
It may not accurately calculate capital gains or losses under UK tax regulations. By using this code, 
you acknowledge that the author assumes no responsibility for errors, omissions, or any outcomes resulting 
from its use. For accurate tax calculations or advice, consult a qualified professional. 
Use this software at your own risk.

## Installation
Download the package from GitHub and install it using pip in the project root directory:
```bash
git clone https://github.com/emretezel/ibcapuk.git
cd ibcapuk
pip install -e .
```
This would install the package in development mode, so that one can make changes to the code and test it 
without having to reinstall the package.

## Usage
1. Download your Interactive Broker statements in htm format. It is recommended to go back as far as possible 
so that all disposals are accounted for.
2. The next step is to parse the trades from the statements. This can be done using the following code:
```python
from ibcapuk import parse_trades

if __name__ == "__main__":
    parse_trades(
        [
            "../statements/futures/17_18.htm",
            "../statements/futures/18_19.htm",
            "../statements/futures/19_20.htm",
            "../statements/futures/20_21.htm",
            "../statements/futures/21_22.htm",
            "../statements/futures/22_23.htm",
            "../statements/futures/23_24.htm",
            "../statements/futures/24_25.htm",
        ],
        [8, 8, 8, 8, 8, 8, 8, 9],
    )
```
The second argument of the `parse_trades` function is a list of integers that represent which table on each statement
corresponds to the trades. The numbers are 1-indexed, so the first table is 1, the second table is 2, and so on.
This will create a `trades.csv` file in the same directory where you ran the script. Please note that FX rates are 
stored in the fx folder inside the package root folder. The latest fx rates could be stale. I will try to update them
as often as possible.
3. The next step is to calculate the capital gains and losses. This can be done using the following code:
```python
from ibcapuk.report import report
from ibcapuk.match_trades import match_trades


if __name__ == "__main__":
    disposals = match_trades("trades.csv", ["Futures", "Stocks", "Forex"])

    for year in range(2017, 2025):
        report(year, disposals)
```
This would create individual reports for each year in the range 2017-2024.
