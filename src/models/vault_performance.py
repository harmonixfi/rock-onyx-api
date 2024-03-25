from datetime import datetime
import uuid

import sqlmodel


class VaultPerformanceBase(sqlmodel.SQLModel):
    datetime: datetime
    total_locked_value: float
    apy_1m: float
    apy_1w: float
    benchmark: float
    pct_benchmark: float


class VaultPerformance(VaultPerformanceBase, table=True):
    __tablename__ = "vault_performance"

    id: uuid.UUID = sqlmodel.Field(default_factory=uuid.uuid4, primary_key=True)
    vault_id: uuid.UUID = sqlmodel.Field(foreign_key="vaults.id")
