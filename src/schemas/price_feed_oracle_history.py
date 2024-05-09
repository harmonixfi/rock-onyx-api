from datetime import datetime
from pydantic import BaseModel

class PriceFeedOracleHistory(BaseModel):
    datetime: datetime
    token_pair: str
    lastest_price: float