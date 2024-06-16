from datetime import datetime, timezone
from typing import Optional
from sqlmodel import SQLModel, Field
from uuid import UUID, uuid4
from models.vaults import VaultCategory

class PointsMultiplierConfig(SQLModel, table=True):
    __tablename__ = "points_multiplier_config"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    vault_id: UUID = Field(foreign_key="vaults.id")
    multiplier: float = Field(nullable=False)
    created_at: datetime = Field(default=datetime.now(timezone.utc))