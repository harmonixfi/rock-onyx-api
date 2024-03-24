import uuid
from pydantic import BaseModel
from datetime import datetime
from typing import List, Dict, Any

class Position(BaseModel):
    id: int
    vault_id: uuid.UUID
    vault_name: str
    user_address: str
    total_balance: float
    init_deposit: float
    pnl: float | None = None
    status: str
    trade_start_date: datetime
    pending_withdrawal: float | None = None
    vault_currency: str | None = None
    current_round: int | None = None
    next_close_round_date : datetime | None = None
    monthly_apy: float | None = None
    weekly_apy: float | None = None


class PortfolioBase(BaseModel):
    total_balance: float
    positions: List[Position] | None = None


class PortfolioInDBBase(PortfolioBase):
    model_config: Dict[str, Any] = {}


class Portfolio(PortfolioBase):
    pass


class PortfolioInDB(PortfolioInDBBase):
    pass