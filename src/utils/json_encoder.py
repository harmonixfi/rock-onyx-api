from fastapi.encoders import jsonable_encoder
from datetime import datetime
from pytz import timezone
from typing import Any


def custom_encoder(obj: Any):
    if isinstance(obj, datetime):
        dt = obj.replace(tzinfo=timezone("UTC")).isoformat()
        return dt
    return jsonable_encoder(obj)
