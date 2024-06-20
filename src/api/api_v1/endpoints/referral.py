from typing import List
from fastapi import APIRouter, HTTPException
from sqlmodel import select
from models.referralcodes import ReferralCode
from models.referrals import Referral
from models.reward_sessions import RewardSessions
from models.user import User
from models.user_portfolio import UserPortfolio
from models.rewards import Reward
from models.user_points import UserPoints
import schemas
from api.api_v1.deps import SessionDep
from core import constants
from utils.api import (
    create_user_with_referral,
    get_user_by_wallet_address,
    is_valid_wallet_address,
)

router = APIRouter()


@router.get("/users/{wallet_address}", response_model=dict)
async def get_user(session: SessionDep, wallet_address: str):
    wallet_address = wallet_address.lower()
    if not is_valid_wallet_address(wallet_address):
        raise HTTPException(status_code=400, detail="Invalid wallet address")
    user = get_user_by_wallet_address(session, wallet_address)
    return {"joined": user is not None}


@router.post("/users/join", response_model=dict)
async def join_user(session: SessionDep, user: schemas.UserJoin):
    user.user_address = user.user_address.lower()
    if not is_valid_wallet_address(user.user_address):
        raise HTTPException(status_code=400, detail="Invalid wallet address")
    valid = create_user_with_referral(user.user_address, user.referral_code, session)
    return {"valid": valid}


@router.get("/users/{wallet_address}/referral", response_model=List[str])
async def get_referral_codes(session: SessionDep, wallet_address: str):
    wallet_address = wallet_address.lower()
    if not is_valid_wallet_address(wallet_address):
        raise HTTPException(status_code=400, detail="Invalid wallet address")
    user = get_user_by_wallet_address(session, wallet_address)
    if not user:
        return []
    statement = select(ReferralCode).where(ReferralCode.user_id == user.user_id)
    referral_codes = session.exec(statement).all()
    return [referral_code.code for referral_code in referral_codes]


@router.get("/users/{wallet_address}/rewards", response_model=schemas.Rewards)
async def get_rewards(session: SessionDep, wallet_address: str):
    wallet_address = wallet_address.lower()
    if not is_valid_wallet_address(wallet_address):
        raise HTTPException(status_code=400, detail="Invalid wallet address")

    user = get_user_by_wallet_address(session, wallet_address)
    if not user:
        return {"reward_percentage": 0, "depositors": 0}

    statement = select(Referral).where(Referral.referrer_id == user.user_id)
    referrals = session.exec(statement).all()
    total_referees = len(referrals)

    # get wallet address of all depositors from user table by user_id
    statement = select(User).where(
        User.user_id.in_([referral.referee_id for referral in referrals])
    )
    depositors = session.exec(statement).all()
    high_balance_depositors = 0
    for depositor in depositors:
        statement = select(UserPortfolio).where(
            UserPortfolio.user_address == depositor.wallet_address
        )
        portfolios = session.exec(statement).first()
        if portfolios and portfolios.total_balance >= 50:
            high_balance_depositors += 1

    statement = select(Reward).where(Reward.user_id == user.user_id)
    rewards = session.exec(statement).first()
    if not rewards:
        rewards = Reward(reward_percentage=0)

    return {
        "reward_percentage": 0.05,
        "depositors": total_referees,
        "high_balance_depositors": high_balance_depositors,
    }


@router.get("/users/{wallet_address}/points", response_model=List[schemas.Points])
async def get_points(session: SessionDep, wallet_address: str):
    wallet_address = wallet_address.lower()
    if not is_valid_wallet_address(wallet_address):
        raise HTTPException(status_code=400, detail="Invalid wallet address")

    user = get_user_by_wallet_address(session, wallet_address)
    if not user:
        return []

    statement = (
        select(UserPoints, RewardSessions)
        .where(UserPoints.session_id == RewardSessions.session_id)
        .where(RewardSessions.end_date == None)
        .where(UserPoints.partner_name == constants.HARMONIX)
        .where(UserPoints.wallet_address == wallet_address)
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
