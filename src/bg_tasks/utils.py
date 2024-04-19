from datetime import timedelta
import uuid
import numpy as np
import pandas as pd
import pendulum
from sqlmodel import Session, select
from models.pps_history import PricePerShareHistory
from empyrical import sortino_ratio, downside_risk

def get_before_price_per_shares(
    session: Session, vault_id: uuid.UUID, days: int
) -> PricePerShareHistory:
    target_date = pendulum.now(tz=pendulum.UTC) - timedelta(days=days)

    # Get the PricePerShareHistory records before the target date and order them by datetime in descending order

    pps_history = session.exec(
        select(PricePerShareHistory)
        .where(PricePerShareHistory.vault_id == vault_id)
        .where(PricePerShareHistory.datetime <= target_date)
        .order_by(PricePerShareHistory.datetime.desc())
        .limit(3)
    ).all()

    # If there are any records, return the price per share of the most recent one
    if pps_history:
        return pps_history[0]

    pps_history = session.exec(
        select(PricePerShareHistory)
        .where(PricePerShareHistory.vault_id == vault_id)
        .order_by(PricePerShareHistory.datetime.asc())
    ).first()
    # If there are no records before the target date, return None
    # and the first record of pps_history datetime
    return pps_history


def calculate_roi(after: float, before: float, days: int) -> float:
    # calculate our annualized return for a vault
    pps_delta = (after - before) / (before or 1)
    annualized_roi = (1 + pps_delta) ** (365.2425 / days) - 1
    return annualized_roi

def calculate_risk_factor(returns):
    # Filter out positive returns
    negative_returns = [r for r in returns if r < 0]

    # Calculate standard deviation of negative returns
    risk_factor = np.std(negative_returns)

    if np.isnan(risk_factor) or np.isinf(risk_factor):
        risk_factor = 0
    return risk_factor

def calculate_pps_statistics(session, vault_id):
    statement = (select(PricePerShareHistory)
            .where(PricePerShareHistory.vault_id == vault_id)
            .order_by(PricePerShareHistory.datetime.desc())
        )
    pps = session.exec(statement).all()

    list_pps = []
    for p in pps:
        list_pps.append(p.price_per_share)
    df = pd.DataFrame(list_pps)

    all_time_high_per_share = df.max().values[0]
    df=df.pct_change()

    sortino = float(sortino_ratio(df, period="weekly"))
    if np.isnan(sortino) or np.isinf(sortino):
        sortino = 0
    downside = float(downside_risk(df, period="weekly"))
    if np.isnan(downside) or np.isinf(downside):
        downside = 0
    returns = df.values.flatten()
    risk_factor = calculate_risk_factor(returns)
    return all_time_high_per_share,sortino,downside,risk_factor