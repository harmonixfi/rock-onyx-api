# import dependencies
import asyncio
from datetime import datetime, timezone
import traceback

from sqlalchemy import select
from sqlmodel import Session
from web3 import Web3
from web3._utils.filters import Filter
from websockets import ConnectionClosedError

from core.db import engine
from core.config import settings
from log import setup_logging_to_file, setup_logging_to_console
from models import (
    PricePerShareHistory,
    UserPortfolio,
    Vault,
    PositionStatus,
    Transaction,
)
from services.socket_manager import WebSocketManager
from utils.calculate_price import calculate_avg_entry_price
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

    from_address = None
    if len(entry["topics"]) >= 2:
        from_address = f'0x{entry["topics"][1].hex()[26:]}'  # For deposit event
    return value, shares, from_address


def _extract_delta_neutral_event(entry):
    # Parse the account parameter from the topics field
    from_address = None
    if len(entry["topics"]) >= 2:
        from_address = f'0x{entry["topics"][1].hex()[26:]}'  # For deposit event
    # Parse the amount and shares parameters from the data field
    data = entry["data"].hex()
    amount = int(data[2:66], 16) / 1e6
    shares = int(data[66 : 66 + 64], 16) / 1e6
    return amount, shares, from_address


def handle_deposit_event(user_portfolio: UserPortfolio, value, from_address, vault: Vault, latest_pps):
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
            total_shares=value / latest_pps,
        )
        session.add(user_portfolio)
        logger.info(
            f"User with address {from_address} added to user_portfolio table"
        )
    else:
        # Update the user_portfolio
        user_portfolio: UserPortfolio = user_portfolio[0]
        user_portfolio.total_balance += value
        user_portfolio.init_deposit += value
        user_portfolio.entry_price = calculate_avg_entry_price(
            user_portfolio, latest_pps, value
        )
        user_portfolio.total_shares += value / latest_pps
        session.add(user_portfolio)
        logger.info(
            f"User with address {from_address} updated in user_portfolio table"
        )
    return user_portfolio


def handle_initiate_withdraw_event(user_portfolio: UserPortfolio, value, from_address, *args, **kwargs):
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
        return user_portfolio
    else:
        logger.info(
            f"User with address {from_address} not found in user_portfolio table"
        )


def handle_withdrawn_event(user_portfolio: UserPortfolio, value, from_address, *args, **kwargs):
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
        return user_portfolio
    else:
        logger.info(
            f"User with address {from_address} not found in user_portfolio table"
        )


event_handlers = {
    "Deposit": handle_deposit_event,
    "InitiateWithdraw": handle_initiate_withdraw_event,
    "Withdrawn": handle_withdrawn_event,
}


def handle_event(vault_address: str, entry, event_name):
    # Get the vault with ROCKONYX_ADDRESS
    vault = session.exec(
        select(Vault).where(Vault.contract_address == vault_address)
    ).first()

    if vault is None:
        raise ValueError("Vault not found")
    vault: Vault = vault[0]

    transaction = session.exec(
        select(Transaction).where(Transaction.txhash == entry["transactionHash"])
    ).first()
    if transaction is None:
        transaction = Transaction(
            txhash=entry["transactionHash"],
        )
        session.add(transaction)
    else:
        logger.info(
            f"Transaction with txhash {entry['transactionHash']} already exists"
        )
    logger.info(f"Processing event {event_name} for vault {vault_address} {vault.name}")

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

    # Call the appropriate handler based on the event name
    handler = event_handlers[event_name]
    user_portfolio = handler(user_portfolio, vault, value, latest_pps, from_address)

    session.commit()


class Web3Listener(WebSocketManager):
    def __init__(self):
        super().__init__(settings.ARBITRUM_MAINNET_INFURA_WEBSOCKER_URL, logger=logger)

    def init_event_filters(self):
        self.wheel_deposit_event_filter = w3.eth.filter(
            {
                "address": settings.ROCKONYX_STABLECOIN_ADDRESS,
                "topics": [settings.STABLECOIN_DEPOSIT_VAULT_FILTER_TOPICS],
            }
        )
        self.wheel_init_withdraw_event_filter = w3.eth.filter(
            {
                "address": settings.ROCKONYX_STABLECOIN_ADDRESS,
                "topics": [settings.STABLECOIN_INITIATE_WITHDRAW_VAULT_FILTER_TOPICS],
            }
        )
        self.wheel_complete_withdraw_event_filter = w3.eth.filter(
            {
                "address": settings.ROCKONYX_STABLECOIN_ADDRESS,
                "topics": [settings.STABLECOIN_COMPLETE_WITHDRAW_VAULT_FILTER_TOPICS],
            }
        )

        self.delta_neutral_deposit_event_filter = w3.eth.filter(
            {
                "address": settings.ROCKONYX_DELTA_NEUTRAL_VAULT_ADDRESS,
                "topics": [settings.DELTA_NEUTRAL_DEPOSIT_EVENT_TOPIC],
            }
        )
        self.delta_neutral_init_withdraw_event_filter = w3.eth.filter(
            {
                "address": settings.ROCKONYX_DELTA_NEUTRAL_VAULT_ADDRESS,
                "topics": [settings.DELTA_NEUTRAL_INITIATE_WITHDRAW_EVENT_TOPIC],
            }
        )
        self.delta_neutral_complete_withdraw_event_filter = w3.eth.filter(
            {
                "address": settings.ROCKONYX_DELTA_NEUTRAL_VAULT_ADDRESS,
                "topics": [settings.DELTA_NEUTRAL_COMPLETE_WITHDRAW_EVENT_TOPIC],
            }
        )

    async def _process_new_entries(
        self, vault_address: str, event_filter: Filter, event_name: str
    ):
        deposit_events = event_filter.get_new_entries()
        for event in deposit_events:
            await handle_event(vault_address, event, event_name)

    async def handle_events(self):
        await self._process_new_entries(
            settings.ROCKONYX_STABLECOIN_ADDRESS,
            self.wheel_deposit_event_filter,
            "Deposit",
        )
        await self._process_new_entries(
            settings.ROCKONYX_STABLECOIN_ADDRESS,
            self.wheel_init_withdraw_event_filter,
            "InitiateWithdraw",
        )
        await self._process_new_entries(
            settings.ROCKONYX_STABLECOIN_ADDRESS,
            self.wheel_complete_withdraw_event_filter,
            "Withdrawn",
        )

        await self._process_new_entries(
            settings.ROCKONYX_DELTA_NEUTRAL_VAULT_ADDRESS,
            self.delta_neutral_deposit_event_filter,
            "Deposit",
        )
        await self._process_new_entries(
            settings.ROCKONYX_DELTA_NEUTRAL_VAULT_ADDRESS,
            self.delta_neutral_init_withdraw_event_filter,
            "InitiateWithdraw",
        )
        await self._process_new_entries(
            settings.ROCKONYX_DELTA_NEUTRAL_VAULT_ADDRESS,
            self.delta_neutral_complete_withdraw_event_filter,
            "Withdrawn",
        )

    async def listen_for_events(self):
        while True:
            try:
                # subscribe to new block headers
                subscription_id = await self.w3.eth.subscribe(
                    "logs",
                    {"address": settings.ROCKONYX_DELTA_NEUTRAL_VAULT_ADDRESS},
                )
                print(f"Subscription response: {subscription_id}")

                subscription_id = await self.w3.eth.subscribe(
                    "logs",
                    {"address": settings.ROCKONYX_STABLECOIN_ADDRESS},
                )
                print(f"Subscription response: {subscription_id}")

                async for _ in self.read_messages():
                    # Handle the event
                    await self.handle_events()
            except Exception as e:
                logger.error(f"Error: {e}")
                logger.error(traceback.format_exc())

    async def run(self):
        await self.connect()
        self.init_event_filters()

        try:
            await self.listen_for_events()
        except Exception as e:
            logger.error(f"Error: {e}")
            logger.error(traceback.format_exc())
        finally:
            await self.disconnect()


if __name__ == "__main__":
    setup_logging_to_console(level=logging.INFO, logger=logger)
    setup_logging_to_file(app="web_listener", level=logging.INFO, logger=logger)

    web3_listener = Web3Listener()
    asyncio.run(web3_listener.run())
