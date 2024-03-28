from typing import List

from fastapi import APIRouter, HTTPException
from sqlmodel import select

import schemas
from api.api_v1.deps import SessionDep
from models import Vault, UserPortfolio
from schemas import Position

router = APIRouter()

@router.get("/{user_address}", response_model=schemas.Portfolio)
async def get_portfolio_info(session: SessionDep, user_address: str):

    statement = select(UserPortfolio).where(
        UserPortfolio.user_address == user_address.lower()
        and UserPortfolio.status == "ACTIVE"
    )
    user_positions = session.exec(statement).all()

    if user_positions is None:
        raise HTTPException(
            status_code=400,
            detail="The data not found in the database.",
        )

    positions: List[Position] = []
    total_balance = 0.0
    for position in user_positions:
        vault = session.exec(select(Vault).where(Vault.id == position.vault_id)).one()
        position = Position(
            id=position.id,
            vault_id=position.vault_id,
            user_address=position.user_address,
            total_balance=position.total_balance,
            init_deposit=position.init_deposit,
            entry_price=position.entry_price,
            pnl=position.pnl,
            status=position.status,
            trade_start_date=position.trade_start_date,
            pending_withdrawal=position.pending_withdrawal,
            vault_name=vault.name,
            vault_currency=vault.vault_currency,
            current_round=vault.current_round,
            next_close_round_date=vault.next_close_round_date,
            monthly_apy=vault.monthly_apy,
            weekly_apy=vault.weekly_apy,
            slug=vault.slug,
        )
        total_balance += position.total_balance
        positions.append(position)

    total_deposit = sum(position.init_deposit for position in positions)
    pnl = (total_balance / total_deposit - 1) * 100

    portfolio = schemas.Portfolio(
        total_balance=total_balance, pnl=pnl, positions=positions
    )
    return portfolio
