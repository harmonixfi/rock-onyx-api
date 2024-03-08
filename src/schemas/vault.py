from pydantic import BaseModel, ConfigDict


class VaultBase(BaseModel):
    id: int
    name: str
    apr: float = None
    monthly_apy: float = None
    weekly_apy: float = None
    max_drawdown: float = None
    vault_capacity: int = None
    vault_currency: str = None


# Properties shared by models stored in DB
class VaultInDBBase(VaultBase):
    model_config = ConfigDict(from_attributes=True)


# Properties to return to client
class Vault(VaultInDBBase):
    pass


# Properties properties stored in DB
class VaultInDB(VaultInDBBase):
    pass
