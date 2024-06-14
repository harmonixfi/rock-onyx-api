from datetime import datetime, timezone
from typing import Optional
from sqlmodel import SQLModel, Field
import uuid

class ReferralCode(SQLModel, table=True):
    __tablename__ = "referral_codes"
    
    referral_code_id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="users.user_id")
    code: str = Field(index=True, unique=True)
    usage_limit: int = Field(default=50)
    created_at: datetime = Field(default=datetime.now(timezone.utc))