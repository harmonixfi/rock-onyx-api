# import dependencies
import asyncio
from datetime import datetime, timezone

from sqlalchemy import select
from sqlmodel import Session
from web3 import Web3

from core.db import engine
from core.config import settings
from models import PricePerShareHistory, UserPortfolio, Vault, PositionStatus

# filter through blocks and look for transactions involving this address
w3 = Web3(Web3.WebsocketProvider("ws://localhost:8545"))

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
            trade_start_date=datetime.now(tz=timezone.utc),
        )
        session.add(user_portfolio)
    else:
        # Update the user_portfolio
        user_portfolio = user_portfolio[0]
        user_portfolio.total_balance += value
        user_portfolio.init_deposit += value

    session.commit()


async def log_loop(event_filter, poll_interval):
    while True:
        try:
            # Add a timeout to the get_new_entries() method
            events = event_filter.get_new_entries()
            for event in events:
                print(event)
                handle_event(event, "Deposit")
        except asyncio.TimeoutError:
            # If a timeout occurs, just ignore it and continue with the next iteration
            continue
        await asyncio.sleep(poll_interval)


def main():
    deposit_event_filter = w3.eth.filter(
        {
            "address": settings.ROCKONYX_STABLECOIN_ADDRESS,
            "topics": [
                "0x73a19dd210f1a7f902193214c0ee91dd35ee5b4d920cba8d519eca65a7b488ca"
            ],
        }
    )
    loop = asyncio.get_event_loop()

    try:
        loop.run_until_complete(
            asyncio.gather(
                log_loop(deposit_event_filter, 2),
            )
        )
    finally:
        loop.close()


main()
