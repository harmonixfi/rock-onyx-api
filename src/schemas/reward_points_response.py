from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

from models.rewards import Reward
from models.user_points import UserPoints

class RewardPointsResponse(BaseModel):
    reward : float
    point : float