import uuid
from datetime import datetime, timezone
from sqlmodel import Session, select

# Assuming these models have been defined as per the previous code
from models import User, Referral, UserPortfolio
from core.db import engine
from models.user_portfolio import PositionStatus
from utils.api import create_referral_code


def migrate_data():
    # Create a session
    with Session(engine) as session:
        # Step 1: Get unique UserPortfolio.user_address
        statement = (
            select(UserPortfolio.user_address)
            .where(UserPortfolio.status == PositionStatus.ACTIVE)
            .distinct()
        )
        user_addresses = session.exec(statement).all()

        for user_address in user_addresses:
            # check if user_address not exist in User table first
            user = session.exec(
                select(User).where(User.wallet_address == user_address)
            ).first()
            if user:
                continue

            # Step 2: Create User
            new_user = User(wallet_address=user_address.lower())
            session.add(new_user)
            session.commit()
            session.refresh(new_user)

            # Step 3: Generate ReferralCode for the new user
            create_referral_code(session, new_user)

            # Step 4: Insert new row in Referral with fixed referrer_id
            new_referral = Referral(
                referral_id=uuid.uuid4(),
                referrer_id=uuid.UUID(
                    "f237e9cb-2a47-46d3-aadf-40ed40efe8a0"
                ),
                referee_id=new_user.user_id,
                referral_code_id=uuid.UUID(
                    "7a6764dc-6db5-466d-aa5a-60c07681763b"
                ),
                created_at=datetime.now(timezone.utc),
            )
            session.add(new_referral)
            session.commit()


if __name__ == "__main__":
    migrate_data()
