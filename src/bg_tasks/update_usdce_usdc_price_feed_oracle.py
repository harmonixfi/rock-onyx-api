import asyncio
from datetime import datetime, timedelta

import pandas as pd
from sqlmodel import Session, select
from web3 import AsyncWeb3, Web3
from web3.eth import AsyncEth

from core.abi_reader import read_abi
from core.config import settings
from core.db import engine
from models.price_feed_oracle_history import PriceFeedOracleHistory
from utils.calculate_price import sqrt_price_to_price
from utils.web3_utils import sign_and_send_transaction

# Connect to the Ethereum network
if settings.ENVIRONMENT_NAME == "Production":
    w3 = AsyncWeb3(
        provider=AsyncWeb3.AsyncHTTPProvider(
            endpoint_uri=settings.ARBITRUM_MAINNET_INFURA_URL,
        ),
        modules={"eth": (AsyncEth,)},
        middlewares=[],
    )
else:
    w3 = AsyncWeb3(
        provider=AsyncWeb3.AsyncHTTPProvider(
            endpoint_uri=settings.SEPOLIA_TESTNET_INFURA_URL,
        ),
        modules={"eth": (AsyncEth,)},
        middlewares=[],
    )

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


async def update_lastest_price(_price, price_decimals=8):
    await sign_and_send_transaction(
        w3,
        contract.functions.setLatestPrice,
        [int(_price * price_decimals)],
        settings.OWNER_WALLET_ADDRESS,
        settings.OWNER_WALLET_PRIVATEKEY,
    )


async def get_current_pool_price():
    result = await usdce_usdc_pool_contract.functions.globalState().call()
    price = sqrt_price_to_price(result[0], 6, 6)
    return price / 1e6


session = Session(engine)


# Main Execution
async def main():
    price_feed_oracle_histories = session.exec(
        select(PriceFeedOracleHistory)
        .where(PriceFeedOracleHistory.token_pair == "usdce_usdc")
        .order_by(PriceFeedOracleHistory.datetime.desc())
        .limit(10)
    ).all()

    current_price = await get_current_pool_price()
    average_price = sum(
        item.latest_price for item in price_feed_oracle_histories
    ) + current_price / (len(price_feed_oracle_histories) + 1)

    await update_lastest_price(average_price)

    new_price_feed = PriceFeedOracleHistory(
        datetime=datetime.now().date(),
        token_pair="usdce_usdc",
        latest_price=average_price,
    )

    session.add(new_price_feed)
    session.commit()


if __name__ == "__main__":
    asyncio.run(main())
