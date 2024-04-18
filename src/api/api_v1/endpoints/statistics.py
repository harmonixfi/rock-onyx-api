from typing import List

from fastapi import APIRouter, HTTPException
import numpy as np
import pandas as pd
from sqlmodel import select

from models.pps_history import PricePerShareHistory
from models.user_portfolio import UserPortfolio
from models.vault_performance import VaultPerformance
import schemas
from api.api_v1.deps import SessionDep
from models import Vault
from empyrical import sortino_ratio, downside_risk

router = APIRouter()


def calculate_risk_factor(returns):
    # Filter out positive returns
    negative_returns = [r for r in returns if r < 0]

    # Calculate standard deviation of negative returns
    risk_factor = np.std(negative_returns)

    return risk_factor

@router.get("/", response_model=List[schemas.Statistics])
async def get_all_statistics(session: SessionDep):
    statement = select(Vault)
    vaults = session.exec(statement).all()
    data = []
    for vault in vaults:
        vault_id = vault.id
        statement = (select(VaultPerformance)
            .where(VaultPerformance.vault_id == vault_id)
            .where(VaultPerformance.datetime == select(VaultPerformance.datetime).order_by(VaultPerformance.datetime.asc()).limit(1))
        )
        performances = session.exec(statement).first()
        if not performances:
            continue
        statement = (select(PricePerShareHistory)
            .where(PricePerShareHistory.vault_id == vault_id)
            .order_by(PricePerShareHistory.datetime.asc())
        )
        pps = session.exec(statement).all()
        lasted_pps = pps[0]

        df = pd.DataFrame(pps)
        df = df.drop(columns=[0, 1, 2])
        df = df.apply(lambda x: x.astype(str).str.split(',').str[1]).apply(lambda x: x.astype(str).str.replace(')', ''))
        df = df.astype(float).pct_change()

        sortino = sortino_ratio(df, period="weekly")
        downside = downside_risk(df, period="weekly")

        returns = df.values.flatten()
        risk_factor = calculate_risk_factor(returns)

        
        if not lasted_pps:
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
            price_per_share = lasted_pps.price_per_share,
            apy_1y = 0,
            total_value_locked = performances.total_locked_value,
            risk_factor = risk_factor,
            unique_depositors = len(portfolios),
            fee_structure = "None",
            vault_address = vault.contract_address,
            manager_address = "None",
            all_time_high_per_share = all_time_high_per_share.price_per_share,
            total_shares = 0,
            sortino_ratio= float(sortino),
            downside_risk = float(downside),
            earned_fee = 0
        )
    data.append(statistic)
    return data