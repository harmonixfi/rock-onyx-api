import requests
ROCKONYX_ADDRESS = '0xBC05da14287317FE12B1a2b5a0E1d756Ff1801Aa'
LIDO_ADDRESS = '0xae7ab96520DE3A18E5e111B5EaAb095312D7fE84'
ETHERSCAN_API_KEY = 'JXCRTSBCEZETHV98MCMQP8XJZQY4357PY9'

def get_transaction():
    page = 0
    while True:
        page += 1
        print(page)
        url = f"https://api.etherscan.io/api?module=account&action=tokentx&contractaddress={LIDO_ADDRESS}&address={ROCKONYX_ADDRESS}&page={page}&offset=1000&sort=desc&apikey={ETHERSCAN_API_KEY}"
        headers = {"Content-Type": "application/json"}
        response = requests.get(url, headers=headers)
        result = response.json()['result']
        for r in result:
            print(f"blocknumber: {r['blockNumber']}, tx: {r['hash']}, value: {r['value']}")
        if(len(result) == 0):
            break;

get_transaction()