from typing import List
from uuid import UUID

from fastapi import APIRouter, HTTPException
import pandas as pd
from sqlmodel import select

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
    schemasvaults = []
    for vault in vaults:
        schemavaults = schemas.Vault(
            id=vault.id,
            name=vault.name,
            apr=vault.apr,
            monthly_apy=vault.monthly_apy,
            weekly_apy=vault.weekly_apy,
            max_drawdown=vault.max_drawdown,
            vault_capacity=vault.vault_capacity,
            vault_currency=vault.vault_currency,
            current_round=vault.current_round,
            next_close_round_date=vault.next_close_round_date,
            slug = slugify(vault.name)
        )  
        schemasvaults.append(schemavaults)
    return schemasvaults


@router.get("/{vault_id}", response_model=schemas.Vault)
async def get_vault_info(session: SessionDep, vault_id: str):
    statement = select(Vault).where(Vault.id == UUID(vault_id))
    vault = session.exec(statement).one()
    schemavaults = schemas.Vault(
            id=vault.id,
            name=vault.name,
            apr=vault.apr,
            monthly_apy=vault.monthly_apy,
            weekly_apy=vault.weekly_apy,
            max_drawdown=vault.max_drawdown,
            vault_capacity=vault.vault_capacity,
            vault_currency=vault.vault_currency,
            current_round=vault.current_round,
            next_close_round_date=vault.next_close_round_date,
            slug = slugify(vault.name)
        )  
    if vault is None:
        raise HTTPException(
            status_code=400,
            detail="The data not found in the database.",
        )

    return vault


@router.get("/{vault_id}/performance")
async def get_vault_performance(session: SessionDep, vault_id: str):
    # Get the PricePerShareHistory records for the given vault_id
    pps_history = session.exec(
        select(PricePerShareHistory)
        .where(PricePerShareHistory.vault_id == vault_id)
        .order_by(PricePerShareHistory.datetime.asc())
    ).all()
    
    # Convert the list of PricePerShareHistory objects to a DataFrame
    pps_history_df = pd.DataFrame([vars(pps) for pps in pps_history])

    # Calculate the cumulative return
    pps_history_df["cum_return"] = (
        (pps_history_df["price_per_share"] / pps_history_df["price_per_share"].iloc[0]) - 1
    ) * 100

    # Rename the datetime column to date
    pps_history_df.rename(columns={"datetime": "date"}, inplace=True)

    # Convert the date column to string format
    pps_history_df["date"] = pps_history_df["date"].dt.strftime('%Y-%m-%d')

    # Convert the DataFrame to a dictionary and return it
    return pps_history_df[["date", "cum_return"]].to_dict(orient="list")
