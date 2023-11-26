# import dependencies
from web3 import Web3
import asyncio

# filter through blocks and look for transactions involving this address
ROCKONYX_ADDRESS = '0xBC05da14287317FE12B1a2b5a0E1d756Ff1801Aa'
LIDO_ADDRESS = '0xae7ab96520DE3A18E5e111B5EaAb095312D7fE84'
w3 = Web3(Web3.WebsocketProvider('wss://quiet-special-sailboat.quiknode.pro/2626d91a9e8f6ea3db42b1acc54c0c4fa9826f5f/'));

# starting_blocknumber = 18597836
# ending_blocknumber = starting_blocknumber + 100

# def getTransactions(start, end, rockOnyxAddress, lidoAddress):
#     print(f"Started filtering through block number {start} to {end} for transactions involving the address - {rockOnyxAddress}...")
#     for x in range(start, end):
#         print(f"block number: {x}")
#         block = w3.eth.get_block(x, True)
#         for transaction in block.transactions:
#             if (transaction['from'].upper() == rockOnyxAddress.upper() and transaction['to'].upper() == lidoAddress.upper()):
#                 tx = w3.eth.get_transaction(transaction['hash'])
#                 print(f"walle transaction: {tx}")

#     print(f"Finished searching blocks {start} through {end}")
    
# getTransactions(starting_blocknumber, ending_blocknumber, ROCKONYX_ADDRESS, LIDO_ADDRESS)

# event_filter = w3.eth.filter({
#     "fromBlock": 18597836, 
#     "toBlock": 18597838,
#     "address": LIDO_ADDRESS,
#     "topics": ["0x96a25c8ce0baabc1fdefd93e9ed25d8e092a3332f3aa9a41722b5697231d1d1a",
#                "0x000000000000000000000000bc05da14287317fe12b1a2b5a0e1d756ff1801aa"
#                ],
#     })
# entries = event_filter.get_all_entries()
# for entry in entries:
#     print(f"deposit to Lido:")
#     print(f"block number: {entry.blockNumber}")
#     print(f"tx: {entry.transactionHash.hex()}")
#     print(f"submit value: {int(entry.data.hex()[0:66],16)}")

def handle_event(entry, eventName):
    print(eventName)
    print(f"block number: {entry.blockNumber}")
    print(f"tx: {entry.transactionHash.hex()}")
    print(f"submit value: {int(entry.data.hex()[0:66],16)}")
        
async def log_loop(event_filter, poll_interval, eventName):
    while True:
        for event in event_filter.get_new_entries():
            handle_event(event, eventName)
        await asyncio.sleep(poll_interval)

def main():
    deposit_event_filter = w3.eth.filter({
        "address": LIDO_ADDRESS,
        "topics": ["0x96a25c8ce0baabc1fdefd93e9ed25d8e092a3332f3aa9a41722b5697231d1d1a"]
        })
    
    withdraw_event_filter = w3.eth.filter({
        "address": LIDO_ADDRESS,
        "topics": ["0x96a25c8ce0baabc1fdefd93e9ed25d8e092a3332f3aa9a41722b5697231d1d1a"]
        })
    loop = asyncio.get_event_loop()

    try:
        loop.run_until_complete(
            asyncio.gather(
                log_loop(deposit_event_filter, 2, "deposit_event_filter"),
                log_loop(withdraw_event_filter, 2, "withdraw_event_filter")   
            )
        )
    finally:
        loop.close()

#     # worker = Thread(target=log_loop, args=(event_filter, 2), daemon=True)
#     # worker.start()

main()