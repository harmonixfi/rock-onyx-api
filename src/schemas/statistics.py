import uuid
from pydantic import BaseModel
from datetime import datetime
from typing import List, Dict, Any


class Statistics(BaseModel):
    price_per_share: float
    apy_1y: float
    total_value_locked: float
    risk_factor: float
    unique_depositors: int
    fee_structure: Dict[str, Any]
    vault_address: str
    manager_address: str
    all_time_high_per_share: float
    total_shares: float
    sortino_ratio: float
    downside_risk: float
    earned_fee: float
