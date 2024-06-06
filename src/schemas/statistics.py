import uuid
from pydantic import BaseModel
from typing import List, Dict, Any

from models.vaults import NetworkChain


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
    vault_network_chain: NetworkChain | None = None
    slug: str


class VaultStats(BaseModel):
    name: str
    price_per_share: float
    apy_1y: float
    risk_factor: float
    total_value_locked: float
    slug: str
    id: uuid.UUID


class DashboardStats(BaseModel):
    tvl_in_all_vaults: float
    total_depositors: int
    tvl_composition: Dict[str, float]
    vaults: List[VaultStats]
