import secrets
from typing import Any, List, Union
from pydantic import AnyHttpUrl, validator
from pydantic_settings import BaseSettings

from pydantic import (
    AnyHttpUrl,
    HttpUrl,
    PostgresDsn,
    ValidationInfo,
    field_validator,
)


class Settings(BaseSettings):
    ENVIRONMENT_NAME: str

    @property
    def is_production(self):
        return self.ENVIRONMENT_NAME == "Production"


    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = secrets.token_urlsafe(32)
    # 60 minutes * 24 hours * 8 days = 8 days
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 30
    SERVER_NAME: str
    SERVER_HOST: AnyHttpUrl
    # BACKEND_CORS_ORIGINS is a JSON-formatted list of origins
    # e.g: '["http://localhost", "http://localhost:4200", "http://localhost:3000", \
    # "http://localhost:8080", "http://local.dockertoolbox.tiangolo.com"]'
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = []

    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    PROJECT_NAME: str
    ETHER_MAINNET_INFURA_URL: str = None
    ARBITRUM_MAINNET_INFURA_URL: str = (
        "https://arbitrum-mainnet.infura.io/v3/85cde589ce754dafa0a57001c326104d"
    )
    SEPOLIA_TESTNET_INFURA_WEBSOCKER_URL: str = (
        "wss://morning-distinguished-dream.ethereum-sepolia.quiknode.pro/4c29b83d4282a066bc116842a183fffecf764d3f"
    )

    SEPOLIA_TESTNET_INFURA_URL: str = (
        "https://sepolia.infura.io/v3/85cde589ce754dafa0a57001c326104d"
    )

    VAULT_FILTER_ADDRESS: str = "0xBcc65b5d2eC6b94509F8cF3d8208AaB22b4fd94B"
    DEPOSIT_VAULT_FILTER_TOPICS: str = "0x73a19dd210f1a7f902193214c0ee91dd35ee5b4d920cba8d519eca65a7b488ca"
    WITHDRAW_VAULT_FILTER_TOPICS: str = "0x92ccf450a286a957af52509bc1c9939d1a6a481783e142e41e2499f0bb66ebc6"

    WALLET_ADDRESS: str
    WSTETH_ADDRESS: str = "0x5979D7b546E38E414F7E9822514be443A4800529"
    USDC_ADDRESS: str = "0xaf88d065e77c8cC2239327C5EDb3A432268e5831"
    USDCE_ADDRESS: str = "0xFF970A61A04b1cA14834A43f5dE4533eBDDB5CC8"
    ROCKONYX_STABLECOIN_ADDRESS: str = "0x01CdC1dc16c677dfD4cFDE4478aAA494954657a0"
    ROCKONYX_DELTA_NEUTRAL_VAULT_ADDRESS: str

    POSTGRES_SERVER: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    SQLALCHEMY_DATABASE_URI: PostgresDsn | None = None

    @field_validator("SQLALCHEMY_DATABASE_URI", mode="before")
    def assemble_db_connection(cls, v: str | None, info: ValidationInfo) -> Any:
        if isinstance(v, str):
            return v
        return PostgresDsn.build(
            scheme="postgresql+psycopg",
            username=info.data.get("POSTGRES_USER"),
            password=info.data.get("POSTGRES_PASSWORD"),
            host=info.data.get("POSTGRES_SERVER"),
            path=f"{info.data.get('POSTGRES_DB') or ''}",
        )

    class Config:
        case_sensitive = True
        env_file = "../.env"


settings = Settings()
