from core.config import settings
from core.db import engine
from models import Vault
from models.pps_history import PricePerShareHistory
from models.vault_performance import VaultPerformance
import requests
from core.config import settings
import requests
from sqlmodel import Session
from sqlalchemy import select
from models import PricePerShareHistory, UserPortfolio, Vault, PositionStatus, Transaction
import logging
from datetime import datetime, timedelta, timezone
from dateutil.relativedelta import relativedelta, FR
from utils.calculate_price import calculate_avg_entry_price

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
START_BLOCK = 0
END_BLOCK = 99999999
OFFSET = 100
THREE_DAYS_AGO = 30 * 24 * 60 * 60

stablecoin_vault_address = settings.ROCKONYX_STABLECOIN_ADDRESS
delta_neutral_vault_abi = settings.ROCKONYX_DELTA_NEUTRAL_VAULT_ADDRESS
api_key = settings.ARBISCAN_API_KEY
url = settings.ARBISCAN_GET_TRANSACTIONS_URL

session = Session(engine)

def decode_transaction_input(transaction):
    transaction_amount = int(transaction['input'][10:], 16)
    transaction_amount = transaction_amount / 1e6
    return transaction_amount

def get_transactions(vault_address, page):
    api_url = f"{url}&address={vault_address}&startblock={START_BLOCK}&endblock={END_BLOCK}&page={page}&offset={OFFSET}&sort=desc&apikey={api_key}"
    response = requests.get(api_url)
    response_json = response.json()
    transactions = response_json['result']
    return transactions

def check_missing_transactions():
    
    address = [stablecoin_vault_address, delta_neutral_vault_abi]
    timestamp_three_days_ago = float(datetime.now().timestamp()) - THREE_DAYS_AGO
    flag = True

    for vault_address in address:

        vault = session.exec(
            select(Vault).where(Vault.contract_address == vault_address)
        ).first()
        if vault is None:
            raise ValueError("Vault not found")
        vault: Vault = vault[0]

        page = 1
        

        while flag:
            transactions = get_transactions(vault_address, page)
            if transactions == 'Max rate limit reached':
                break

            for transaction in transactions:
                transaction_timestamp = float(transaction['timeStamp'])
                if transaction_timestamp > timestamp_three_days_ago:
                    from_address = transaction['from']

                    transaction_date = datetime.utcfromtimestamp(int(transaction['timeStamp']))
                    transaction_date = datetime(transaction_date.year, transaction_date.month, transaction_date.day)
                    #get price per share from range friday to friday
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

                    if transaction['functionName'] == "deposit(uint256 amount)":
                        transaction_hash = transaction['hash'] 
                        existing_transaction = session.exec(
                            select(Transaction).where(Transaction.txhash == transaction_hash)
                        ).first()
                        if existing_transaction is None:
                            trx = Transaction(
                                txhash=transaction_hash,
                            )
                            session.add(trx)
                            value = decode_transaction_input(transaction)
                            if user_portfolio is None:
                            #Create new user_portfolio for this user address
                                user_portfolio = UserPortfolio(
                                    vault_id=vault.id,
                                    user_address=from_address,
                                    total_balance=value,
                                    init_deposit=value,
                                    entry_price=history_pps,
                                    pnl=0,
                                    status=PositionStatus.ACTIVE,
                                    trade_start_date=datetime.now(timezone.utc),
                                    total_shares=value/history_pps
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
                                user_portfolio.entry_price = calculate_avg_entry_price(user_portfolio, history_pps, value)
                                user_portfolio.total_shares += value/history_pps
                                session.add(user_portfolio)
                                logger.info(
                                    f"User with address {from_address} updated in user_portfolio table"
                                )
                        else:
                            logger.info(f"Transaction with txhash {transaction_hash} already exists")
                else:
                    flag = False
                    break
            page += 1
            if not flag:
                break
    session.commit()


if __name__ == "__main__":
    check_missing_transactions()
