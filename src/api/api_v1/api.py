from fastapi import APIRouter

from api.api_v1.endpoints import (
    items,
    vaults
)

api_router = APIRouter()
# api_router.include_router(
#     items.router, prefix="/items"
# )
api_router.include_router(
    vaults.router, prefix="/vaults"
)
api_router.redirect_slashes = False
