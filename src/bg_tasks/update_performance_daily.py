from datetime import datetime

import numpy as np
import pandas as pd

from services.gsheet import authenticate_gspread
from services.market_data import get_price


def parse_currency_to_float(series: pd.Series):
    series = series.str.replace("$", "")
    series = series.str.replace(",", "").astype(float)
    return series


# Step 2: Fetch Data from Google Sheets
def fetch_data(client, sheet_name):
    sheet = client.open(sheet_name)
    ws = sheet.get_worksheet(1)
    data = ws.get_all_records()
    df = pd.DataFrame(data)
    df["Vault Value"] = df["Vault Value"].astype(float)
    df["Cap Gain"] = df["Cap Gain"].astype(float)
    df["Cum Return"] = df["Cum Return"].astype(float)
    df["APR"] = df["APR"].astype(float)
    df["Benchmark %"] = df["Benchmark %"].astype(float)

    df[["Benchmark", "Benchmark %"]] = df[["Benchmark", "Benchmark %"]].astype("float")
    return sheet, df


# Step 4: Calculate Performance Metrics
def calculate_performance(sheet, df):
    current_price = get_price("ETHUSDT")

    spot_ws = sheet.get_worksheet(2)
    options_ws = sheet.get_worksheet(3)

    # Fetch data from specific cells
    spot_val_cell = spot_ws.acell("D7").value
    if "ETH" in spot_val_cell:
        spot_val_cell = spot_val_cell.replace("ETH", "")
    cash_cell = spot_ws.acell("D8").value
    option_eth_cell = options_ws.acell("I2").value

    spot_val = float(spot_val_cell) * current_price
    cash = float(cash_cell)
    option_eth = float(option_eth_cell)

    # Calculations
    df.loc[len(df)] = [
        datetime.utcnow().strftime("%Y-%m-%d"),
        None,
        None,
        None,
        None,
        None,
        None,
    ]  # Add new row for current date
    df.loc[len(df) - 1, "Vault Value"] = spot_val + cash + option_eth
    df["Cap Gain"] = df["Vault Value"] - df["Vault Value"].shift()
    df.loc[len(df) - 1, "Benchmark"] = current_price

    # Calculate Cumulative Returns
    df["Cum Return"] = ((df["Vault Value"] / df["Vault Value"].iloc[0]) - 1) * 100
    df["Benchmark %"] = ((df["Benchmark"] / df["Benchmark"].iloc[0]) - 1) * 100

    # Annualized return of df['Vault Value']
    lido_apr = float(spot_ws.acell("L7").value)
    radiant_apr = float(spot_ws.acell("R7").value)

    # calculate apr for staking
    spot_eth_val = float(spot_val_cell)
    reward1 = lido_apr * spot_eth_val
    reward2 = radiant_apr * spot_eth_val
    stake_apr = (reward1 + reward2) / spot_eth_val

    # calculate APR for options premium
    premium_values = options_ws.batch_get(("D2:D9",))[0]
    position_sizes = options_ws.batch_get(("E2:E9",))[0]

    total_premium = 0
    for premium, size in zip(premium_values, position_sizes):
        total_premium += float(size[0]) * float(premium[0])
    premium_apr = (total_premium / option_eth) * 52

    portfolio_apr = (stake_apr * 0.8) + (premium_apr * 0.2)
    df.loc[len(df) - 1, "APR"] = portfolio_apr * 100

    return df


# Step 5: Write Data Back to Google Sheets
def update_performance_sheet(sheet, df):
    performance_sheet = sheet.get_worksheet(1)
    data = []
    for col in df.columns:
        data.append(df[col].iloc[-1])

    row = len(df) + 1
    performance_sheet.update(range_name=f"A{row}:G{row}", values=[data])


# Main Execution
def main():
    client = authenticate_gspread()

    sheet, df = fetch_data(client, "Rock Onyx Fund")
    df = calculate_performance(sheet, df)
    update_performance_sheet(sheet, df)


if __name__ == "__main__":
    main()
