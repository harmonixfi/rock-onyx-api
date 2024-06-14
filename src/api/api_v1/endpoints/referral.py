import json
from typing import List
import uuid

from fastapi import APIRouter, HTTPException
from sqlalchemy import distinct, func
from sqlmodel import select
from models.pps_history import PricePerShareHistory
from models.referralcodes import ReferralCode
from models.referrals import Referral
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
        user = get_user_by_wallet_address(session, wallet_address)
        return {'joined': user is not None}

def get_user_by_wallet_address(session, wallet_address):
    statement = select(User).where(User.wallet_address == wallet_address)
    user = session.exec(statement).first()
    return user


@router.post("/users/join", response_model=dict)
async def join_user(session: SessionDep, user: schemas.UserJoin):
        valid = create_user_with_referral(user.user_address, user.referral_code, session)
        return {'valid': valid}

@router.get("/users/{wallet_address}/referral", response_model=List[str])
async def get_referral_codes(session: SessionDep, wallet_address: str):
        user = get_user_by_wallet_address(session, wallet_address)
        statement = select(ReferralCode).where(ReferralCode.user_id == user.user_id)
        referral_codes = session.exec(statement).all()
        return [referral_code.code for referral_code in referral_codes]

def create_user_with_referral(user_address, referral_code, session):
        user = get_user_by_wallet_address(session, user_address)
        if user:
                return False
        referral = get_referral_by_code(session, referral_code)
        if not referral:
                return False
        if referral.usage_limit <= 0:
                return False
        referral.usage_limit -= 1
        user = User(
                user_id=uuid.uuid4(),
                wallet_address=user_address)
        session.add(user)
        session.commit()

        for _ in range(10):
                create_referral_code(session, user)

        new_referral = Referral(
                referrer_id=referral.user_id,
                referee_id=user.user_id,
                referral_code_id=referral.referral_code_id
        )
        session.add(new_referral)
        session.commit()
        return True

def create_referral_code(session, user):
    new_referral_code = ReferralCode(
                referral_code_id=uuid.uuid4(),
                user_id=user.user_id,
                code=uuid.uuid4().hex,
                usage_limit=50
        )
    session.add(new_referral_code)
    session.commit()

def get_referral_by_code(session, code):
        statement = select(ReferralCode).where(ReferralCode.code == code)
        referral = session.exec(statement).first()
        return referral
