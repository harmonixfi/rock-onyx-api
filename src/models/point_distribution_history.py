from sqlmodel import SQLModel, Field
from typing import Optional
from uuid import UUID
from datetime import datetime, timezone


class PointDistributionHistory(SQLModel, table=True):
    __tablename__ = "point_distribution_history"

    id: Optional[UUID] = Field(default=None, primary_key=True)
    partner_name: str = Field(index=True)
    point: float
    created_at: datetime = Field(default=datetime.now(timezone.utc), index=True)
