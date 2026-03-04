# src/main.py
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from contextlib import asynccontextmanager
import logging

from src.database import engine
from src.api import products, orders, auth, promo_codes
from src.core.logging_middleware import LoggingMiddleware
from src.core.exceptions import create_error

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("api_access")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Application startup")
    yield
    logger.info("Application shutdown")
    engine.dispose()


app = FastAPI(
    title="Marketplace API",
    version="1.0.0",
    description="Marketplace CRUD + Orders Logic",
    lifespan=lifespan
)

app.add_middleware(LoggingMiddleware)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=400,
        content={
            "error_code": "VALIDATION_ERROR",
            "message": "Validation Error",
            "details": exc.errors()
        }
    )


# Роутеры
app.include_router(auth.router, prefix="/api/v1")
app.include_router(products.router, prefix="/api/v1")
app.include_router(orders.router, prefix="/api/v1")
app.include_router(promo_codes.router, prefix="/api/v1")  # ← Добавлено


@app.get("/health", tags=["System"])
def health_check():
    return {"status": "ok", "version": "1.0.0"}


@app.get("/", include_in_schema=False)
def root():
    return {"message": "API is running", "docs": "/docs"}