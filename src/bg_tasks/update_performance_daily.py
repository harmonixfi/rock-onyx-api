from datetime import datetime, timedelta

import numpy as np
import pandas as pd

from services.gsheet import authenticate_gspread
from services.market_data import get_price, get_klines


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


def calculate_options_apr(sheet):
    options_ws = sheet.get_worksheet(3)
    data = options_ws.get_all_records()
    data = pd.DataFrame(data)

    capital_employed = float(options_ws.acell("I2").value)

    # Calculate total premiums received
    data["Expiration Date"] = pd.to_datetime(data["Expiration Date"])
    data["Annualized Premium"] = (data["Premium"] * data["Quantity"]) * 26
    total_annualized_premiums = data["Annualized Premium"].sum()

    # Calculate APR
    apr = total_annualized_premiums / capital_employed
    return apr


# Step 4: Calculate Performance Metrics
def calculate_performance(sheet, df):
    current_price = get_price("ETHUSDT")

    # d = datetime.strptime(df["Date"].iloc[-1], "%Y-%m-%d")
    # candles = get_klines("ETHUSDT", end_time=(d + timedelta(days=2)), limit=1)
    # current_price = float(candles[0][4])

    spot_ws = sheet.get_worksheet(2)
    options_ws = sheet.get_worksheet(3)

    # Fetch data from specific cells
    spot_val_cell = spot_ws.acell("D7").value
    if "ETH" in spot_val_cell:
        spot_val_cell = spot_val_cell.replace("ETH", "")
    cash_cell = spot_ws.acell("D8").value
    option_eth_cell = options_ws.acell("I2").value

    spot_val = float(spot_val_cell) * current_price
    spot_eth_val = float(spot_val_cell)
    cash = float(cash_cell)
    option_usd = float(option_eth_cell)

    radiant_eth_val = float(spot_ws.acell("P8").value)

    # Annualized return of df['Vault Value']
    lido_apr = float(spot_ws.acell("L7").value)
    radiant_apr = float(spot_ws.acell("R7").value)

    # Calculations
    df.loc[len(df)] = [
        datetime.utcnow().strftime("%Y-%m-%d"),
        # (d + timedelta(days=1)).strftime("%Y-%m-%d"),
        None,
        None,
        None,
        None,
        None,
        None,
    ]  # Add new row for current date

    # Calculate daily reward from Lido and radiant
    radiant_daily_reward = radiant_eth_val * (radiant_apr / 365) * len(df)
    staked_reward_usd = (radiant_daily_reward) * current_price

    df.loc[len(df) - 1, "Vault Value"] = (
        spot_val + cash + option_usd + staked_reward_usd
    )
    df["Cap Gain"] = df["Vault Value"] - df["Vault Value"].shift()
    df.loc[len(df) - 1, "Benchmark"] = current_price

    # Calculate Cumulative Returns
    df["Cum Return"] = ((df["Vault Value"] / df["Vault Value"].iloc[0]) - 1) * 100
    df["Benchmark %"] = ((df["Benchmark"] / df["Benchmark"].iloc[0]) - 1) * 100

    # calculate apr for staking
    reward1 = lido_apr * spot_eth_val
    reward2 = radiant_apr * spot_eth_val
    stake_apr = (reward1 + reward2) / spot_eth_val

    premium_apr = calculate_options_apr(sheet)

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
