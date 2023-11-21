from datetime import datetime
import gspread
import pandas as pd
import numpy as np
import requests
from oauth2client.service_account import ServiceAccountCredentials

# scope = [
#     "https://spreadsheets.google.com/feeds",
#     "https://www.googleapis.com/auth/drive",
# ]

# add credentials to the account
# creds = ServiceAccountCredentials.from_json_keyfile_name("config/auth.json", scope)


# Step 1: Setup and Authenticate with Google Sheets
def authenticate_gspread():
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive.file",
        "https://www.googleapis.com/auth/drive",
    ]
    creds = ServiceAccountCredentials.from_json_keyfile_name("config/auth.json", scope)
    client = gspread.authorize(creds)
    return client


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
    df["Cap Gain"] = df["Cap Gain"].replace("", np.nan).astype(float)
    df["Cum Return"] = df["Cum Return"].str.replace("%", "")
    df["Cum Return"] = df["Cum Return"].replace("", np.nan).astype(float)
    df["APR"] = df["APR"].replace("", np.nan).astype(float)
    df["Benchmark %"] = df["Benchmark %"].str.replace("%", "")
    df["Benchmark %"] = df["Benchmark %"].replace("", np.nan).astype(float)

    df[["Benchmark", "Benchmark %"]] = df[["Benchmark", "Benchmark %"]].astype("float")
    return sheet, df


# Step 3: Retrieve Current ETHUSDT Price
def get_price():
    url = "https://testnet.binance.vision/api/v3/avgPrice?symbol=ETHUSDT"
    headers = {"Content-Type": "application/json"}
    response = requests.get(url, headers=headers)
    return float(response.json()["price"])


# Step 4: Calculate Performance Metrics
def calculate_performance(sheet, df):
    current_price = get_price()

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
    df[
        "Cum Return"
    ] = ((df["Vault Value"] / df["Vault Value"].iloc[0]) - 1) * 100
    df[
        "Benchmark %"
    ] = ((df["Benchmark"] / df["Benchmark"].iloc[0]) - 1) * 100

    # Annualized return of df['Vault Value']
    days = (datetime.utcnow() - datetime.strptime(df["Date"][0], "%Y-%m-%d")).days
    df[
        "APR"
    ] = ((df["Vault Value"][len(df) - 1] / df["Vault Value"][0]) ** (365 / days) - 1) * 100

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
