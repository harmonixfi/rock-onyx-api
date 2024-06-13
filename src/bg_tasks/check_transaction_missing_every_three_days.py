import logging
from datetime import datetime, timedelta, timezone

import pendulum
import requests
# import seqlog
from dateutil.relativedelta import FR, relativedelta
from sqlmodel import Session, select

from core.config import settings
from core.db import engine
from log import setup_logging_to_file
from models import (PositionStatus, PricePerShareHistory, Transaction,
                    UserPortfolio, Vault)
from models.pps_history import PricePerShareHistory
from models.vault_performance import VaultPerformance
from models.vaults import NetworkChain
from utils.calculate_price import calculate_avg_entry_price

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
START_BLOCK = 0
END_BLOCK = 99999999
OFFSET = 5
THREE_DAYS_AGO = 30 * 24 * 60 * 60
INITIAL_WITHDRAW_METHOD_ID = '0x12edde5e'
COMPLETE_WITHDRAW_METHOD_ID = '0x4f0cb5f3'
DEPOSIT_METHOD_ID = '0xb6b55f25'
DEPOSIT_FUNCTION_NAME_WITH_ADDRESS = 'deposit(uint256 visrDeposit, address from, address to)'
DEPOSIT_FUNCTION_NAME = 'deposit(uint256 amount)'
stablecoin_vault_address = settings.ROCKONYX_STABLECOIN_ADDRESS
delta_neutral_vault_abi = settings.ROCKONYX_DELTA_NEUTRAL_VAULT_ADDRESS
api_key = settings.ARBISCAN_API_KEY
url = settings.ARBISCAN_GET_TRANSACTIONS_URL

session = Session(engine)


def decode_transaction_input(transaction):
    transaction_amount = int(transaction["input"][10:74], 16)
    transaction_amount = transaction_amount / 1e6
    return transaction_amount


def get_transactions(vault_address, page):

    query_params = {
        "address": vault_address,
        "startblock": START_BLOCK,
        "endblock": END_BLOCK,
        "page": page,
        "offset": OFFSET,
        "sort": "asc",
        "apikey": api_key,
    }
    api_url = (
        f"{url}&{'&'.join(f'{key}={value}' for key, value in query_params.items())}"
    )
    response = requests.get(api_url)
    response_json = response.json()
    transactions = response_json["result"]
    return transactions


def check_missing_transactions():

    # query all active vaults
    vaults = session.exec(
        select(Vault)
        .where(Vault.is_active == True)
        .where(Vault.network_chain == NetworkChain.arbitrum_one)
    ).all()

    timestamp_three_days_ago = float(datetime.now().timestamp()) - THREE_DAYS_AGO

    for vault in vaults:
        page = 1

        while True:
            transactions = get_transactions(vault.contract_address, page)
            if transactions == "Max rate limit reached":
                break
            if not transactions:
                break
            
            # check if the last transaction of this page is older than 3 days
            last_transaction = transactions[-1]
            last_transaction_timestamp = float(last_transaction["timeStamp"])
            if last_transaction_timestamp < timestamp_three_days_ago:
                page+=1
                continue
            
            for transaction in transactions:
                transaction_timestamp = float(transaction["timeStamp"])
                if transaction_timestamp < timestamp_three_days_ago:
                    continue
                else:
                    from_address = transaction["from"]
                    transaction_date = pendulum.from_timestamp(
                        int(transaction["timeStamp"]), tz=pendulum.UTC
                    )
                    transaction_date = datetime(
                        transaction_date.year,
                        transaction_date.month,
                        transaction_date.day,
                    )
                    # get price per share from range friday to friday
                    last_friday = transaction_date + relativedelta(weekday=FR(-1))
                    this_thursday = last_friday + timedelta(days=6)

                    history_pps = session.exec(
                        select(PricePerShareHistory)
                        .where(PricePerShareHistory.vault_id == vault.id)
                        .where(PricePerShareHistory.datetime >= last_friday)
                        .where(PricePerShareHistory.datetime <= this_thursday)
                        .order_by(PricePerShareHistory.datetime.desc())
                    ).first()

                    if history_pps is not None:
                        history_pps = history_pps[0].price_per_share
                    else:
                        history_pps = 1

                    user_portfolio = session.exec(
                        select(UserPortfolio)
                        .where(UserPortfolio.user_address == from_address)
                        .where(UserPortfolio.vault_id == vault.id)
                        .where(UserPortfolio.status == PositionStatus.ACTIVE)
                    ).first()


                    if transaction['functionName'] == DEPOSIT_FUNCTION_NAME or transaction['functionName'] == DEPOSIT_FUNCTION_NAME_WITH_ADDRESS and transaction['isError'] == '0':
                        if transaction["from"] == '0x4df74787bc8a9fb8925f8c2ba4df9d4203fc101ad48262214d825d29da36487a':
                            print("Transaction: ", transaction)
                        transaction_hash = transaction["hash"]
                        existing_transaction = session.exec(
                            select(Transaction).where(
                                Transaction.txhash == transaction_hash
                            )
                        ).first()
                        if existing_transaction is None:
                            trx = Transaction(
                                txhash=transaction_hash,
                            )
                            session.add(trx)
                            value = decode_transaction_input(transaction)
                            if user_portfolio is None:
                                # Create new user_portfolio for this user address
                                user_portfolio = UserPortfolio(
                                    vault_id=vault.id,
                                    user_address=from_address,
                                    total_balance=value,
                                    init_deposit=value,
                                    entry_price=history_pps,
                                    pnl=0,
                                    status=PositionStatus.ACTIVE,
                                    trade_start_date=datetime.now(timezone.utc),
                                    total_shares=value / history_pps,
                                )

                                session.add(user_portfolio)
                                session.commit()
                                logger.info(
                                    f"User with address {from_address} added to user_portfolio table"
                                )
                            else:
                                # Update the user_portfolio
                                user_portfolio.total_balance += value
                                user_portfolio.init_deposit += value
                                user_portfolio.entry_price = calculate_avg_entry_price(
                                    user_portfolio, history_pps, value
                                )
                                user_portfolio.total_shares += value / history_pps
                                
                                session.add(user_portfolio)
                                session.commit()
                                logger.info(
                                    f"User with address {from_address} updated in user_portfolio table"
                                )
                        else:
                            logger.info(
                                f"Transaction with txhash {transaction_hash} already exists"
                            )
                    elif transaction["methodId"] == INITIAL_WITHDRAW_METHOD_ID and transaction['isError'] == '0':
                        if user_portfolio is None:
                            logger.info(
                                f"User with address {from_address} not found in user_portfolio table for initial withdraw"
                            )
                            continue
                        transaction_hash = transaction["hash"]
                        existing_transaction = session.exec(
                            select(Transaction).where(
                                Transaction.txhash == transaction_hash
                            )
                        ).first()
                        if existing_transaction is None:
                            trx = Transaction(
                                txhash=transaction_hash,
                            )
                            session.add(trx)
                            value = decode_transaction_input(transaction)
                            # Update the user_portfolio
                            if user_portfolio.pending_withdrawal is None:
                                user_portfolio.pending_withdrawal = value
                            else:
                                user_portfolio.pending_withdrawal += value
                            user_portfolio.initiated_withdrawal_at = datetime.now(timezone.utc)
                            user_portfolio.init_deposit -= value

                            session.add(user_portfolio)
                            session.commit()
                            logger.info(
                                f"User with address {from_address} updated in user_portfolio table")
                        else:
                            logger.info(
                                f"Transaction with txhash {transaction_hash} already exists"
                            )
                    elif transaction["methodId"] == COMPLETE_WITHDRAW_METHOD_ID and transaction['isError'] == '0':
                        if user_portfolio is None:
                            logger.info(
                                f"User with address {from_address} not found in user_portfolio table for complete withdraw"
                            )
                            continue
                        transaction_hash = transaction["hash"]
                        existing_transaction = session.exec(
                            select(Transaction).where(
                                Transaction.txhash == transaction_hash
                            )
                        ).first()
                        if existing_transaction is None:
                            trx = Transaction(
                                txhash=transaction_hash,
                            )
                            session.add(trx)
                            value = decode_transaction_input(transaction)
                            # Update the user_portfolio
                            user_portfolio.pending_withdrawal = 0
                            user_portfolio.total_balance -= value
                            if user_portfolio.total_balance <= 0:
                                user_portfolio.status = PositionStatus.CLOSED
                                user_portfolio.trade_end_date = datetime.now(timezone.utc)

                            session.add(user_portfolio)
                            session.commit()
                            logger.info(
                                f"User with address {from_address} updated in user_portfolio table")
                        else:
                            logger.info(
                                f"Transaction with txhash {transaction_hash} already exists"
                            )
            page += 1


if __name__ == "__main__":
    setup_logging_to_file(
        app="check_transaction_missing_every_three_days", level=logging.INFO, logger=logger
    )

    # if settings.SEQ_SERVER_URL is not None or settings.SEQ_SERVER_URL != "":
    #     seqlog.configure_from_file("./config/seqlog.yml")
    
    check_missing_transactions()
