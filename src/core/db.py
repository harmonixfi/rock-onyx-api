from sqlmodel import Session, create_engine, select

import crud
from core.config import settings
from models.vaults import Vault

engine = create_engine(str(settings.SQLALCHEMY_DATABASE_URI))


# make sure all SQLModel models are imported (models) before initializing DB
# otherwise, SQLModel might fail to initialize relationships properly
# for more details: https://github.com/tiangolo/full-stack-fastapi-postgresql/issues/28


def init_db(session: Session) -> None:
    # Tables should be created with Alembic migrations
    # But if you don't want to use migrations, create
    # the tables un-commenting the next lines
    # from sqlmodel import SQLModel

    # from core.engine import engine
    # This works because the models are already imported and registered from models
    # SQLModel.metadata.create_all(engine)

    # Create initial data
    vault1 = Vault(
        name="Stablecoin Vault", vault_capacity=4 * 1e6, vault_currency="USDC"
    )
    vault2 = Vault(name="Delta Neutral Vault", vault_capacity=4 * 1e6, vault_currency="USDC")
    session.add(vault1)
    session.add(vault2)
    session.commit()
