from sqlmodel import SQLModel, Field
from uuid import UUID, uuid4
from datetime import datetime, timezone


class UserPoints(SQLModel, table=True):
    __tablename__ = "user_points"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    vault_id: UUID = Field(foreign_key="vaults.id")
    wallet_address: str = Field(index=True)
    points: float
    partner_name: str = Field(index=True)
    created_at: datetime = Field(default=datetime.now(timezone.utc), index=True)
    updated_at: datetime = Field(default=datetime.now(timezone.utc), index=True)


class UserPointAudit(SQLModel, table=True):
    __tablename__ = "user_point_audit"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_points_id: UUID = Field(foreign_key="user_points.id")
    old_value: float
    new_value: float
    created_at: datetime = Field(default=datetime.now(timezone.utc))
