from typing import List

from fastapi import APIRouter, HTTPException
from sqlmodel import select
from web3 import Web3

from core.abi_reader import read_abi
import schemas
from api.api_v1.deps import SessionDep
from models import Vault, UserPortfolio
from schemas import Position
from core.config import settings

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
async def get_portfolio_info(session: SessionDep, user_address: str):

    statement = (
        select(UserPortfolio)
        .where(UserPortfolio.user_address == user_address.lower())
        .where(UserPortfolio.status == "ACTIVE")
    )
    user_positions = session.exec(statement).all()

    if user_positions is None or len(user_positions) == 0:
        portfolio = schemas.Portfolio(total_balance=0, pnl=0, positions=[])
        return portfolio

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

        if vault.contract_address == settings.ROCKONYX_DELTA_NEUTRAL_VAULT_ADDRESS:
            price_per_share = delta_neutral_contract.functions.pricePerShare().call()
            shares = delta_neutral_contract.functions.balanceOf(
                Web3.to_checksum_address(user_address)
            ).call()
        else:
            price_per_share = wheel_options_contract.functions.pricePerShare().call()
            shares = wheel_options_contract.functions.balanceOf(
                Web3.to_checksum_address(user_address)
            ).call()

        shares = shares / 10**6
        price_per_share = price_per_share / 10**6
        position.total_balance = shares * price_per_share
        position.pnl = position.total_balance - position.init_deposit

        total_balance += position.total_balance
        positions.append(position)

    total_deposit = sum(position.init_deposit for position in positions)
    pnl = (total_balance / total_deposit - 1) * 100

    portfolio = schemas.Portfolio(
        total_balance=total_balance, pnl=pnl, positions=positions
    )
    return portfolio
