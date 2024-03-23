from datetime import datetime
from sqlmodel import SQLModel, Field
import uuid


class PricePerShareHistoryBase(SQLModel):
    datetime: datetime
    price_per_share: float


class PricePerShareHistory(PricePerShareHistoryBase, table=True):
    __tablename__ = "pps_history"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    vault_id: uuid.UUID = Field(foreign_key="vaults.id")
