# import dependencies
import asyncio
from datetime import datetime, timezone

from sqlalchemy import select
from sqlmodel import Session
from web3 import Web3

from core.db import engine
from core.config import settings
from models import PricePerShareHistory, UserPortfolio, Vault, PositionStatus
from datetime import datetime, timezone
import logging
# Initialize logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# filter through blocks and look for transactions involving this address
if settings.ENVIRONMENT_NAME == "Prodcution":
    w3 = Web3(Web3.HTTPProvider(settings.ARBITRUM_MAINNET_INFURA_URL))
else:
    w3 = Web3(Web3.HTTPProvider(settings.SEPOLIA_TESTNET_INFURA_URL))

session = Session(engine)


def handle_event(entry, eventName):
    # Decode the data field
    data = entry["data"].hex()
    value = int(data[2:66], 16) / 1e6
    shares = int("0x" + data[66:], 16) / 1e6

    # Decode the from address
    from_address = f'0x{entry["topics"][1].hex()[26:]}'

    # Get the vault with ROCKONYX_ADDRESS
    vault = session.exec(
        select(Vault).where(
            Vault.contract_address == settings.ROCKONYX_STABLECOIN_ADDRESS
        )
    ).first()
    if vault is None:
        raise ValueError("Vault not found")
    
    vault = vault[0]

    # Get the latest pps from pps_history table
    latest_pps = session.exec(
        select(PricePerShareHistory).order_by(PricePerShareHistory.datetime.desc())
    ).first()
    if latest_pps is not None:
        latest_pps = latest_pps[0].price_per_share
    else:
        latest_pps = 1

    # Check if user with from_address has position in user_portfolio table
    user_portfolio = session.exec(
        select(UserPortfolio).where(UserPortfolio.user_address == from_address)
    ).first()
    if eventName == "Deposit":
        if user_portfolio is None:
            # Create new user_portfolio for this user address
            user_portfolio = UserPortfolio(
                vault_id=vault.id,
                user_address=from_address,
                total_balance=value,
                init_deposit=value,
                entry_price=latest_pps,
                pnl=0,
                status=PositionStatus.ACTIVE,
                trade_start_date=datetime.now(timezone.utc),
            )
            session.add(user_portfolio)
        else:
            # Update the user_portfolio
            user_portfolio = user_portfolio[0]
            user_portfolio.total_balance += value
            user_portfolio.init_deposit += value
            session.add(user_portfolio)

    elif eventName == "Withdraw":
        if user_portfolio is not None:
            user_portfolio = user_portfolio[0]
            user_portfolio.total_balance -= value
            if user_portfolio.total_balance <= 0:
                user_portfolio.status = PositionStatus.CLOSED
                user_portfolio.trade_end_date = datetime.now(timezone.utc)
            session.add(user_portfolio)
        else:
            logger.error(f"User with address {from_address} not found in user_portfolio table")

    else:
        pass

    session.commit()


async def log_loop(event_filter, poll_interval, eventName):
    while True:
        try:
            # Add a timeout to the get_new_entries() method
            events = event_filter.get_new_entries()
            for event in events:
                if eventName == "Deposit":
                    handle_event(event, "Deposit")
                elif eventName == "Withdraw":
                    handle_event(event, "Withdraw")
        except asyncio.TimeoutError:
            # If a timeout occurs, just ignore it and continue with the next iteration
            continue
        await asyncio.sleep(poll_interval)


def main():
    deposit_event_filter = w3.eth.filter(
        {
            "address": settings.VAULT_FILTER_ADDRESS,
            "topics": [
                settings.DEPOSIT_VAULT_FILTER_TOPICS
            ],
        }
    )
    withdraw_event_filter = w3.eth.filter(
        {
            "address": settings.VAULT_FILTER_ADDRESS,
            "topics": [
                settings.DEPOSIT_VAULT_FILTER_TOPICS
            ],
        }
    )
    loop = asyncio.get_event_loop()

    try:
        loop.run_until_complete(
            asyncio.gather(
                log_loop(deposit_event_filter, 2, "Deposit"),
                log_loop(withdraw_event_filter, 2, "Withdraw"),
            )
        )
    finally:
        loop.close()


main()
