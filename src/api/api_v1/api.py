from fastapi import APIRouter

from api.api_v1.endpoints import (
    vaults,
    portfolio
)

api_router = APIRouter()

api_router.include_router(
    vaults.router, prefix="/vaults"
)
api_router.include_router(
    portfolio.router, prefix="/portfolio"
)
api_router.redirect_slashes = False
