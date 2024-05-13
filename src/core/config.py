import secrets
from typing import Any, List, Optional, Union
from pydantic import AnyHttpUrl, Extra, validator
from pydantic_settings import BaseSettings

from pydantic import (
    AnyHttpUrl,
    HttpUrl,
    PostgresDsn,
    ValidationInfo,
    field_validator,
)
from web3 import Web3


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
    ETHER_MAINNET_INFURA_URL: str | None = None
    ARBITRUM_MAINNET_INFURA_URL: str = (
        "https://arbitrum-mainnet.infura.io/v3/85cde589ce754dafa0a57001c326104d"
    )
    ARBITRUM_MAINNET_INFURA_WEBSOCKER_URL: str = (
        "wss://restless-falling-season.arbitrum-mainnet.quiknode.pro/738a8e5fbc70d4ccbcb1d7bb9ff6c98da481e523/"
    )
    SEPOLIA_TESTNET_INFURA_WEBSOCKER_URL: str = (
        "wss://restless-falling-season.arbitrum-mainnet.quiknode.pro/738a8e5fbc70d4ccbcb1d7bb9ff6c98da481e523/"
    )

    SEPOLIA_TESTNET_INFURA_URL: str = (
        "https://arbitrum-mainnet.infura.io/v3/85cde589ce754dafa0a57001c326104d"
    )

    WALLET_ADDRESS: str
    WSTETH_ADDRESS: str = "0x5979D7b546E38E414F7E9822514be443A4800529"
    USDC_ADDRESS: str = "0xaf88d065e77c8cC2239327C5EDb3A432268e5831"
    USDCE_ADDRESS: str = "0xFF970A61A04b1cA14834A43f5dE4533eBDDB5CC8"
    ROCKONYX_STABLECOIN_ADDRESS: str
    ROCKONYX_DELTA_NEUTRAL_VAULT_ADDRESS: str
    ROCKONYX_RESTAKING_DELTA_NEUTRAL_VAULT_ADDRESS: str
    ROCKONYX_USDCE_USDC_PRICE_FEED_ADDRESS: str
    USDCE_USDC_CAMELOT_POOL_ADDRESS: str

    STABLECOIN_DEPOSIT_VAULT_FILTER_TOPICS: str = Web3.solidity_keccak(
        ["string"], ["Deposited(address,uint256,uint256)"]
    ).hex()
    STABLECOIN_INITIATE_WITHDRAW_VAULT_FILTER_TOPICS: str = Web3.solidity_keccak(
        ["string"], ["InitiateWithdrawal(address,uint256,uint256)"]
    ).hex()
    STABLECOIN_COMPLETE_WITHDRAW_VAULT_FILTER_TOPICS: str = Web3.solidity_keccak(
        ["string"], ["Withdrawn(address,uint256,uint256)"]
    ).hex()

    DELTA_NEUTRAL_DEPOSIT_EVENT_TOPIC: str = Web3.solidity_keccak(
        ["string"], ["Deposited(address,uint256,uint256)"]
    ).hex()
    DELTA_NEUTRAL_INITIATE_WITHDRAW_EVENT_TOPIC: str = Web3.solidity_keccak(
        ["string"], ["RequestFunds(address,uint256,uint256)"]
    ).hex()
    DELTA_NEUTRAL_COMPLETE_WITHDRAW_EVENT_TOPIC: str = Web3.solidity_keccak(
        ["string"], ["Withdrawn(address,uint256,uint256)"]
    ).hex()
    DELTA_NEUTRAL_POSITION_OPENED_EVENT_TOPIC: str = Web3.solidity_keccak(
        ["string"], ["PositionOpened(uint256,uint256,uint256,uint256)"]
    ).hex()
    DELTA_NEUTRAL_POSITION_CLOSED_EVENT_TOPIC: str = Web3.solidity_keccak(
        ["string"], ["PositionOpened(uint256,uint256,uint256,uint256,uint256,uint256,uint256)"]
    ).hex()

    OWNER_WALLET_ADDRESS: str
    OWNER_WALLET_PRIVATEKEY: str

    POSTGRES_SERVER: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    SQLALCHEMY_DATABASE_URI: PostgresDsn | None = None

    PYTHONPATH: Optional[str] = None
    NODE_ENV: Optional[str] = None
    NEXT_PUBLIC_THIRD_WEB_CLIENT_ID: Optional[str] = None
    NEXT_PUBLIC_API_URL: Optional[str] = None
    NEXT_PUBLIC_ROCK_ONYX_USDT_VAULT_ADDRESS: Optional[str] = None
    NEXT_PUBLIC_USDC_ADDRESS: Optional[str] = None

    ARBISCAN_API_KEY: str
    ARBISCAN_GET_TRANSACTIONS_URL: str = "https://api.arbiscan.io/api?module=account&action=txlist"
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
        extra = "allow"


settings = Settings()
