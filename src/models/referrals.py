from datetime import datetime, timezone
from typing import Optional
from sqlmodel import SQLModel, Field
from uuid import UUID, uuid4

class Referral(SQLModel, table=True):
    __tablename__ = "referrals"
    
    referral_id: UUID = Field(default_factory=uuid4, primary_key=True)
    referrer_id: UUID = Field(foreign_key="users.user_id")
    referee_id: UUID = Field(foreign_key="users.user_id")
    referral_code_id: UUID = Field(foreign_key="referral_codes.referral_code_id")
    created_at: datetime = Field(default=datetime.now(timezone.utc))
