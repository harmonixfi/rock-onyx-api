from datetime import datetime, timezone
from typing import Optional
from sqlmodel import SQLModel, Field
from uuid import UUID, uuid4

class RewardSessions(SQLModel, table=True):
    __tablename__ = "reward_sessions"
    
    session_id: UUID = Field(default_factory=uuid4, primary_key=True)
    session_name: str = Field(index=True)
    start_date: datetime = Field(default=datetime.now(timezone.utc))
    update_date: Optional[datetime] = Field(default=None)
    end_date: Optional[datetime] = Field(default=None)
    points_distributed: float = Field(default=0)
    partner_name : str
