from datetime import timedelta
import uuid

import pendulum
from sqlmodel import Session, select
from models.pps_history import PricePerShareHistory


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
