from datetime import datetime, timedelta

import numpy as np
import pandas as pd
import web3

from services.gsheet import authenticate_gspread
from services.market_data import get_price, get_klines
from web3 import Web3
from core.abi_reader import read_abi
from core.config import settings
from services.uniswap_data import get_uniswap_quote

# Connect to the Ethereum network
w3 = Web3(Web3.HTTPProvider(settings.ARBITRUM_MAINNET_INFURA_URL))
token_abi = read_abi("ERC20")
rockonyx_stablecoin_vault_abi = read_abi("RockOnyxStableCoin")
rockOnyxUSDTVaultContract = web3.eth.contract(
    address=settings.ROCKONYX_STABLECOIN_ADDRESS, abi=rockonyx_stablecoin_vault_abi
)


def balance_of(wallet_address, token_address):
    token_contract = w3.eth.contract(address=token_address, abi=token_abi)
    token_balance = token_contract.functions.balanceOf(wallet_address).call()
    return token_balance


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


def get_wallet_balances():
    # Call the getUserAccountData function
    wallet_address = Web3.to_checksum_address(settings.WALLET_ADDRESS)
    # Get ETH balance
    eth_balance = w3.eth.get_balance(wallet_address)
    eth_balance = w3.from_wei(eth_balance, "ether")

    wstETH_balance = balance_of(wallet_address, settings.WSTETH_ADDRESS)
    wstETH_balance = w3.from_wei(wstETH_balance, "ether")

    usdc_balance = balance_of(wallet_address, settings.USDC_ADDRESS) / 10**6

    usdce_balance = balance_of(wallet_address, settings.USDCE_ADDRESS) / 10**6

    return {
        "ETH": eth_balance,
        "wstETH": wstETH_balance,
        "USDC": usdc_balance,
        "USDC.e": usdce_balance,
    }


def get_price_per_share_history(sheet):
    ws = sheet.get_worksheet(5)
    data = ws.get_all_records()
    df = pd.DataFrame(data)
    df["Date"] = pd.to_datetime(df["Date"])
    return df


def update_price_per_share_sheet(sheet, row_num, values):
    ws = sheet.get_worksheet(5)
    ws.update(range_name=f"A{row_num}:D{row_num}", values=[values])


def calculate_roi(after: float, before: float, days: int) -> float:
    # calculate our annualized return for a vault
    pps_delta = (after - before) / (before or 1)
    annualized_roi = (1 + pps_delta) ** (365.2425 / days) - 1
    return annualized_roi


def get_before_price_per_shares(df, days=30) -> pd.Series:
    today = datetime.utcnow()
    # Calculate the date 30 days ago
    previous_month = (
        (today - timedelta(days=days))
        .replace(hour=0)
        .replace(minute=0)
        .replace(second=0)
        .replace(microsecond=0)
    )

    # Check if the date is in the DataFrame, if not, get the first value
    row = df[df["Date"] == previous_month]
    if len(row) > 0:
        result = row.iloc[0]
    else:
        result = df.iloc[0]

    return result["PricePerShare"]


def get_current_pps():
    pps = rockOnyxUSDTVaultContract.functions.pricePerShare().call()

    return pps


def get_current_tvl():
    pps = rockOnyxUSDTVaultContract.functions.totalValueLocked().call()

    return pps


# Step 4: Calculate Performance Metrics
def calculate_performance(sheet, df):
    current_price = get_price("ETHUSDT")

    # today = datetime.strptime(df["Date"].iloc[-1], "%Y-%m-%d")
    today = datetime.utcnow().strftime("%Y-%m-%d")
    # candles = get_klines("ETHUSDT", end_time=(today + timedelta(days=2)), limit=1)
    # current_price = float(candles[0][4])

    price_per_share_df = get_price_per_share_history(sheet)
    total_shares = price_per_share_df["TotalShares"].iloc[-1]

    current_price_per_share = get_current_pps()
    total_balance = get_current_tvl()
    update_price_per_share_sheet(
        sheet,
        row_num=int(len(price_per_share_df) + 2),  # include header
        values=[
            today,
            0,
            0,
            float(current_price_per_share),
        ],
    )

    # Calculate Monthly APY
    month_ago_price_per_share = get_before_price_per_shares(price_per_share_df, days=30)
    monthly_apy = calculate_roi(
        current_price_per_share, month_ago_price_per_share, days=30
    )

    week_ago_price_per_share = get_before_price_per_shares(price_per_share_df, days=7)
    weekly_apy = calculate_roi(
        current_price_per_share, week_ago_price_per_share, days=7
    )
    apys = [monthly_apy, weekly_apy]
    net_apy = next((value for value in apys if value != 0), 0)

    # assume we are compounding every week
    compounding = 52

    # calculate our APR after fees
    apr = compounding * ((net_apy + 1) ** (1 / compounding)) - compounding

    # Calculations
    df.loc[len(df)] = [
        today,
        total_balance,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
    ]  # Add new row for current date

    df["Cap Gain"] = df["Vault Value"] - df["Vault Value"].shift()
    df.loc[len(df) - 1, "Benchmark"] = current_price
    # Calculate Cumulative Returns
    df["Cum Return"] = ((df["Vault Value"] / df["Vault Value"].iloc[0]) - 1) * 100
    df["Benchmark %"] = ((df["Benchmark"] / df["Benchmark"].iloc[0]) - 1) * 100
    df.loc[len(df) - 1, "APR"] = apr * 100
    df.loc[len(df) - 1, "APY_1M"] = monthly_apy * 100
    df.loc[len(df) - 1, "APY_1W"] = weekly_apy * 100
    return df


# Step 5: Write Data Back to Google Sheets
def update_performance_sheet(sheet, df):
    performance_sheet = sheet.get_worksheet(1)
    data = []
    for col in df.columns:
        data.append(df[col].iloc[-1])

    row = len(df) + 1
    performance_sheet.update(range_name=f"A{row}:I{row}", values=[data])


# Main Execution
def main():
    client = authenticate_gspread()

    sheet, df = fetch_data(client, "Rock Onyx Fund")
    df = calculate_performance(sheet, df)
    update_performance_sheet(sheet, df)


if __name__ == "__main__":
    main()
