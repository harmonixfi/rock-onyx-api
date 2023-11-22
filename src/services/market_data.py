import requests


def get_price(symbol):
    url = f"https://api.binance.com/api/v3/avgPrice?symbol={symbol}"
    headers = {"Content-Type": "application/json"}
    response = requests.get(url, headers=headers)
    return float(response.json()["price"])