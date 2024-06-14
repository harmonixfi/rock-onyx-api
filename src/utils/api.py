import uuid
from models.referralcodes import ReferralCode
from models.referrals import Referral
from models.user import User
from sqlmodel import select

def get_user_by_wallet_address(session, wallet_address):
    statement = select(User).where(User.wallet_address == wallet_address)
    user = session.exec(statement).first()
    return user

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