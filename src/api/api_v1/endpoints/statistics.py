import json
from typing import List

from fastapi import APIRouter, HTTPException
from sqlmodel import select
from models.pps_history import PricePerShareHistory
from models.user_portfolio import UserPortfolio
from models.vault_performance import VaultPerformance
import schemas
import pandas as pd
from api.api_v1.deps import SessionDep
from models import Vault
from core.config import settings

router = APIRouter()


@router.get("/{vault_id}", response_model=schemas.Statistics)
async def get_all_statistics(session: SessionDep, vault_id: str):

    statement = select(Vault).where(Vault.id == vault_id)
    vault = session.exec(statement).first()

    statement = (
        select(VaultPerformance)
        .where(VaultPerformance.vault_id == vault_id)
        .order_by(VaultPerformance.datetime.desc())
    )
    performances = session.exec(statement).first()
    if performances is None:
        raise HTTPException(
            status_code=400,
            detail="The performances data not found in the database.",
        )

    statement = select(UserPortfolio).where(UserPortfolio.vault_id == vault_id)
    portfolios = session.exec(statement).all()

    pps_history = session.exec(
        select(PricePerShareHistory)
        .where(PricePerShareHistory.vault_id == vault_id)
        .order_by(PricePerShareHistory.datetime.desc())
    ).first()
    last_price_per_share = pps_history.price_per_share
    statistic = schemas.Statistics(
        name=vault.name,
        price_per_share=last_price_per_share,
        apy_1y=(
            performances.apy_ytd
            if vault.contract_address == settings.ROCKONYX_STABLECOIN_ADDRESS
            else performances.apy_1m
        ),
        total_value_locked=performances.total_locked_value,
        risk_factor=performances.risk_factor,
        unique_depositors=len(portfolios),
        fee_structure=json.loads(performances.fee_structure),
        vault_address=vault.contract_address,
        manager_address=settings.OWNER_WALLET_ADDRESS,
        all_time_high_per_share=performances.all_time_high_per_share,
        total_shares=performances.total_shares,
        sortino_ratio=performances.sortino_ratio,
        downside_risk=performances.downside_risk,
        earned_fee=performances.earned_fee,
        slug=vault.slug,
    )
    return statistic


@router.get("/", response_model=schemas.Dashboard)
async def get_dashboard_statistics(session: SessionDep):
    statement = select(Vault).where(Vault.strategy_name != None)
    vaults = session.exec(statement).all()
    data = []
    tvl_in_all_vaults = 0
    tvl_composition = {}
    for vault in vaults:
        statement = (
            select(VaultPerformance)
            .where(VaultPerformance.vault_id == vault.id)
            .order_by(VaultPerformance.datetime.desc())
        )
        performances = session.exec(statement).first()

        pps_history = session.exec(
            select(PricePerShareHistory)
            .where(PricePerShareHistory.vault_id == vault.id)
            .order_by(PricePerShareHistory.datetime.desc())
        ).first()

        last_price_per_share = pps_history.price_per_share if pps_history else 0

        statistic = schemas.Vault_Dashboard(
            name=vault.name,
            price_per_share=last_price_per_share,
            apy_1y=(
                performances.apy_ytd
                if vault.contract_address == settings.ROCKONYX_STABLECOIN_ADDRESS
                else performances.apy_1m
            ),
            risk_factor=performances.risk_factor,
            total_value_locked=performances.total_locked_value,
            vault_address=vault.contract_address,
            slug=vault.slug,
            id=vault.id,
        )
        tvl_in_all_vaults += performances.total_locked_value
        tvl_composition[vault.slug] = performances.total_locked_value
        data.append(statistic)

    for key in tvl_composition:
        tvl_composition[key] = (
            tvl_composition[key] / tvl_in_all_vaults if tvl_in_all_vaults > 0 else 0
        )

    data = schemas.Dashboard(
        tvl_in_all_vaults=tvl_in_all_vaults,
        tvl_composition=tvl_composition,
        vaults=data,
    )
    return data


@router.get("/{vault_id}/tvl-history")
async def get_vault_performance(session: SessionDep, vault_id: str):
    # Get the VaultPerformance records for the given vault_id
    statement = select(Vault).where(Vault.id == vault_id)
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
        return {"date": [], "tvl": []}

    # Convert the list of VaultPerformance objects to a DataFrame
    pps_history_df = pd.DataFrame([vars(rec) for rec in perf_hist])

    # Rename the datetime column to date
    pps_history_df.rename(columns={"datetime": "date"}, inplace=True)

    pps_history_df["tvl"] = pps_history_df["total_locked_value"]

    # Convert the date column to string format
    pps_history_df["date"] = pps_history_df["date"].dt.strftime("%Y-%m-%dT%H:%M:%S")
    pps_history_df.fillna(0, inplace=True)

    # Convert the DataFrame to a dictionary and return it
    return pps_history_df[["date", "tvl"]].to_dict(orient="list")
