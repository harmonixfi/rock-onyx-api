from datetime import datetime, timezone
from typing import Optional
from sqlmodel import SQLModel, Field
from uuid import UUID, uuid4

class Session(SQLModel, table=True):
    __tablename__ = "sessions"
    
    session_id: UUID = Field(default_factory=uuid4, primary_key=True)
    session_name: str = Field(index=True)
    start_date: datetime = Field(default=datetime.now(timezone.utc))
    end_date: datetime = Field(default=None)
