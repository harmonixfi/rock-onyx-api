import json
import numpy as np
import pandas as pd
from fastapi import APIRouter, FastAPI, HTTPException, Path
from sqlmodel import select
from api.api_v1.deps import SessionDep

from services.gsheet import authenticate_gspread
from models import Vault

router = APIRouter()

# Load vaults data from JSON file
with open("data/vaults.json", "r") as vaults_file:
    vaults_data = json.load(vaults_file)


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


@router.get("/vaults")
async def get_all_vaults(session: SessionDep):
    statement = select(Vault)
    vaults = session.exec(statement).all()
    return vaults


@router.get("/vaults/{vault_id}")
async def get_vault_info(vault_id: str):
    vault = select(Vault).where(Vault.id == vault_id)
    
    if not vault:
        raise HTTPException(
            status_code=400,
            detail="The data not found in the database.",
        )

    return vault


@router.get("/vaults/{vault_id}/performance")
async def get_vault_performance(vault_id: str):
    vault_info = next((vault for vault in vaults_data if vault["id"] == vault_id), None)
    if not vault_info:
        return {"error": "Vault not found"}

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
