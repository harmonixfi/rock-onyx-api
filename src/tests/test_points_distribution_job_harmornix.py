from typing import List
from unittest.mock import patch

import pytest
from sqlalchemy.orm import Session

from bg_tasks.restaking_point_calculation import main
from core import constants
from core.db import engine
from models import UserPoints, UserPortfolio, Vault, PointDistributionHistory
from models.points_multiplier_config import PointsMultiplierConfig
from models.reward_session_config import RewardSessionConfig
from models.reward_sessions import RewardSessions
from models.user_points import UserPointAudit
from models.user_points_history import UserPointsHistory
from schemas import EarnedRestakingPoints

@pytest.fixture
def db_session():
    session = Session(engine)
    yield session

@pytest.fixture(autouse=True)
def clean_db(db_session: Session):
    db_session.query(UserPointsHistory).delete()
    db_session.query(UserPoints).delete()
    db_session.query(PointsMultiplierConfig).delete()
    db_session.query(UserPortfolio).delete()
    db_session.query(Vault).delete()
    db_session.query(RewardSessionConfig).delete()
    db_session.query(RewardSessions).delete()
    db_session.commit()

def insert_test_data_case_1(session: Session):
    