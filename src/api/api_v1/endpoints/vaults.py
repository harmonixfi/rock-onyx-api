from typing import List
from uuid import UUID

from fastapi import APIRouter, HTTPException
import pandas as pd
from sqlmodel import select

from models.vault_performance import VaultPerformance
import schemas
from api.api_v1.deps import SessionDep
from models import Vault
from models.pps_history import PricePerShareHistory
from utils.slug import slugify

router = APIRouter()


@router.get("/", response_model=List[schemas.Vault])
async def get_all_vaults(session: SessionDep):
    statement = select(Vault)
    vaults = session.exec(statement).all()
    return vaults


@router.get("/{vault_slug}", response_model=schemas.Vault)
async def get_vault_info(session: SessionDep, vault_slug: str):
    statement = select(Vault).where(Vault.slug == vault_slug)
    vault = session.exec(statement).first()
    if vault is None:
        raise HTTPException(
            status_code=400,
            detail="The data not found in the database.",
        )
    return vault


@router.get("/{vault_slug}/performance")
async def get_vault_performance(session: SessionDep, vault_slug: str):
    # Get the VaultPerformance records for the given vault_id
    statement = select(Vault).where(Vault.slug == vault_slug)
    vault = session.exec(statement).first()
    if vault is None:
        raise HTTPException(
            status_code=400,
            detail="The data not found in the database.",
        )

    perf_hist = session.exec(
        select(VaultPerformance)
        .where(VaultPerformance.vault_id == vault.id)
        .order_by(VaultPerformance.datetime.asc())
    ).all()

    # Convert the list of VaultPerformance objects to a DataFrame
    pps_history_df = pd.DataFrame([vars(rec) for rec in perf_hist])

    # Rename the datetime column to date
    pps_history_df.rename(columns={"datetime": "date"}, inplace=True)

    # Convert the date column to string format
    pps_history_df["date"] = pps_history_df["date"].dt.strftime("%Y-%m-%d")
    pps_history_df.fillna(0, inplace=True)

    # Convert the DataFrame to a dictionary and return it
    return pps_history_df[["date", "apy_1m", "apy_ytd"]].to_dict(orient="list")
