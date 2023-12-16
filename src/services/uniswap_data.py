import requests
from web3 import Web3
from core.config import settings


headers = {
    "authority": "api.uniswap.org",
    "accept": "*/*",
    "content-type": "application/json",
    "origin": "https://app.uniswap.org",
    "referer": "https://app.uniswap.org/",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
    "x-request-source": "uniswap-web",
}


class Quotation:
    def __init__(self, quote_response):
        self.src_amount = float(quote_response["quote"]["amountDecimals"])
        self.dest_amount = float(quote_response["quote"]["quoteDecimals"])


def get_uniswap_quote(token_in, src_amount, token_out, chain_id=42161) -> Quotation:
    w3 = Web3(Web3.HTTPProvider(settings.ARBITRUM_MAINNET_INFURA_URL))

    if not w3.is_connected():
        raise Exception("Web3 provider is not connected")

    # Convert the amount from decimals to wei
    if token_in in [settings.USDCE_ADDRESS, settings.USDC_ADDRESS]:
        amount_in_wei = src_amount * 10**6
    else:
        amount_in_wei = w3.to_wei(src_amount, "ether")

    url = "https://api.uniswap.org/v2/quote"

    payload = {
        "tokenInChainId": chain_id,
        "tokenIn": token_in,
        "tokenOutChainId": chain_id,
        "tokenOut": token_out,
        "amount": str(amount_in_wei),
        "sendPortionEnabled": True,
        "type": "EXACT_INPUT",
        "configs": [
            {
                "protocols": ["V2", "V3", "MIXED"],
                "enableUniversalRouter": True,
                "routingType": "CLASSIC",
                "enableFeeOnTransferFeeFetching": True,
            }
        ],
    }

    response = requests.post(url, headers=headers, json=payload)

    if response.status_code == 200:
        return Quotation(response.json())
    else:
        return None

