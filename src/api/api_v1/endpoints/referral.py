import json
from typing import List
import uuid
import datetime
from fastapi import APIRouter, HTTPException
from sqlalchemy import distinct, func
from sqlmodel import select
import models
from models.pps_history import PricePerShareHistory
from models.referralcodes import ReferralCode
from models.referrals import Referral
from models.reward_sessions import RewardSessions
from models.user import User
from models.user_portfolio import UserPortfolio
from models.vault_performance import VaultPerformance
from models.rewards import Reward
from models.user_points import UserPoints
import schemas
import pandas as pd
from api.api_v1.deps import SessionDep
from models import Vault
from core.config import settings
from core import constants
from utils.api import (
    create_user_with_referral,
    get_user_by_wallet_address,
    is_valid_wallet_address,
)

router = APIRouter()


@router.get("/users/{wallet_address}", response_model=dict)
async def get_user(session: SessionDep, wallet_address: str):
    user = get_user_by_wallet_address(session, wallet_address)
    return {"joined": user is not None}


@router.post("/users/join", response_model=dict)
async def join_user(session: SessionDep, user: schemas.UserJoin):
    valid = create_user_with_referral(user.user_address, user.referral_code, session)
    return {"valid": valid}


@router.get("/users/{wallet_address}/referral", response_model=List[str])
async def get_referral_codes(session: SessionDep, wallet_address: str):
    user = get_user_by_wallet_address(session, wallet_address)
    if not user:
        return []
    statement = select(ReferralCode).where(ReferralCode.user_id == user.user_id)
    referral_codes = session.exec(statement).all()
    return [referral_code.code for referral_code in referral_codes]


@router.get("/users/{wallet_address}/rewards", response_model=schemas.Rewards)
async def get_rewards(session: SessionDep, wallet_address: str):
    user = get_user_by_wallet_address(session, wallet_address)
    if not user:
        return {"reward_percentage": 0, "depositors": 0}
    statement = select(Referral).where(Referral.referrer_id == user.user_id)
    referrals = session.exec(statement).all()
    depositors = len(referrals)
    statement = select(Reward).where(Reward.user_id == user.user_id)
    rewards = session.exec(statement).first()
    if not rewards:
        rewards = Reward(reward_percentage=0)
    return {"reward_percentage": rewards.reward_percentage, "depositors": depositors}


@router.get("/users/{wallet_address}/points", response_model=List[schemas.Points])
async def get_points(session: SessionDep, wallet_address: str):
    user = get_user_by_wallet_address(session, wallet_address)
    if not user:
        return []
    statement = select(UserPoints, RewardSessions).where(
        UserPoints.session_id == RewardSessions.session_id
    )

    user_points = session.exec(statement).all()

    if not user_points:
        return []
    points: List[schemas.Points] = []
    for user_point in user_points:
        point = schemas.Points(
            points=user_point.UserPoints.points,
            start_date=user_point.RewardSessions.start_date,
            end_date=user_point.RewardSessions.end_date,
            session_name=user_point.RewardSessions.session_name,
            partner_name=user_point.RewardSessions.partner_name,
        )
        points.append(point)
    return points
