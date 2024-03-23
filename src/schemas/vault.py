import uuid
from pydantic import BaseModel, ConfigDict


class VaultBase(BaseModel):
    id: uuid.UUID
    name: str
    apr: float = None
    apr: float | None = None
    monthly_apy: float | None = None
    weekly_apy: float | None = None
    max_drawdown: float | None = None
    vault_capacity: int | None = None
    vault_currency: str | None = None
    current_round: int | None = None
    next_close_round_date: int | None = None


# Properties shared by models stored in DB
class VaultInDBBase(VaultBase):
    model_config = ConfigDict(from_attributes=True)


# Properties to return to client
class Vault(VaultInDBBase):
    pass


# Properties properties stored in DB
class VaultInDB(VaultInDBBase):
    pass
