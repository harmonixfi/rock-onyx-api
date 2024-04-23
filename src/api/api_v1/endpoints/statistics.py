import json
from typing import List

from fastapi import APIRouter, HTTPException
from sqlmodel import select

from bg_tasks.utils import calculate_pps_statistics
from models.pps_history import PricePerShareHistory
from models.user_portfolio import UserPortfolio
from models.vault_performance import VaultPerformance
import schemas
from api.api_v1.deps import SessionDep
from models import Vault

router = APIRouter()

@router.get("/{vault_id}", response_model=schemas.Statistics)
async def get_all_statistics(session: SessionDep, vault_id: str):

    statement = (select(Vault)
        .where(Vault.id == vault_id)
    )
    vault = session.exec(statement).first()

    statement = (select(VaultPerformance)
        .where(VaultPerformance.vault_id == vault_id)
        .order_by(VaultPerformance.datetime.desc())
    )
    performances = session.exec(statement).first()

    statement = (select(UserPortfolio)
        .where(UserPortfolio.vault_id == vault_id)
    )
    portfolios = session.exec(statement).all()

    pps_history = session.exec(
        select(PricePerShareHistory)
        .where(PricePerShareHistory.vault_id == vault_id)
        .order_by(PricePerShareHistory.datetime.desc())
    ).first()
    last_price_per_share = pps_history.price_per_share
    statistic = schemas.Statistics(
        name = vault.name,
        price_per_share = last_price_per_share,
        apy_1y = performances.apy_ytd,
        total_value_locked = performances.total_locked_value,
        risk_factor = performances.risk_factor,
        unique_depositors = len(portfolios),
        fee_structure = json.loads(performances.fee_structure),
        vault_address = vault.contract_address,
        manager_address = "0x20f89bA1B0Fc1e83f9aEf0a134095Cd63F7e8CC7",
        all_time_high_per_share = performances.all_time_high_per_share,
        total_shares = performances.total_shares,
        sortino_ratio= performances.sortino_ratio,
        downside_risk = performances.downside_risk,
        earned_fee = performances.earned_fee
    )
    return statistic

@router.get("/", response_model=schemas.Dashboard)
async def get_dashboard_statistics(session: SessionDep):
    statement = select(Vault)
    vaults = session.exec(statement).all()
    data = []
    tvl_in_all_vaults = 0
    tvl_composition = {}
    for vault in vaults:
        statement = (select(VaultPerformance)
            .where(VaultPerformance.vault_id == vault.id)
            .order_by(VaultPerformance.datetime.desc())
        )
        performances = session.exec(statement).first()

        pps_history = session.exec(
            select(PricePerShareHistory)
            .where(PricePerShareHistory.vault_id == vault.id)
            .order_by(PricePerShareHistory.datetime.desc())
        ).first()
        last_price_per_share = pps_history.price_per_share

        statistic = schemas.Vault_Dashboard(
            name = vault.name,
            price_per_share = last_price_per_share,
            apy_1y = performances.apy_ytd,
            risk_factor = performances.risk_factor,
            total_value_locked = performances.total_locked_value,
            vault_address = vault.contract_address,
            slug=vault.slug,
            id=vault.id
        )
        tvl_in_all_vaults += performances.total_locked_value
        tvl_composition[vault.slug] = performances.total_locked_value
        data.append(statistic)

    for key in tvl_composition:
        tvl_composition[key] = tvl_composition[key]/tvl_in_all_vaults
    data = schemas.Dashboard(
        tvl_in_all_vaults=tvl_in_all_vaults,
        tvl_composition=tvl_composition,
        vaults=data
    )
    return data
