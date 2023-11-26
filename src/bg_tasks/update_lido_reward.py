import requests
from web3 import Web3
from core.config import settings
from services.gsheet import authenticate_gspread


def get_lido_reward():
    url = f"https://reward-history-backend.lido.fi/?address={settings.WALLET_ADDRESS}"

    response = requests.request("GET", url)
    data = response.json()
    avg_apr = float(data["averageApr"]) / 100
    reward_eth = float(Web3.from_wei(int(data["totals"]["ethRewards"]), unit='ether'))
    return avg_apr, reward_eth


def main():
    client = authenticate_gspread()

    sheet = client.open("Rock Onyx Fund")
    ws = sheet.get_worksheet(2)

    avg_apr, reward_eth = get_lido_reward()
    ws.update_acell("L8", reward_eth)
    ws.update_acell("L7", avg_apr)


if __name__ == "__main__":
    main()
