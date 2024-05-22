from datetime import datetime
from pydantic import BaseModel


class EarnedPoints(BaseModel):
    name: str
    point: float
    created_at: datetime | None = None