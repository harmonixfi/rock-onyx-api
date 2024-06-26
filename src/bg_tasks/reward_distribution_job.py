import logging
from datetime import datetime, timedelta, timezone
from sqlmodel import Session, select
from uuid import UUID
from log import setup_logging_to_file
from models.point_distribution_history import PointDistributionHistory
from models.points_multiplier_config import PointsMultiplierConfig
from models.referrals import Referral
from models.reward_session_config import RewardSessionConfig
from models.reward_sessions import RewardSessions
from models.rewards import Reward
from models.user import User
from models.user_points import UserPoints
from models.user_points_history import UserPointsHistory
from models.user_portfolio import PositionStatus, UserPortfolio
from models.vaults import Vault
from core.db import engine
from core.config import settings
from core import constants
from sqlmodel import Session, select


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

session = Session(engine)


def reward_distribution_job():
    with Session(engine) as session:
        logger.info("Starting reward distribution job...")
        current_time = datetime.now(timezone.utc)
        referrals_query = select(Referral).order_by(Referral.created_at)
        referrals = session.exec(referrals_query).all()
        unique_referrers = []
        for referral in referrals:
            if len(unique_referrers) >= constants.REWARD_HIGH_LIMIT:
                break
            if referral.referrer_id in unique_referrers:
                continue
            reward_query = select(Reward).where(Reward.user_id == referral.referrer_id)
            reward = session.exec(reward_query).first()
            if reward:
                if reward.end_date is None:
                    continue
                if reward.end_date.replace(tzinfo=timezone.utc) < current_time:
                    reward.reward_percentage = constants.REWARD_DEFAULT_PERCENTAGE
                    session.commit()
                unique_referrers.append(referral.referrer_id)
                continue
            else:
                user_query = select(User).where(User.user_id == referral.referee_id)
                user = session.exec(user_query).first()
                if not user:
                    continue
                user_portfolio_query = select(UserPortfolio).where(
                    UserPortfolio.user_address == user.wallet_address
                )
                user_portfolio = session.exec(user_portfolio_query).first()
                if not user_portfolio:
                    continue
                if user_portfolio.total_balance >= constants.MIN_FUNDS_FOR_HIGH_REWARD:
                    reward_percentage = Reward(
                        user_id=referral.referrer_id,
                        referral_code_id=referral.referral_code_id,
                        reward_percentage=constants.REWARD_HIGH_PERCENTAGE,
                        start_date=current_time,
                        end_date=current_time
                        + timedelta(days=constants.HIGH_REWARD_DURATION_DAYS),
                    )
                    session.add(reward_percentage)
                    session.commit()
                    unique_referrers.append(referral.referrer_id)
                    logger.info(
                        f"High reward percentage {constants.REWARD_HIGH_PERCENTAGE}% for referrer {referral.referrer_id}"
                    )
        logger.info("Reward distribution job completed.")


# Example usage
if __name__ == "__main__":
    reward_distribution_job()
