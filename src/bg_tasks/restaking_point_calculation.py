"""
Implement the logic for calculating the restaking points for a user.
In our system, we have multiple vaults that have VaultCategory = points, we need to calculate points for all the restaking vaults.

1. define function to get earned points from vault address
2. define function to calculate restaking point distributions for each vault to users.

"""

import json
from typing import Dict, List
from sqlmodel import Session, col, select

from core.db import engine
from core import constants
from models.point_distribution_history import PointDistributionHistory
from models.user_points import UserPoints
from models.user_portfolio import PositionStatus, UserPortfolio
from models.vaults import Vault, VaultCategory
from schemas import EarnedRestakingPoints
from services import renzo_service
from services import zircuit_service

session = Session(engine)

GET_POINTS_SERVICE = {
    "renzo": renzo_service.get_points,
    "zircuit": zircuit_service.get_points,
}


def get_restaking_vaults_with_partner(partner_name) -> list[Vault]:
    """
    Get all vaults that have VaultCategory = points
    :return: list of vaults
    """
    vaults = session.exec(
        select(Vault)
        .where(Vault.category == VaultCategory.points)
        .where(Vault.routes != None)
        .where(col(Vault.routes).contains(partner_name))
    ).all()
    return vaults


def get_earned_points(
    vault_addresses: List[str], partner_name: str
) -> EarnedRestakingPoints:
    assert partner_name in GET_POINTS_SERVICE, f"Partner {partner_name} not supported"

    get_points_func = GET_POINTS_SERVICE[partner_name]

    points = EarnedRestakingPoints(
        total_points=0, eigen_layer_points=0, partner_name=partner_name
    )
    for vault_address in vault_addresses:
        p = get_points_func(vault_address)
        points.total_points += p.total_points
        points.eigen_layer_points += p.eigen_layer_points

    return points


def get_previous_point_distribution(partner_name: str) -> float:
    # get point distribution history for the vault
    prev_point_distribution = session.exec(
        select(PointDistributionHistory)
        .where(PointDistributionHistory.partner_name == partner_name)
        .order_by(PointDistributionHistory.created_at.desc())
    ).first()

    if prev_point_distribution is not None:
        prev_point = prev_point_distribution.point
    else:
        prev_point = 0

    return prev_point


def distribute_points_to_users(
    user_positions: List[UserPortfolio],
    earned_points: float,
    user_percentage: Dict[str, float],
    partner_name: str,
):
    """
    Distribute points to users based on their share percentages.
    """
    for user in user_positions:
        user_points = session.exec(
            select(UserPoints)
            .where(UserPoints.wallet_address == user.user_address)
            .where(UserPoints.partner_name == partner_name)
        ).first()
        if user_points:
            user_points.points += earned_points * user_percentage[user.user_address]

        else:
            user_points = UserPoints(
                wallet_address=user.user_address,
                points=earned_points * user_percentage[user.user_address],
                partner_name=partner_name,
            )

        session.add(user_points)


def calculate_point_distributions(vaults: list[Vault], partner_name: str):
    user_positions: List[UserPortfolio] = []
    vault_addresses = []

    for vault in vaults:
        vault_addresses.append(vault.contract_address)

        # get all users who have points in the vault
        positions = session.exec(
            select(UserPortfolio)
            .where(UserPortfolio.vault_id == vault.id)
            .where(UserPortfolio.status == PositionStatus.ACTIVE)
        ).all()

        user_positions.extend(positions)

    # calculate the percentage of shares for each user
    total_deposit_amount = sum([user.init_deposit for user in user_positions])
    user_percentage = {}
    for user in user_positions:
        pct = user.init_deposit / total_deposit_amount
        user_percentage[user.user_address] = pct

    # get earned points for the partner
    prev_point = get_previous_point_distribution(partner_name)
    total_earned_points = get_earned_points(vault_addresses, partner_name)

    # the job run every 12 hour, so we need to calculate the earned points in the last 12 hour
    earned_points_in_period = total_earned_points.total_points - prev_point

    # calculate user earn points in the period
    distribute_points_to_users(
        user_positions=user_positions,
        earned_points=earned_points_in_period,
        user_percentage=user_percentage,
        partner_name=partner_name,
    )

    # save the point distribution history
    point_distribution = PointDistributionHistory(
        partner_name=partner_name,
        point=total_earned_points.total_points,
    )
    session.add(point_distribution)

    if partner_name in {constants.RENZO, constants.KELPDAO}:
        # distribute eigenlayer points to user
        prev_eigen_point = get_previous_point_distribution(constants.EIGENLAYER)

        # the job run every 12 hour, so we need to calculate the earned points in the last 12 hour
        earned_eigen_points_in_period = (
            total_earned_points.eigen_layer_points - prev_eigen_point
        )

        distribute_points_to_users(
            user_positions=user_positions,
            earned_points=earned_eigen_points_in_period,
            user_percentage=user_percentage,
            partner_name=constants.EIGENLAYER,
        )

        # save the point distribution history
        point_distribution = PointDistributionHistory(
            partner_name=constants.EIGENLAYER,
            point=total_earned_points.eigen_layer_points,
        )
        session.add(point_distribution)

    session.commit()


def main():
    # get all vaults that have VaultCategory = points
    partners = [constants.RENZO, constants.ZIRCUIT]

    for partner in partners:
        vaults = get_restaking_vaults_with_partner(partner_name=partner)
        if len(vaults) > 0:
            calculate_point_distributions(vaults, partner_name=partner)

    session.commit()


if __name__ == "__main__":
    main()
