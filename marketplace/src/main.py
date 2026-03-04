from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from contextlib import asynccontextmanager
import logging

from src.schemas import (
    ProductCreate, ProductUpdate,
    OrderCreate, OrderItemInput,
    PromoCodeCreate, PromoCodeUpdate,
    ErrorResponse
)

from src.database import engine
from src.api import products, orders, auth, promo_codes
from src.core.logging_middleware import LoggingMiddleware
from src.core.exceptions import create_error
from src.schemas import HealthResponse

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
    title="Marketplace API(HW2)",
    version="1.1.2",
    description="Marketplace CRUD + Orders Logic by Alex Pokrovskiy",
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


app.include_router(auth.router, prefix="/api/v1")
app.include_router(products.router, prefix="/api/v1")
app.include_router(orders.router, prefix="/api/v1")
app.include_router(promo_codes.router, prefix="/api/v1")


@app.get("/health", response_model=HealthResponse, tags=["System"])
def health_check():
    return {"status": "ok", "version": "1.0.0"}


@app.get("/", include_in_schema=False)
def root():
    return {"message": "API is running", "docs": "/docs"}

@app.get("/.well-known/schemas", include_in_schema=False, response_model=None)
def register_schemas(
    product_create: ProductCreate = None,
    product_update: ProductUpdate = None,
    order_create: OrderCreate = None,
    order_item_input: OrderItemInput = None,
    promo_code_create: PromoCodeCreate = None,
    promo_code_update: PromoCodeUpdate = None,
    error_response: ErrorResponse = None,
):
    pass
