from datetime import datetime
from sqlmodel import SQLModel, Field
import uuid


class PriceFeedOracleHistoryBase(SQLModel):
    datetime: datetime
    token_pair: str
    lastest_price: float

class PriceFeedOracleHistory(PriceFeedOracleHistoryBase, table=True):
    __tablename__ = "price_feed_oracle_history"
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
