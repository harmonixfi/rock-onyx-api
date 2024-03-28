from datetime import datetime
import uuid

import sqlmodel


class VaultBase(sqlmodel.SQLModel):
    id: uuid.UUID = sqlmodel.Field(default_factory=uuid.uuid4, primary_key=True)
    name: str
    contract_address: str | None = None
    apr: float | None = None
    ytd_apy: float | None = None
    monthly_apy: float | None = None
    weekly_apy: float | None = None
    max_drawdown: float | None = None
    vault_capacity: int | None = None
    vault_currency: str | None = None
    current_round: int | None = None
    next_close_round_date: datetime | None = None
    slug: str | None = None


# Database model, database table inferred from class name
class Vault(VaultBase, table=True):
    __tablename__ = "vaults"
