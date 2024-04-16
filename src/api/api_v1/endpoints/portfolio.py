import datetime
from typing import List

from fastapi import APIRouter, HTTPException, Query
from sqlmodel import select
from web3 import Web3

from bg_tasks.utils import calculate_roi
from core.abi_reader import read_abi
from models.user_portfolio import PositionStatus
import schemas
from api.api_v1.deps import SessionDep
from models import Vault, UserPortfolio
from schemas import Position
from core.config import settings
from utils.json_encoder import custom_encoder

router = APIRouter()

if settings.ENVIRONMENT_NAME == "Production":
    w3 = Web3(Web3.HTTPProvider(settings.ARBITRUM_MAINNET_INFURA_URL))
else:
    w3 = Web3(Web3.HTTPProvider(settings.SEPOLIA_TESTNET_INFURA_URL))

rockonyx_stablecoin_vault_abi = read_abi("RockOnyxStableCoin")
wheel_options_contract = w3.eth.contract(
    address=settings.ROCKONYX_STABLECOIN_ADDRESS, abi=rockonyx_stablecoin_vault_abi
)

rockonyx_delta_neutral_vault_abi = read_abi("RockOnyxDeltaNeutralVault")
delta_neutral_contract = w3.eth.contract(
    address=settings.ROCKONYX_DELTA_NEUTRAL_VAULT_ADDRESS,
    abi=rockonyx_delta_neutral_vault_abi,
)


@router.get("/{user_address}", response_model=schemas.Portfolio)
async def get_portfolio_info(
    session: SessionDep,
    user_address: str,
    vault_id: str = Query(
        None, description="Vault Id"
    ),
):
    statement = (
        select(UserPortfolio)
        .where(UserPortfolio.user_address == user_address.lower())
        .where(UserPortfolio.status == PositionStatus.ACTIVE)
    )
    if vault_id:
        statement.where(UserPortfolio.vault_id == vault_id)
    
    user_positions = session.exec(statement).all()

    if user_positions is None or len(user_positions) == 0:
        portfolio = schemas.Portfolio(total_balance=0, pnl=0, positions=[])
        return portfolio

    positions: List[Position] = []
    total_balance = 0.0
    for pos in user_positions:
        vault = session.exec(select(Vault).where(Vault.id == pos.vault_id)).one()

        position = Position(
            id=pos.id,
            vault_id=pos.vault_id,
            user_address=pos.user_address,
            total_balance=pos.total_balance,
            init_deposit=pos.init_deposit,
            entry_price=pos.entry_price,
            pnl=pos.pnl,
            status=pos.status,
            pending_withdrawal=pos.pending_withdrawal,
            vault_name=vault.name,
            vault_currency=vault.vault_currency,
            current_round=vault.current_round,
            monthly_apy=vault.monthly_apy,
            weekly_apy=vault.weekly_apy,
            slug=vault.slug,
            initiated_withdrawal_at=custom_encoder(pos.initiated_withdrawal_at),
        )

        if vault.contract_address == settings.ROCKONYX_DELTA_NEUTRAL_VAULT_ADDRESS:
            price_per_share = delta_neutral_contract.functions.pricePerShare().call()
            shares = delta_neutral_contract.functions.balanceOf(
                Web3.to_checksum_address(user_address)
            ).call()
        else:

            # calculate next Friday from today
            position.next_close_round_date = (
                datetime.datetime.now()
                + datetime.timedelta(days=(4 - datetime.datetime.now().weekday()) % 7)
            ).replace(hour=8, minute=0, second=0)

            price_per_share = wheel_options_contract.functions.pricePerShare().call()
            shares = wheel_options_contract.functions.balanceOf(
                Web3.to_checksum_address(user_address)
            ).call()

        shares = shares / 10**6
        price_per_share = price_per_share / 10**6
        position.total_balance = shares * price_per_share
        position.pnl = position.total_balance - position.init_deposit

        holding_period = (datetime.datetime.now() - pos.trade_start_date).days
        position.apy = calculate_roi(
            position.total_balance,
            position.init_deposit,
            days=holding_period if holding_period > 0 else 1,
        )
        position.apy *= 100

        total_balance += position.total_balance

        # encode datetime
        position.trade_start_date = custom_encoder(pos.trade_start_date)
        position.next_close_round_date = custom_encoder(vault.next_close_round_date)

        positions.append(position)

    total_deposit = sum(position.init_deposit for position in positions)
    pnl = (total_balance / total_deposit - 1) * 100

    portfolio = schemas.Portfolio(
        total_balance=total_balance, pnl=pnl, positions=positions
    )
    return portfolio
