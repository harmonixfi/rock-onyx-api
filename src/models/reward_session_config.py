from datetime import datetime, timezone
from typing import Optional
from sqlmodel import SQLModel, Field
from uuid import UUID, uuid4

class RewardSessionConfig(SQLModel, table=True):
    __tablename__ = "reward_session_config"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    session_id: UUID = Field(foreign_key="reward_sessions.session_id")
    start_delay_days: int
    max_points: float
    config_date: datetime
    created_at: datetime = Field(default=datetime.now(timezone.utc))