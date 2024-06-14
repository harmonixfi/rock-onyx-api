from fastapi import APIRouter

from api.api_v1.endpoints import (
    vaults,
    portfolio,
    statistics,
    referral,
)

api_router = APIRouter()

api_router.include_router(
    vaults.router, prefix="/vaults"
)
api_router.include_router(
    portfolio.router, prefix="/portfolio"
)
api_router.include_router(
    statistics.router, prefix="/statistics"
)
api_router.include_router(
    referral.router, prefix="/referral"
)
api_router.redirect_slashes = False
