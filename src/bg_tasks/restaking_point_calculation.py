"""
Implement the logic for calculating the restaking points for a user.
In our system, we have multiple vaults that have VaultCategory = points, we need to calculate points for all the restaking vaults.

1. define function to get earned points from vault address
2. define function to calculate restaking point distributions for each vault to users.

"""

from sqlmodel import Session, select

from core.db import engine
from models.vaults import Vault

session = Session(engine)


def get_restaking_vaults():
    """
    Get all vaults that have VaultCategory = points
    :return: list of vaults
    """
    vaults = session.exec(
        select(Vault).where(Vault.vault_capacity == VaultCategory.points)
    ).all()


def main():
    # get all vaults that have VaultCategory = points

    vaults = get_restaking_vaults()
    pass
