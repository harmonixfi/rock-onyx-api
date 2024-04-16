def calculate_avg_entry_price(user_portfolio, latest_pps, shares):
    if user_portfolio.total_shares == None:
        user_portfolio.total_shares = 0
    avg_entry_price = (
        user_portfolio.total_shares * user_portfolio.entry_price + latest_pps * shares
    ) / (user_portfolio.total_shares + shares)
    return avg_entry_price
