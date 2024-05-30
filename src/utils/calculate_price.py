def calculate_avg_entry_price(user_portfolio, latest_pps, shares):
    if user_portfolio.total_shares == None:
        user_portfolio.total_shares = 0
    avg_entry_price = (
        user_portfolio.total_shares * user_portfolio.entry_price + latest_pps * shares
    ) / (user_portfolio.total_shares + shares)
    return avg_entry_price

def sqrt_price_to_price(sqrtRatioX96: int, dec0: int, dec1: int) -> int:
    dec = dec1 if dec1 <= dec0 else (18 - dec1) + dec0
    numerator1 = sqrtRatioX96 * sqrtRatioX96
    numerator2 = 10 ** dec
    price = (numerator1 * numerator2) // (1 << 192)
    return price