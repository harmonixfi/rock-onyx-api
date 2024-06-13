import json
from typing import List

from fastapi import APIRouter, HTTPException
from sqlalchemy import distinct, func
from sqlmodel import select
from models.pps_history import PricePerShareHistory
from models.user import User
from models.user_portfolio import UserPortfolio
from models.vault_performance import VaultPerformance
import schemas
import pandas as pd
from api.api_v1.deps import SessionDep
from models import Vault
from core.config import settings
from core import constants


router = APIRouter()

@router.get("/users/{wallet_address}", response_model=dict)
async def get_user(session: SessionDep, wallet_address: str):
        statement = select(User).where(User.wallet_address == wallet_address)
        user = session.exec(statement).first()
        return {'joined': user is not None}
