import json
from typing import List

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, and_, select

import schemas
from api.api_v1.deps import SessionDep
from core import constants
from models import PointDistributionHistory, Vault
from models.vault_performance import VaultPerformance
from models.vaults import NetworkChain, VaultCategory

router = APIRouter()


def _update_vault_apy(vault: Vault) -> schemas.Vault:
    schema_vault = schemas.Vault.model_validate(vault)

    if vault.strategy_name == constants.OPTIONS_WHEEL_STRATEGY:
        schema_vault.apy = vault.ytd_apy
    else:
        schema_vault.apy = vault.monthly_apy
    return schema_vault


def get_vault_earned_point_by_partner(
    session: Session, vault: Vault, partner_name: str
) -> PointDistributionHistory:
    """
    Get the latest PointDistributionHistory record for the given vault_id
    """
    statement = (
        select(PointDistributionHistory)
        .where(
            PointDistributionHistory.vault_id == vault.id,
            PointDistributionHistory.partner_name == partner_name,
        )
        .order_by(PointDistributionHistory.created_at.desc())
    )
    point_dist_hist = session.exec(statement).first()
    if point_dist_hist is None:
        return PointDistributionHistory(
            vault_id=vault.id, partner_name=partner_name, point=0.0
        )
    return point_dist_hist


def get_earned_points(session: Session, vault: Vault) -> List[schemas.EarnedPoints]:
    partners = json.loads(vault.routes) + [constants.EIGENLAYER]

    earned_points = []
    for partner in partners:
        point_dist_hist = get_vault_earned_point_by_partner(session, vault, partner)
        if point_dist_hist is not None:
            earned_points.append(
                schemas.EarnedPoints(
                    name=partner,
                    point=point_dist_hist.point,
                    created_at=point_dist_hist.created_at,
                )
            )
        else:
            # add default value 0
            earned_points.append(
                schemas.EarnedPoints(
                    name=partner,
                    point=0.0,
                    created_at=None,
                )
            )

    return earned_points


@router.get("/", response_model=List[schemas.Vault])
async def get_all_vaults(
    session: SessionDep,
    category: VaultCategory = Query(None),
    network_chain: NetworkChain = Query(None),
):
    statement = select(Vault).where(Vault.is_active == True)
    if category or network_chain:
        conditions = []
        if category:
            conditions.append(Vault.category == category)
        if network_chain:
            conditions.append(Vault.network_chain == network_chain)
        statement = statement.where(and_(*conditions))

    vaults = session.exec(statement).all()
    data = []
    for vault in vaults:
        schema_vault = _update_vault_apy(vault)
        if vault.category == VaultCategory.points:
            schema_vault.points = get_earned_points(session, vault)
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
    if vault.category == VaultCategory.points:
        schema_vault.points = get_earned_points(session, vault)
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

    if vault.strategy_name == constants.DELTA_NEUTRAL_STRATEGY:
        pps_history_df["apy"] = pps_history_df["apy_1m"]
    elif vault.strategy_name == constants.OPTIONS_WHEEL_STRATEGY:
        pps_history_df["apy"] = pps_history_df["apy_ytd"]

    # Convert the date column to string format
    pps_history_df["date"] = pps_history_df["date"].dt.strftime("%Y-%m-%dT%H:%M:%S")
    pps_history_df.fillna(0, inplace=True)

    # Convert the DataFrame to a dictionary and return it
    return pps_history_df[["date", "apy"]].to_dict(orient="list")
