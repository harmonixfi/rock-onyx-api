# import dependencies
import asyncio
from datetime import datetime, timezone
import traceback

from sqlalchemy import select
from sqlmodel import Session
from web3 import Web3
from websockets import ConnectionClosedError

from core.db import engine
from core.config import settings
from log import setup_logging_to_file
from models import PricePerShareHistory, UserPortfolio, Vault, PositionStatus
from datetime import datetime, timezone
import logging

# # Initialize logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def init_web3():
    # filter through blocks and look for transactions involving this address
    if settings.ENVIRONMENT_NAME == "Production":
        w3 = Web3(
            Web3.WebsocketProvider(settings.ARBITRUM_MAINNET_INFURA_WEBSOCKER_URL)
        )
    else:
        w3 = Web3(Web3.WebsocketProvider(settings.SEPOLIA_TESTNET_INFURA_WEBSOCKER_URL))

    return w3


w3 = init_web3()
session = Session(engine)


def _extract_stablecoin_event(entry):
    # Decode the data field
    data = entry["data"].hex()
    value = int(data[2:66], 16) / 1e6
    shares = int("0x" + data[66:], 16) / 1e6

    # Decode the from address
    from_address = f'0x{entry["topics"][1].hex()[26:]}'
    return value, shares, from_address


def _extract_delta_neutral_event(entry):
    # Parse the account parameter from the topics field
    from_address = f'0x{entry["topics"][1].hex()[26:]}'
    # Parse the amount and shares parameters from the data field
    data = entry["data"].hex()
    amount = int(data[2:66], 16) / 1e6
    shares = int(data[66 : 66 + 64], 16) / 1e6
    return amount, shares, from_address


def handle_event(vault_address: str, entry, eventName):
    # Get the vault with ROCKONYX_ADDRESS
    vault = session.exec(
        select(Vault).where(Vault.contract_address == vault_address)
    ).first()

    if vault is None:
        raise ValueError("Vault not found")

    vault: Vault = vault[0]
    logger.info(f"Processing event {eventName} for vault {vault_address} {vault.name}")

    # Get the latest pps from pps_history table
    latest_pps = session.exec(
        select(PricePerShareHistory)
        .where(PricePerShareHistory.vault_id == vault.id)
        .order_by(PricePerShareHistory.datetime.desc())
    ).first()
    if latest_pps is not None:
        latest_pps = latest_pps[0].price_per_share
    else:
        latest_pps = 1

    # Extract the value, shares and from_address from the event
    if vault_address == settings.ROCKONYX_STABLECOIN_ADDRESS:
        value, _, from_address = _extract_stablecoin_event(entry)
    elif vault_address == settings.ROCKONYX_DELTA_NEUTRAL_VAULT_ADDRESS:
        value, _, from_address = _extract_delta_neutral_event(entry)
    else:
        raise ValueError("Invalid vault address")

    logger.info(f"Value: {value}, from_address: {from_address}")

    # Check if user with from_address has position in user_portfolio table
    user_portfolio = session.exec(
        select(UserPortfolio)
        .where(UserPortfolio.user_address == from_address)
        .where(UserPortfolio.vault_id == vault.id)
        .where(UserPortfolio.status == PositionStatus.ACTIVE)
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
            logger.info(
                f"User with address {from_address} added to user_portfolio table"
            )
        else:
            # Update the user_portfolio
            user_portfolio = user_portfolio[0]
            user_portfolio.total_balance += value
            user_portfolio.init_deposit += value
            session.add(user_portfolio)
            logger.info(
                f"User with address {from_address} updated in user_portfolio table"
            )

    elif eventName == "InitiateWithdraw":
        if user_portfolio is not None:
            user_portfolio = user_portfolio[0]
            if user_portfolio.pending_withdrawal is None:
                user_portfolio.pending_withdrawal = value
            else:
                user_portfolio.pending_withdrawal += value

            user_portfolio.initiated_withdrawal_at = datetime.now(timezone.utc)
            session.add(user_portfolio)
            logger.info(
                f"User with address {from_address} updated in user_portfolio table"
            )
        else:
            logger.info(
                f"User with address {from_address} not found in user_portfolio table"
            )

    elif eventName == "Withdrawn":
        if user_portfolio is not None:
            user_portfolio = user_portfolio[0]
            user_portfolio.total_balance -= value
            if user_portfolio.total_balance <= 0:
                user_portfolio.status = PositionStatus.CLOSED
                user_portfolio.trade_end_date = datetime.now(timezone.utc)

            session.add(user_portfolio)
            logger.info(
                f"User with address {from_address} updated in user_portfolio table"
            )
        else:
            logger.info(
                f"User with address {from_address} not found in user_portfolio table"
            )

    else:
        pass

    session.commit()


async def log_loop(vault_address, event_filter, poll_interval, eventName):
    while True:
        try:
            # Add a timeout to the get_new_entries() method
            events = event_filter.get_new_entries()
            for event in events:
                try:
                    handle_event(vault_address, event, eventName)
                except Exception as e:
                    logger.error(e)
                    logger.error(traceback.format_exc())
        except asyncio.TimeoutError:
            # If a timeout occurs, just ignore it and continue with the next iteration
            continue
        except Exception as e:
            raise e

        await asyncio.sleep(poll_interval)


# Create event filters for the stablecoin vault
def create_event_filter():
    wheel_deposit_event_filter = w3.eth.filter(
        {
            "address": settings.ROCKONYX_STABLECOIN_ADDRESS,
            "topics": [settings.STABLECOIN_DEPOSIT_VAULT_FILTER_TOPICS],
        }
    )
    # wheel_init_withdraw_event_filter = w3.eth.filter(
    #     {
    #         "address": settings.ROCKONYX_STABLECOIN_ADDRESS,
    #         "topics": [settings.STABLECOIN_INITIATE_WITHDRAW_VAULT_FILTER_TOPICS],
    #     }
    # )
    wheel_complete_withdraw_event_filter = w3.eth.filter(
        {
            "address": settings.ROCKONYX_STABLECOIN_ADDRESS,
            "topics": [settings.STABLECOIN_COMPLETE_WITHDRAW_VAULT_FILTER_TOPICS],
        }
    )

    delta_neutral_deposit_event_filter = w3.eth.filter(
        {
            "address": settings.ROCKONYX_DELTA_NEUTRAL_VAULT_ADDRESS,
            "topics": [settings.DELTA_NEUTRAL_DEPOSIT_EVENT_TOPIC],
        }
    )
    delta_neutral_init_withdraw_event_filter = w3.eth.filter(
        {
            "address": settings.ROCKONYX_DELTA_NEUTRAL_VAULT_ADDRESS,
            "topics": [settings.DELTA_NEUTRAL_INITIATE_WITHDRAW_EVENT_TOPIC],
        }
    )
    delta_neutral_complete_withdraw_event_filter = w3.eth.filter(
        {
            "address": settings.ROCKONYX_DELTA_NEUTRAL_VAULT_ADDRESS,
            "topics": [settings.DELTA_NEUTRAL_COMPLETE_WITHDRAW_EVENT_TOPIC],
        }
    )
    return (
        wheel_deposit_event_filter,
        # wheel_init_withdraw_event_filter,
        wheel_complete_withdraw_event_filter,
        delta_neutral_deposit_event_filter,
        delta_neutral_init_withdraw_event_filter,
        delta_neutral_complete_withdraw_event_filter,
    )


async def main():
    global w3

    while True:
        try:
            (
                wheel_deposit_event_filter,
                # wheel_init_withdraw_event_filter,
                wheel_complete_withdraw_event_filter,
                delta_neutral_deposit_event_filter,
                delta_neutral_init_withdraw_event_filter,
                delta_neutral_complete_withdraw_event_filter,
            ) = create_event_filter()

            await asyncio.gather(
                asyncio.create_task(
                    log_loop(
                        settings.ROCKONYX_STABLECOIN_ADDRESS,
                        wheel_deposit_event_filter,
                        20,
                        "Deposit",
                    )
                ),
                # asyncio.create_task(
                #     log_loop(
                #         settings.ROCKONYX_STABLECOIN_ADDRESS,
                #         wheel_init_withdraw_event_filter,
                #         20,
                #         "InitiateWithdraw",
                #     )
                # ),
                asyncio.create_task(
                    log_loop(
                        settings.ROCKONYX_STABLECOIN_ADDRESS,
                        wheel_complete_withdraw_event_filter,
                        20,
                        "CompleteWithdraw",
                    )
                ),
                asyncio.create_task(
                    log_loop(
                        settings.ROCKONYX_DELTA_NEUTRAL_VAULT_ADDRESS,
                        delta_neutral_deposit_event_filter,
                        20,
                        "Deposit",
                    )
                ),
                asyncio.create_task(
                    log_loop(
                        settings.ROCKONYX_DELTA_NEUTRAL_VAULT_ADDRESS,
                        delta_neutral_init_withdraw_event_filter,
                        20,
                        "InitiateWithdraw",
                    )
                ),
                asyncio.create_task(
                    log_loop(
                        settings.ROCKONYX_DELTA_NEUTRAL_VAULT_ADDRESS,
                        delta_neutral_complete_withdraw_event_filter,
                        20,
                        "CompleteWithdraw",
                    )
                ),
            )
        except ConnectionClosedError as e:
            logger.error(f"Connection closed error: {e}")
            w3 = init_web3()
            continue
        except Exception as e:
            logger.error(e)
            if "-32000" in str(e) and "filter not found" in str(e):
                logger.info("Filter not found. Retrying...")
            else:
                logger.info(f"Error occurred: {e}")


if __name__ == "__main__":
    setup_logging_to_file(app="web_listener", level=logging.INFO, logger=logger)
    asyncio.run(main())
