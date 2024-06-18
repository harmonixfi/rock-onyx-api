from sqlmodel import SQLModel, Field
from uuid import UUID, uuid4
from datetime import datetime, timezone

class UserPointsHistory(SQLModel, table=True):
    __tablename__ = "user_points_history"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_points_id: UUID = Field(foreign_key="user_points.id")
    point: float
    created_at: datetime = Field(default=datetime.now(timezone.utc))
    updated_at: datetime = Field(default=datetime.now(timezone.utc))