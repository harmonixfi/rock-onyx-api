from core.config import settings
from web3 import Web3
from core.abi_reader import read_abi

# Connect to the Ethereum network
w3 = Web3(
    Web3.HTTPProvider(
        "https://arbitrum-mainnet.infura.io/v3/85cde589ce754dafa0a57001c326104d"
    )
)
token_abi = read_abi("ERC20")


def balance_of(wallet_address, token_address):
    token_contract = w3.eth.contract(address=token_address, abi=token_abi)
    token_balance = token_contract.functions.balanceOf(wallet_address).call()
    return token_balance


# Call the getUserAccountData function
wallet_address = Web3.to_checksum_address("0xbc05da14287317fe12b1a2b5a0e1d756ff1801aa")
# Get ETH balance
balance = w3.eth.get_balance(wallet_address)
print(f"ETH Balance: {w3.from_wei(balance, 'ether')}")

wstETH_address = "0x5979D7b546E38E414F7E9822514be443A4800529"
token_balance = balance_of(wallet_address, wstETH_address)
print(f"wstETH Balance: {w3.from_wei(token_balance, 'ether')}")

usdc_address = "0xaf88d065e77c8cC2239327C5EDb3A432268e5831"
token_balance = balance_of(wallet_address, usdc_address)
print(f"USDC Balance: {token_balance / 10**6}")

usdce_address = "0xFF970A61A04b1cA14834A43f5dE4533eBDDB5CC8"
token_balance = balance_of(wallet_address, usdce_address)
print(f"USDC.e Balance: {token_balance / 10**6}")
