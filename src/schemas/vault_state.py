from pydantic import BaseModel

class VaultState(BaseModel):
    performance_fee: float = 0
    management_fee: float = 0
    current_round_fee: float = 0
    withdrawal_pool: float = 0
    pending_deposit: float = 0
    total_share: float = 0
    last_locked: float = 0