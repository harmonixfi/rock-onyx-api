from sqlmodel import SQLModel, Field
from typing import Optional
from uuid import UUID, uuid4

class User(SQLModel, table=True):
    __tablename__ = "users"
    
    user_id: UUID = Field(default_factory=uuid4, primary_key=True)
    wallet_address: str = Field(index=True, unique=True)
