from typing import List

from fastapi import APIRouter, HTTPException
import pandas as pd
from sqlmodel import select

from models.pps_history import PricePerShareHistory
from models.user_portfolio import UserPortfolio
from models.vault_performance import VaultPerformance
import schemas
from api.api_v1.deps import SessionDep
from models import Vault

router = APIRouter()

@router.get("/", response_model=List[schemas.Statistics])
async def get_all_statistics(session: SessionDep):
    statement = select(Vault)
    vaults = session.exec(statement).all()
    data = []
    for vault in vaults:
        vault_id = vault.id
        #select where datatime lasted
        statement = (select(VaultPerformance)
            .where(VaultPerformance.vault_id == vault_id)
            .where(VaultPerformance.datetime == select(VaultPerformance.datetime).order_by(VaultPerformance.datetime.desc()).limit(1))
        )
        performances = session.exec(statement).first()
        if not performances:
            continue
        statement = (select(PricePerShareHistory)
            .where(PricePerShareHistory.vault_id == vault_id)
            .order_by(PricePerShareHistory.datetime.desc()).limit(1)
        )
        pps = session.exec(statement).first()
        if not pps:
            continue
        statement = (select(UserPortfolio)
            .where(UserPortfolio.vault_id == vault_id)
        )
        portfolios = session.exec(statement).all()
        statement = (select(PricePerShareHistory)
                     .where(PricePerShareHistory.vault_id == vault_id)
                    .order_by(PricePerShareHistory.price_per_share.desc()).limit(1)
                        )
        all_time_high_per_share = session.exec(statement).first()
        statistic = schemas.Statistics(
            price_per_share = pps.price_per_share,
            apy_1y = 0,
            total_value_locked = performances.total_locked_value,
            risk_factor = 0,
            unique_depositors = len(portfolios),
            fee_structure = "None",
            vault_address = vault.contract_address,
            manager_address = "None",
            all_time_high_per_share = all_time_high_per_share.price_per_share,
            total_shares = 0,
            sortino_ratio = 0,
            downside_risk = 0,
            earned_fee = 0
        )
    data.append(statistic)
    return data