from datetime import datetime, timedelta

import pandas as pd
from sqlmodel import Session, select
from web3 import Web3

from core.abi_reader import read_abi
from core.config import settings
from core.db import engine
from models.price_feed_oracle_history import PriceFeedOracleHistory
from utils.calculate_price import sqrt_price_to_price

# Connect to the Ethereum network
if settings.ENVIRONMENT_NAME == "Production":
    w3 = Web3(Web3.HTTPProvider(settings.ARBITRUM_MAINNET_INFURA_URL))
else:
    w3 = Web3(Web3.HTTPProvider(settings.SEPOLIA_TESTNET_INFURA_URL))

rockonyx_usdce_usdc_price_feed_abi = read_abi("UsdceUsdcPriceFeedOracle")
contract = w3.eth.contract(
    address=settings.ROCKONYX_USDCE_USDC_PRICE_FEED_ADDRESS,
    abi=rockonyx_usdce_usdc_price_feed_abi,
)

usdce_usdc_pool_abi = read_abi("camelotpool")
usdce_usdc_pool_contract = w3.eth.contract(
    address=settings.USDCE_USDC_CAMELOT_POOL_ADDRESS,
    abi=usdce_usdc_pool_abi,
)

def update_lastest_price(_price):
    contract.functions.setLatestPrice(_price).call()

def get_current_pool_price():
    result = usdce_usdc_pool_contract.functions.globalState().call()
    return 1e14 / sqrt_price_to_price(result[0], 6, 6)

session = Session(engine)

# Main Execution
def main():
    price_feed_oracle_histories = session.exec(
        select(PriceFeedOracleHistory)
        .where(PriceFeedOracleHistory.token_pair == "usdce_usdc")
        .order_by(PriceFeedOracleHistory.datetime.asc())
        .limit(10)
    ).all()

    current_price = get_current_pool_price();
    average_price = current_price

    for price_feed_oracle_history in price_feed_oracle_histories:
        average_price += price_feed_oracle_history.lastest_price
    
    average_price = average_price / (len(price_feed_oracle_histories) + 1)

    # update_lastest_price(average_price);

    new_price_feed = PriceFeedOracleHistory(
            datetime=datetime.now().date(), 
            token_pair="usdce_usdc", 
            lastest_price=average_price
        )
    
    session.add(new_price_feed)
    session.commit()

if __name__ == "__main__":
    main()
