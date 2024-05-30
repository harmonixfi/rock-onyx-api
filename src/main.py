from fastapi.exceptions import ValidationException
from fastapi.responses import JSONResponse
import uvicorn
from fastapi import FastAPI, Request
from api.api_v1.api import api_router
from starlette.middleware.cors import CORSMiddleware

from core.config import settings

app = FastAPI(
    title=settings.PROJECT_NAME, openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Set all CORS enabled origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:4000",
        "https://testnet.rockonyx.xyz",
        "https://rockonyx.xyz",
        "https://www.rockonyx.xyz",
        "https://testnet.harmonix.fi",
        "https://harmonix.fi",
        "https://www.harmonix.fi",
        "https://app.harmonix.fi",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(ValidationException)
async def validation_exception_handler(request: Request, exc: ValidationException):
    return JSONResponse(
        status_code=400,
        content={
            "error": "validation",
            "validation": {
                "error_code": exc.error_code,
                "error_message": exc.error_message,
            },
        },
    )


@app.exception_handler(Exception)
async def exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"error": str(exc)},
    )


app.include_router(api_router, prefix=settings.API_V1_STR)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
