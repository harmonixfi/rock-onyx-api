from datetime import datetime
import uuid

import sqlmodel
from sqlalchemy.dialects.postgresql import JSON

class VaultPerformanceBase(sqlmodel.SQLModel):
    datetime: datetime
    total_locked_value: float
    apy_1m: float
    apy_1w: float
    apy_ytd: float
    benchmark: float
    pct_benchmark: float
    risk_factor: float
    all_time_high_per_share: float
    total_shares: float
    sortino_ratio: float
    downside_risk: float
    earned_fee: float
    fee_structure: str
    
class VaultPerformance(VaultPerformanceBase, table=True):
    __tablename__ = "vault_performance"

    id: uuid.UUID = sqlmodel.Field(default_factory=uuid.uuid4, primary_key=True)
    vault_id: uuid.UUID = sqlmodel.Field(foreign_key="vaults.id")
