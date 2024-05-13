import uuid
from sqlmodel import Field, SQLModel
from typing import Optional
from uuid import UUID
from datetime import datetime, timezone


class UserRestakingPoint(SQLModel, table=True):
    __tablename__ = "user_restaking_points"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    position_id: int = Field(foreign_key="user_portfolio.id")
    vault_id: UUID = Field(foreign_key="vaults.id")
    vendor_name: str  # Name of the staking platform e.g., 'Renzo', 'Zircuit'
    points: float = Field(default=0, index=True)  # Total points earned
    session_name: str  # Name of the session e.g., 'Session 1', 'Session 2'
    last_updated: datetime = Field(
        default_factory=lambda: datetime.now(tz=timezone.utc)
    )  # Last update timestamp
