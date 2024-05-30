import uuid
from pydantic import BaseModel
from typing import List, Dict, Any


class Statistics(BaseModel):
    name: str
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
    slug: str


class Vault_Dashboard(BaseModel):
    name: str
    price_per_share: float
    apy_1y: float
    risk_factor: float
    total_value_locked: float
    slug: str
    id: uuid.UUID


class Dashboard(BaseModel):
    tvl_in_all_vaults: float
    tvl_composition: Dict[str, float]
    vaults: List[Vault_Dashboard]
