from typing import List
from uuid import UUID

from fastapi import APIRouter, HTTPException
from sqlmodel import select

import schemas
from api.api_v1.deps import SessionDep
from models import Vault
from models.vault_performance import VaultPerformance

router = APIRouter()


@router.get("/", response_model=List[schemas.Vault])
async def get_all_vaults(session: SessionDep):
    statement = select(Vault)
    vaults = session.exec(statement).all()
    return vaults


@router.get("/{vault_id}", response_model=schemas.Vault)
async def get_vault_info(session: SessionDep, vault_id: str):
    statement = select(Vault).where(Vault.id == UUID(vault_id))
    vault = session.exec(statement).one()

    if vault is None:
        raise HTTPException(
            status_code=400,
            detail="The data not found in the database.",
        )

    return vault


@router.get("/{vault_id}/performance")
async def get_vault_performance(session: SessionDep, vault_id: str):
    vault_performance = session.exec(
        select(VaultPerformance)
        .where(VaultPerformance.vault_id == vault_id)
        .order_by(VaultPerformance.datetime.asc())
    ).all()
    if not vault_performance:
        raise HTTPException(status_code=404, detail="Vault performance not found")
    return vault_performance
