from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException

router = APIRouter()


@router.get("/")
def read_items(
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """
    Retrieve items.
    """

    return "Ok"
