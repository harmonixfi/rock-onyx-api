from web3 import AsyncWeb3
from web3.eth import Contract


async def sign_and_send_transaction(
    web3: AsyncWeb3, function, args, from_address, private_key, value: int = None
):
    cnt = await web3.eth.get_transaction_count(from_address)
    # cnt = 1235
    transaction = {
        "from": from_address,
        "nonce": cnt
    }
    if value is not None:
        transaction["value"] = value

    tx = await function(*args).build_transaction(transaction)
    signed_tx = web3.eth.account.sign_transaction(tx, private_key)
    tx_hash = await web3.eth.send_raw_transaction(signed_tx.rawTransaction)
    receipt = await web3.eth.wait_for_transaction_receipt(tx_hash)
    return receipt


def parse_hex_to_int(hex_str, is_signed=True):
    """Parse a hexadecimal string to an integer. Assumes hex_str is without '0x' and is big-endian."""
    if is_signed:
        return int.from_bytes(bytes.fromhex(hex_str), byteorder="big", signed=True)
    else:
        return int(hex_str, 16)