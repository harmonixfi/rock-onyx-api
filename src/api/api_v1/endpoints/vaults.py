import numpy as np
import pandas as pd
from fastapi import APIRouter, FastAPI

from services.gsheet import authenticate_gspread
from services.market_data import get_price

router = APIRouter()


def fetch_data(client, sheet_name):
    sheet = client.open(sheet_name).get_worksheet(1)
    data = sheet.get_all_records()
    df = pd.DataFrame(data)
    df["Vault Value"] = df["Vault Value"].astype(float)
    df["Cap Gain"] = df["Cap Gain"].astype(float)
    df["Cum Return"] = df["Cum Return"].astype(float)
    df["APR"] = df["APR"].astype(float)
    df["Benchmark %"] = df["Benchmark %"].astype(float)

    df[["Benchmark", "Benchmark %"]] = df[["Benchmark", "Benchmark %"]].astype("float")
    return df


def calculate_max_drawdown(cum_returns):
    # Calculate the maximum drawdown in the cumulative return series
    peak = cum_returns.cummax()
    drawdown = (cum_returns - peak) / peak
    max_drawdown = drawdown.min()
    return max_drawdown


@router.get("/vaults/7c5406ae-f72c-412a-9444-f5b83c78ee48")
async def get_vault_info():
    client = authenticate_gspread()
    df = fetch_data(client, "Rock Onyx Fund")

    apr = df["APR"].iloc[-1]
    monthly_apy = df["APY_1M"].iloc[-1]
    weekly_apy = df["APY_1W"].iloc[-1]
    max_drawdown = calculate_max_drawdown(
        df["Cum Return"]
    )  # Convert back to percentage

    current_price = get_price("ETHUSDT")
    vault_capacity = 4_000_000 / current_price

    return {
        "apr": apr,
        "monthly_apy": monthly_apy,
        "weekly_apy": weekly_apy,
        "max_drawdown": max_drawdown,
        "total_deposit": 5825,
        "vault_capacity": vault_capacity,
        "vault_currency": "USDC",
    }


@router.get("/vaults/7c5406ae-f72c-412a-9444-f5b83c78ee48/performance")
async def get_vault_performance():
    client = authenticate_gspread()
    df = fetch_data(client, "Rock Onyx Fund")

    # Convert non-compliant values to None
    df = df.replace([np.inf, -np.inf], np.nan)
    df = df.where(pd.notnull(df), 0)

    # Prepare data for JSON response
    performance_data = {
        "date": df["Date"].tolist(),
        "cum_return": df["Cum Return"].tolist(),
        "benchmark_ret": df["Benchmark %"].tolist(),
    }

    return performance_data
