import json


def read_abi(token: str):
    with open(f"./config/{token.lower()}_abi.json") as f:
        data = json.load(f)
        return data
