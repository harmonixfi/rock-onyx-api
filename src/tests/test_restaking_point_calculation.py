from typing import List
from unittest.mock import patch

import pytest
from sqlalchemy.orm import Session

from bg_tasks.restaking_point_calculation import main
from core import constants
from core.db import engine
from models import UserPoints, UserPortfolio, Vault, PointDistributionHistory
from schemas import EarnedRestakingPoints


@pytest.fixture(scope="module")
def db_session():
    session = Session(engine)
    yield session


@pytest.fixture(autouse=True)
def clean_user_portfolio(db_session: Session):
    db_session.query(PointDistributionHistory).delete()
    db_session.query(UserPoints).delete()
    db_session.query(UserPortfolio).delete()
    db_session.query(Vault).delete()
    db_session.commit()


def insert_test_data_case_1(session: Session):
    # Insert test data into Vaults table
    vault = Vault(
        name="Renzo Arb",
        contract_address="0x55c4c840f9ac2e62efa3f12bba1b57a12086f5",
        routes='["renzo"]',
        category="points",
        network_chain="arbitrum_one",
    )
    session.add(vault)

    # Insert test data into UserPortfolio table
    user_portfolio = UserPortfolio(
        vault_id=vault.id,
        user_address="0xBC05da14287317FE12B1a2b5a0E1d756Ff1801Aa",
        total_balance=1000,
        init_deposit=1000,
        total_shares=1000,
    )
    session.add(user_portfolio)

    session.commit()


@patch("bg_tasks.restaking_point_calculation.get_earned_points")
def test_calculate_points_case1(mock_get_points, db_session: Session):
    insert_test_data_case_1(db_session)

    # Arrange
    mock_get_points.return_value = EarnedRestakingPoints(
        total_points=100, eigen_layer_points=50, partner_name=constants.RENZO
    )
    user_address = "0xBC05da14287317FE12B1a2b5a0E1d756Ff1801Aa"
    vault_id = "ac14be54-f9bf-43c5-ac3d-e7fb23f19e7e"

    # Act
    main()

    # Assert
    renzo_points = (
        db_session.query(UserPoints)
        .filter_by(wallet_address=user_address, partner_name=constants.RENZO)
        .first()
    )
    assert renzo_points.points == 100

    eigenlayer_points = (
        db_session.query(UserPoints)
        .filter_by(wallet_address=user_address, partner_name=constants.EIGENLAYER)
        .first()
    )
    assert eigenlayer_points.points == 50

    point_distribution = (
        db_session.query(PointDistributionHistory)
        .filter_by(partner_name=constants.RENZO)
        .first()
    )
    assert point_distribution.point == 100

    point_distribution = (
        db_session.query(PointDistributionHistory)
        .filter_by(partner_name=constants.EIGENLAYER)
        .first()
    )
    assert point_distribution.point == 50


def insert_test_data_case_2(session: Session):
    # Insert test data into Vaults table
    vault = Vault(
        name="Renzo Arb",
        contract_address="0x55c4c840f9ac2e62efa3f12bba1b57a12086f5",
        routes='["renzo", "zircuit"]',
        category="points",
        network_chain="arbitrum_one",
    )
    session.add(vault)

    # Insert test data into UserPortfolio table
    user_portfolios = [
        UserPortfolio(
            vault_id=vault.id,
            user_address="0xBC05da14287317FE12B1a2b5a0E1d756Ff1801Aa",
            total_balance=1000,
            init_deposit=1000,
            total_shares=1000,
        ),
        UserPortfolio(
            vault_id=vault.id,
            user_address="0xBC05da14287317FE12B1a2b5a0E1d756Ff1802Aa",
            total_balance=500,
            init_deposit=500,
            total_shares=500,
        ),
    ]
    for user_portfolio in user_portfolios:
        session.add(user_portfolio)

    session.commit()


def mock_get_earned_points(vault_address: str, partner_name: str):
    if partner_name == constants.RENZO:
        return EarnedRestakingPoints(
            total_points=100,
            eigen_layer_points=100,
            partner_name=partner_name,
        )
    elif partner_name == constants.ZIRCUIT:
        return EarnedRestakingPoints(
            total_points=100,
            eigen_layer_points=100,
            partner_name=partner_name,
        )


# Test case
@patch(
    "bg_tasks.restaking_point_calculation.get_earned_points",
    new=mock_get_earned_points,
)
def test_calculate_points_case2(db_session: Session):
    insert_test_data_case_2(db_session)

    # Act
    main()

    user1 = "0xBC05da14287317FE12B1a2b5a0E1d756Ff1801Aa"
    user2 = "0xBC05da14287317FE12B1a2b5a0E1d756Ff1802Aa"
    user1_points = (
        db_session.query(UserPoints)
        .filter_by(wallet_address=user1)
        .all()
    )
    # filter user1_points by renzo
    assert len(user1_points) > 0
    renzo_points = next(filter(lambda x: x.partner_name == constants.RENZO, user1_points))
    assert round(renzo_points.points, 2) == 66.67

    zircuit_points = next(filter(lambda x: x.partner_name == constants.ZIRCUIT, user1_points))
    assert round(zircuit_points.points, 2) == 66.67

    eigen_points = next(filter(lambda x: x.partner_name == constants.EIGENLAYER, user1_points))
    assert round(eigen_points.points, 2) == 66.67

    user2_points = (
        db_session.query(UserPoints)
        .filter_by(wallet_address=user2)
        .all()
    )
    # filter user1_points by renzo
    assert len(user2_points) > 0
    renzo_points = next(filter(lambda x: x.partner_name == constants.RENZO, user2_points))
    assert round(renzo_points.points, 2) == 33.33

    zircuit_points = next(filter(lambda x: x.partner_name == constants.ZIRCUIT, user2_points))
    assert round(zircuit_points.points, 2) == 33.33

    eigen_points = next(filter(lambda x: x.partner_name == constants.EIGENLAYER, user2_points))
    assert round(eigen_points.points, 2) == 33.33
