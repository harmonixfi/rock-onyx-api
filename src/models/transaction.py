from typing import Optional
from sqlmodel import SQLModel, Field
from enum import Enum
from uuid import UUID
from datetime import datetime, timezone

class Transaction(SQLModel, table=True):
    __tablename__ = "transaction"
    txhash: str = Field(primary_key=True)
    created_on: datetime = Field(default=datetime.now(tz=timezone.utc))

