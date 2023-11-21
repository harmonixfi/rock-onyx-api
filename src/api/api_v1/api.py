from fastapi import APIRouter

from api.api_v1.endpoints import (
    items
)

api_router = APIRouter()
api_router.include_router(
    items, prefix="/items"
)
api_router.redirect_slashes = False
