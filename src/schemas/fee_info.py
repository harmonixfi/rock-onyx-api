from pydantic import BaseModel

class FeeInfo(BaseModel):
    deposit_fee: float
    exit_fee: float
    performance_fee: float
    management_fee: float