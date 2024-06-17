import logging
from datetime import datetime, timedelta, timezone
from sqlmodel import Session, select
from uuid import UUID
from log import setup_logging_to_file
from models.points_multiplier_config import PointsMultiplierConfig
from models.user_points import UserPoints
from models.user_portfolio import PositionStatus, UserPortfolio
from models.vaults import Vault
from core.db import engine
from core.config import settings
from sqlmodel import Session, select
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration constants
CONFIG_DATE = datetime(2024, 1, 1, tzinfo=timezone.utc)  # Example configuration date
SESSION_START_DELAY_DAYS = 69
SESSION_1_START_DATE = CONFIG_DATE + timedelta(days=SESSION_START_DELAY_DAYS)
MAX_SESSION_1_POINTS = 5_000_000

session = Session(engine)

def harmonix_distribute_points():
    current_time = datetime.now(timezone.utc)

    if current_time < SESSION_1_START_DATE:
        logger.info("Session 1 has not started yet.")
        return
    
    # select all user points distributed where partner_name is Harmonix and created_at is greater than or equal to SESSION_1_START_DATE
    session_1_points_query = (
        select(UserPoints)
        .where(UserPoints.partner_name == "Harmonix")
        .where(UserPoints.created_at >= SESSION_1_START_DATE)
    )
    
    total_points_distributed = sum([user_points.points for user_points in session.exec(session_1_points_query).all()])

    if total_points_distributed >= MAX_SESSION_1_POINTS:
        logger.info("Maximum points for Session 1 have been distributed.")
        return
    
    # Fetch active user portfolios
    active_portfolios_query = (
        select(UserPortfolio)
        .where(UserPortfolio.status == PositionStatus.ACTIVE)
    )
    active_portfolios = session.exec(active_portfolios_query).all()
    active_portfolios.sort(key=lambda x: x.trade_start_date)
    for portfolio in active_portfolios:
        vault_query = select(Vault).where(Vault.id == portfolio.vault_id)
        vault = session.exec(vault_query).first()
        
        if not vault:
            continue
        
        # Get the multiplier for the vault category
        multiplier_query = select(PointsMultiplierConfig).where(
            PointsMultiplierConfig.vault_id == vault.id
        )
        multiplier_config = session.exec(multiplier_query).first()
        
        if not multiplier_config:
            continue
        multiplier = multiplier_config.multiplier
        
        # Calculate points to be distributed
        duration_hours = (current_time - portfolio.trade_start_date.replace(tzinfo=timezone.utc)).total_seconds() / 3600
        points = (portfolio.total_balance / 100) * duration_hours * multiplier
        
        # Check if the total points exceed the maximum allowed
        if total_points_distributed + points > MAX_SESSION_1_POINTS:
            points = MAX_SESSION_1_POINTS - total_points_distributed
        
        # Create UserPoints entry
        user_points = UserPoints(
            vault_id=portfolio.vault_id,
            wallet_address=portfolio.user_address,
            points=points,
            partner_name="Harmonix",
            session_id=None  # or the specific session id if available
        )
        session.add(user_points)
        session.commit()
        
        total_points_distributed += points
        
        if total_points_distributed >= MAX_SESSION_1_POINTS:
            break

    logger.info("Points distribution job completed.")

if __name__ == "__main__":
    harmonix_distribute_points()