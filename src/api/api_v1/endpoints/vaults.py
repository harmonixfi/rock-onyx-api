from typing import List

from fastapi import APIRouter, HTTPException
import pandas as pd
from sqlmodel import select

from models.vault_performance import VaultPerformance
import schemas
from api.api_v1.deps import SessionDep
from models import Vault

router = APIRouter()


def _update_vault_apy(vault: Vault) -> schemas.Vault:
    schema_vault = schemas.Vault.model_validate(vault)

    if vault.slug == "delta-neutral-vault":
        schema_vault.apy = vault.monthly_apy
    elif vault.slug == "options-wheel-vault":
        schema_vault.apy = vault.ytd_apy

    return schema_vault


@router.get("/", response_model=List[schemas.Vault])
async def get_all_vaults(session: SessionDep):
    statement = select(Vault)
    vaults = session.exec(statement).all()
    data = []
    for vault in vaults:
        schema_vault = _update_vault_apy(vault)
        data.append(schema_vault)
    return data


@router.get("/{vault_slug}", response_model=schemas.Vault)
async def get_vault_info(session: SessionDep, vault_slug: str):
    statement = select(Vault).where(Vault.slug == vault_slug)
    vault = session.exec(statement).first()
    if vault is None:
        raise HTTPException(
            status_code=400,
            detail="The data not found in the database.",
        )

    schema_vault = _update_vault_apy(vault)
    return schema_vault


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
    if len(perf_hist) == 0:
        return {"date": [], "apy": []}

    # Convert the list of VaultPerformance objects to a DataFrame
    pps_history_df = pd.DataFrame([vars(rec) for rec in perf_hist])

    # Rename the datetime column to date
    pps_history_df.rename(columns={"datetime": "date"}, inplace=True)

    if vault.slug == "delta-neutral-vault":
        pps_history_df["apy"] = pps_history_df["apy_1m"]
    elif vault.slug == "options-wheel-vault":
        pps_history_df["apy"] = pps_history_df["apy_ytd"]

    # Convert the date column to string format
    pps_history_df["date"] = pps_history_df["date"].dt.strftime("%Y-%m-%dT%H:%M:%S")
    pps_history_df.fillna(0, inplace=True)

    # Convert the DataFrame to a dictionary and return it
    return pps_history_df[["date", "apy"]].to_dict(orient="list")
