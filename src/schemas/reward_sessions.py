#write schema for sessions base on sessions in models
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class RewardSessions(BaseModel):
    session_name: str
    start_date: datetime
    partner_name : str
    end_date: Optional[datetime] = None
