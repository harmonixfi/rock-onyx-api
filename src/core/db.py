from datetime import datetime
from sqlalchemy import func
from sqlmodel import Session, create_engine, select

import crud
from core.config import settings
from models.pps_history import PricePerShareHistory
from models.vault_performance import VaultPerformance
from models.vaults import NetworkChain, Vault

engine = create_engine(str(settings.SQLALCHEMY_DATABASE_URI))


# make sure all SQLModel models are imported (models) before initializing DB
# otherwise, SQLModel might fail to initialize relationships properly
# for more details: https://github.com/tiangolo/full-stack-fastapi-postgresql/issues/28


def init_pps_history(session: Session, vault: Vault):
    cnt = session.exec(
        select(func.count()).select_from(PricePerShareHistory).where(
            PricePerShareHistory.vault_id == vault.id
        )
    ).one()

    if cnt == 0:
        pps_history_data = [
            PricePerShareHistory(
                datetime=datetime(2024, 1, 31), price_per_share=1, vault_id=vault.id
            )
        ]

        for pps in pps_history_data:
            session.add(pps)

        session.commit()


def seed_stablecoin_pps_history(session: Session, vault: Vault):
    cnt = session.exec(select(func.count()).select_from(PricePerShareHistory)).one()
    if cnt == 0:
        pps_history_data = [
            PricePerShareHistory(
                datetime=datetime(2024, 1, 31), price_per_share=1, vault_id=vault.id
            ),
            PricePerShareHistory(
                datetime=datetime(2024, 2, 9), price_per_share=1.0000, vault_id=vault.id
            ),
            PricePerShareHistory(
                datetime=datetime(2024, 2, 16),
                price_per_share=1.043481,
                vault_id=vault.id,
            ),
            PricePerShareHistory(
                datetime=datetime(2024, 2, 23),
                price_per_share=1.066503,
                vault_id=vault.id,
            ),
            PricePerShareHistory(
                datetime=datetime(2024, 3, 1),
                price_per_share=1.151802,
                vault_id=vault.id,
            ),
        ]

        for pps in pps_history_data:
            session.add(pps)

        session.commit()


def seed_vault_performance(stablecoin_vault: Vault, session):
    cnt = session.exec(select(func.count()).select_from(VaultPerformance)).one()
    if cnt == 0:
        if stablecoin_vault:
            vault_performances = [
                VaultPerformance(
                    datetime=datetime(2024, 2, 9),
                    total_locked_value=650.469078,
                    apy_1m=0,
                    apy_1w=0,
                    benchmark=2454.89,
                    pct_benchmark=1.451064143,
                    vault_id=stablecoin_vault.id,
                ),
                VaultPerformance(
                    datetime=datetime(2024, 2, 16),
                    total_locked_value=1148.814994,
                    apy_1m=67.89769076,
                    apy_1w=821.4619023,
                    benchmark=2822.835139,
                    pct_benchmark=16.65668528,
                    vault_id=stablecoin_vault.id,
                ),
                VaultPerformance(
                    datetime=datetime(2024, 2, 23),
                    total_locked_value=1175.957697,
                    apy_1m=118.9935637,
                    apy_1w=212.2583925,
                    benchmark=3028.727421,
                    pct_benchmark=23.37528042,
                    vault_id=stablecoin_vault.id,
                ),
                VaultPerformance(
                    datetime=datetime(2024, 3, 1),
                    total_locked_value=1253.815827,
                    apy_1m=458.8042689,
                    apy_1w=5440.514972,
                    benchmark=3366.58661,
                    pct_benchmark=37.13798215,
                    vault_id=stablecoin_vault.id,
                ),
            ]

            for vp in vault_performances:
                session.add(vp)

        session.commit()


def init_db(session: Session) -> None:
    # Create initial data
    vaults = [
        Vault(
            name="Options Wheel Vault",
            vault_capacity=4 * 1e6,
            vault_currency="USDC",
            contract_address=settings.ROCKONYX_STABLECOIN_ADDRESS,
            slug="options-wheel-vault",
        ),
        Vault(
            name="Delta Neutral Vault",
            vault_capacity=4 * 1e6,
            vault_currency="USDC",
            contract_address=settings.ROCKONYX_DELTA_NEUTRAL_VAULT_ADDRESS,
            slug="delta-neutral-vault",
        ),
        Vault(
            name="Restaking Delta Neutral Vault",
            vault_capacity=4 * 1e6,
            vault_currency="USDC",
            contract_address=settings.ROCKONYX_RENZO_RESTAKING_DELTA_NEUTRAL_VAULT_ADDRESS,
            slug="renzo-zircuit-restaking-delta-neutral-vault",
            routes="['renzo', 'zircuit']",
            category="points",
            network_chain=NetworkChain.ethereum,
        ),
        Vault(
            name="Restaking Delta Neutral Vault",
            vault_capacity=4 * 1e6,
            vault_currency="USDC",
            contract_address=settings.ROCKONYX_KELPDAO_RESTAKING_DELTA_NEUTRAL_VAULT_ADDRESS,
            slug="kelpdao-restaking-delta-neutral-vault",
            routes="['kelpdao']",
            category="points",
            network_chain=NetworkChain.arbitrum_one,
        ),
    ]

    for vault in vaults:
        existing_vault = session.exec(
            select(Vault).where(Vault.slug == vault.slug)
        ).first()
        if not existing_vault:
            session.add(vault)

    session.commit()

    # Seed data for VaultPerformance for Stablecoin Vault
    stablecoin_vault = session.exec(
        select(Vault).where(Vault.name == "Options Wheel Vault")
    ).first()

    seed_vault_performance(stablecoin_vault, session)
    seed_stablecoin_pps_history(session, stablecoin_vault)

    renzo_zircuit_restaking = session.exec(
        select(Vault).where(Vault.slug == "renzo-zircuit-restaking-delta-neutral-vault")
    ).first()
    init_pps_history(session, renzo_zircuit_restaking)

    renzo_zircuit_restaking = session.exec(
        select(Vault).where(Vault.slug == "kelpdao-restaking-delta-neutral-vault")
    ).first()
    init_pps_history(session, renzo_zircuit_restaking)
