import uuid
from datetime import datetime, timedelta

import pandas as pd
from sqlmodel import Session, select
from web3 import Web3

from core.abi_reader import read_abi
from core.config import settings
from core.db import engine
from models import Vault
from models.pps_history import PricePerShareHistory
from models.vault_performance import VaultPerformance
from services.market_data import get_price

# Connect to the Ethereum network
if( settings.ENVIRONMENT_NAME == "Prodcution"):
    w3 = Web3(Web3.HTTPProvider(settings.ARBITRUM_MAINNET_INFURA_URL))
else:
    w3 = Web3(Web3.HTTPProvider(settings.SEPOLIA_TESTNET_INFURA_URL))
token_abi = read_abi("ERC20")
rockonyx_delta_neutral_vault_abi = read_abi("RockOnyxDeltaNeutralVault")
rockOnyxUSDTVaultContract = w3.eth.contract(
    address=settings.ROCKONYX_DELTA_NEUTRAL_VAULT_ADDRESS, abi=rockonyx_delta_neutral_vault_abi
)

session = Session(engine)


def balance_of(wallet_address, token_address):
    token_contract = w3.eth.contract(address=token_address, abi=token_abi)
    token_balance = token_contract.functions.balanceOf(wallet_address).call()
    return token_balance


def get_price_per_share_history(vault_id: uuid.UUID) -> pd.DataFrame:
    pps_history = session.exec(
        select(PricePerShareHistory)
        .where(PricePerShareHistory.vault_id == vault_id)
        .order_by(PricePerShareHistory.datetime.asc())
    ).all()

    # Convert the list of PricePerShareHistory objects to a DataFrame
    pps_history_df = pd.DataFrame([vars(pps) for pps in pps_history])

    return pps_history_df[["datetime", "price_per_share", "vault_id"]]


def update_price_per_share(vault_id: uuid.UUID, current_price_per_share: float):
    today = datetime.now().date()

    # Check if a PricePerShareHistory record for today already exists
    existing_pps = session.exec(
        select(PricePerShareHistory).where(
            PricePerShareHistory.vault_id == vault_id,
            PricePerShareHistory.datetime == today,
        )
    ).first()

    if existing_pps:
        # If a record for today already exists, update the price per share
        existing_pps.price_per_share = current_price_per_share
    else:
        # If no record for today exists, create a new one
        new_pps = PricePerShareHistory(
            datetime=today, price_per_share=current_price_per_share, vault_id=vault_id
        )
        session.add(new_pps)

    session.commit()


def calculate_roi(after: float, before: float, days: int) -> float:
    # calculate our annualized return for a vault
    pps_delta = (after - before) / (before or 1)
    annualized_roi = (1 + pps_delta) ** (365.2425 / days) - 1
    return annualized_roi


def get_before_price_per_shares(vault_id: uuid.UUID, days: int):
    target_date = datetime.now() - timedelta(days=days)

    # Get the PricePerShareHistory records before the target date and order them by datetime in descending order
    pps_history = session.exec(
        select(PricePerShareHistory)
        .where(
            PricePerShareHistory.vault_id == vault_id,
            PricePerShareHistory.datetime <= target_date,
        )
        .order_by(PricePerShareHistory.datetime.desc())
    ).all()

    # If there are any records, return the price per share of the most recent one
    if pps_history:
        return pps_history[0].price_per_share

    # If there are no records before the target date, return None
    return 1


def get_current_pps():
    pps = rockOnyxUSDTVaultContract.functions.pricePerShare().call()
    return pps / 1e6


def get_current_round():
    current_round = rockOnyxUSDTVaultContract.functions.getCurrentRound().call()
    return current_round


def get_current_tvl():
    tvl = rockOnyxUSDTVaultContract.functions.totalValueLocked().call()

    return tvl / 1e6


def get_next_friday():
    today = datetime.today()
    next_friday = today + timedelta((4 - today.weekday()) % 7)
    next_friday = next_friday.replace(hour=8, minute=0, second=0, microsecond=0)
    return next_friday

def get_next_day():
    today = datetime.today()
    next_day = today + timedelta(1)
    next_day = next_day.replace(hour=8, minute=0, second=0, microsecond=0)
    return next_day

# Step 4: Calculate Performance Metrics
def calculate_performance(vault_id: uuid.UUID):
    current_price = get_price("ETHUSDT")

    # today = datetime.strptime(df["Date"].iloc[-1], "%Y-%m-%d")
    today = datetime.utcnow().strftime("%Y-%m-%d")
    # candles = get_klines("ETHUSDT", end_time=(today + timedelta(days=2)), limit=1)
    # current_price = float(candles[0][4])

    # price_per_share_df = get_price_per_share_history(vault_id)

    current_price_per_share = get_current_pps()
    total_balance = get_current_tvl()

    # Calculate Monthly APY
    month_ago_price_per_share = get_before_price_per_shares(vault_id, days=30)
    monthly_apy = calculate_roi(
        current_price_per_share, month_ago_price_per_share, days=30
    )

    week_ago_price_per_share = get_before_price_per_shares(vault_id, days=7)
    weekly_apy = calculate_roi(
        current_price_per_share, week_ago_price_per_share, days=7
    )

    apys = [monthly_apy, weekly_apy]
    net_apy = next((value for value in apys if value != 0), 0)

    # assume we are compounding every week
    compounding = 52

    # calculate our APR after fees
    apr = compounding * ((net_apy + 1) ** (1 / compounding)) - compounding

    performance_history = session.exec(
        select(VaultPerformance).order_by(VaultPerformance.datetime.asc()).limit(1)
    ).first()

    benchmark = current_price
    benchmark_percentage = ((benchmark / performance_history.benchmark) - 1) * 100
    apy_1m = monthly_apy * 100
    apy_1w = weekly_apy * 100

    # Create a new VaultPerformance object
    performance = VaultPerformance(
        datetime=today,
        total_locked_value=total_balance,
        benchmark=benchmark,
        pct_benchmark=benchmark_percentage,
        apy_1m=apy_1m,
        apy_1w=apy_1w,
        vault_id=vault_id,
    )
    update_price_per_share(vault_id, current_price_per_share)

    return performance


# Main Execution
def main():
    # Get the vault from the Vault table with name = "Delta Neutral Vault"
    vault = session.exec(select(Vault).where(Vault.name == "Delta Neutral Vault")).first()

    new_performance_rec = calculate_performance(vault.id)
    # Add the new performance record to the session and commit
    session.add(new_performance_rec)

    # Update the vault with the new information
    vault.monthly_apy = new_performance_rec.apy_1m
    vault.weekly_apy = new_performance_rec.apy_1w
    # vault.current_round = get_current_round()
    vault.current_round = None  # TODO: Remove this line once the contract is updated
    vault.next_close_round_date = None

    session.commit()


if __name__ == "__main__":
    main()
