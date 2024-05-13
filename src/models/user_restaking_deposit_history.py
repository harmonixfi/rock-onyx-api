import uuid
from sqlmodel import SQLModel, Field
from datetime import datetime, timezone


class UserRestakingDepositHistory(SQLModel, table=True):
    __tablename__ = "user_restaking_deposit_history"
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    position_id: int = Field(foreign_key="user_portfolio.id")
    deposit_amount: float
    created_at: datetime = Field(default=datetime.now(tz=timezone.utc))
    updated_at: datetime | None = Field(default=None, nullable=True)


# Create a model that store the audit data for UserRestakingDepositHistory when system changes any field in the table.
class UserRestakingDepositHistoryAudit(SQLModel, table=True):
    __tablename__ = "user_restaking_deposit_history_audit"
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    deposit_history_id: uuid.UUID = Field(foreign_key="user_restaking_deposit_history.id")
    field_name: str = Field(length=255, nullable=False)
    old_value: str = Field(length=255, nullable=False)
    new_value: str = Field(length=255, nullable=False)
    updated_at: datetime = Field(default=datetime.now(tz=timezone.utc))
    updated_by: str = Field(length=255, nullable=False)
    created_at: datetime = Field(default=datetime.now(tz=timezone.utc))
