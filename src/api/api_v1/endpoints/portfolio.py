from typing import List
from uuid import UUID

from fastapi import APIRouter, HTTPException
import pandas as pd
from sqlmodel import select

from models.user_portfolio import PositionStatus
import schemas
from api.api_v1.deps import SessionDep
from models import Vault, UserPortfolio
from models.pps_history import PricePerShareHistory
from models.vault_performance import VaultPerformance
from schemas import Position
from utils.slug import slugify
router = APIRouter()

@router.get("/", response_model=schemas.Portfolio)
async def get_all_portfolios(session: SessionDep):

    statement = select(UserPortfolio).where(UserPortfolio.status == PositionStatus.ACTIVE)
    userportfolios = session.exec(statement).all()
    positions = []
    total_balance = 0.0
    for userportfolio in userportfolios:
        vault = session.exec(select(Vault).where(Vault.id == userportfolio.vault_id)).one()
        position = Position(
            id=userportfolio.id,
            vault_id=userportfolio.vault_id,
            user_address=userportfolio.user_address,
            total_balance=userportfolio.total_balance,
            init_deposit=userportfolio.init_deposit,
            entry_price=userportfolio.entry_price,
            pnl=userportfolio.pnl,
            status=userportfolio.status,
            trade_start_date=userportfolio.trade_start_date,
            pending_withdrawal=userportfolio.pending_withdrawal,
            vault_name=vault.name,
            vault_currency=vault.vault_currency,
            current_round=vault.current_round,
            next_close_round_date=vault.next_close_round_date,
            monthly_apy=vault.monthly_apy,
            weekly_apy=vault.weekly_apy,
            slug=slugify(vault.name)
        )
        total_balance += userportfolio.total_balance
        positions.append(position)

    portfolio = schemas.Portfolio(
        total_balance=total_balance,
        positions=positions
    )  
    return portfolio

@router.get("/{user_address}", response_model=schemas.Portfolio)
async def get_portfolio_info(session: SessionDep, user_address: str):
    statement = select(UserPortfolio).where(UserPortfolio.user_address == user_address and UserPortfolio.status == "ACTIVE")
    userportfolios = session.exec(statement).all()

    if userportfolios is None:
        raise HTTPException(
            status_code=400,
            detail="The data not found in the database.",
        )

    positions = []
    total_balance = 0.0
    for userportfolio in userportfolios:
        vault = session.exec(select(Vault).where(Vault.id == userportfolio.vault_id)).one()
        position = Position(
            id=userportfolio.id,
            vault_id=userportfolio.vault_id,
            user_address=userportfolio.user_address,
            total_balance=userportfolio.total_balance,
            init_deposit=userportfolio.init_deposit,
            entry_price=userportfolio.entry_price,
            pnl=userportfolio.pnl,
            status=userportfolio.status,
            trade_start_date=userportfolio.trade_start_date,
            pending_withdrawal=userportfolio.pending_withdrawal,
            vault_name=vault.name,
            vault_currency=vault.vault_currency,
            current_round=vault.current_round,
            next_close_round_date=vault.next_close_round_date,
            monthly_apy=vault.monthly_apy,
            weekly_apy=vault.weekly_apy,
            slug=slugify(vault.name)
        )
        total_balance += userportfolio.total_balance
        positions.append(position)
    portfolio = schemas.Portfolio(
        total_balance=total_balance,
        positions=positions
    )
    return portfolio