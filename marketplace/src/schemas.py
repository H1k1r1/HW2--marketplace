# src/schemas.py
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime
from enum import Enum
import re


# === Enums ===
class ProductStatus(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    ARCHIVED = "ARCHIVED"


class OrderStatus(str, Enum):
    CREATED = "CREATED"
    PAYMENT_PENDING = "PAYMENT_PENDING"
    PAID = "PAID"
    SHIPPED = "SHIPPED"
    COMPLETED = "COMPLETED"
    CANCELED = "CANCELED"


class UserRole(str, Enum):
    USER = "USER"
    SELLER = "SELLER"
    ADMIN = "ADMIN"


class PromoDiscountType(str, Enum):
    PERCENTAGE = "PERCENTAGE"
    FIXED_AMOUNT = "FIXED_AMOUNT"


class OperationType(str, Enum):
    CREATE_ORDER = "CREATE_ORDER"
    UPDATE_ORDER = "UPDATE_ORDER"


# === Product Schemas ===
class ProductCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=4000)
    price: float = Field(..., gt=0)
    stock: int = Field(..., ge=0)
    category: str = Field(..., min_length=1, max_length=100)
    status: ProductStatus = ProductStatus.ACTIVE

    @field_validator('name')
    @classmethod
    def name_not_empty(cls, v):
        if not v.strip():
            raise ValueError('name cannot be empty or whitespace')
        return v


class ProductUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=4000)
    price: Optional[float] = Field(None, gt=0)
    stock: Optional[int] = Field(None, ge=0)
    category: Optional[str] = Field(None, min_length=1, max_length=100)
    status: Optional[ProductStatus] = None


class ProductResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    price: float
    stock: int
    category: str
    status: ProductStatus
    created_at: datetime
    updated_at: datetime
    seller_id: Optional[str]

    class Config:
        from_attributes = True


class ProductListResponse(BaseModel):
    items: List[ProductResponse]
    totalElements: int
    page: int
    size: int


# === Order Schemas ===
class OrderItemInput(BaseModel):
    product_id: str
    quantity: int = Field(..., ge=1, le=999)


class OrderCreate(BaseModel):
    items: List[OrderItemInput] = Field(..., min_length=1, max_length=50)
    promo_code: Optional[str] = Field(None, pattern=r'^[A-Z0-9_]{4,20}$')

    @field_validator('promo_code')
    @classmethod
    def promo_code_format(cls, v):
        if v and not re.match(r'^[A-Z0-9_]{4,20}$', v):
            raise ValueError('promo_code must match pattern ^[A-Z0-9_]{4,20}$ (uppercase only)')
        return v


class OrderItemResponse(BaseModel):
    product_id: str
    quantity: int
    price_at_order: float

    class Config:
        from_attributes = True


class OrderResponse(BaseModel):
    id: str
    user_id: str
    status: OrderStatus
    total_amount: float
    discount_amount: float
    created_at: datetime
    updated_at: datetime
    items: List[OrderItemResponse]

    class Config:
        from_attributes = True


# === Auth Schemas ===
class RegisterRequest(BaseModel):
    email: str = Field(..., pattern=r'^[^@]+@[^@]+\.[^@]+$')
    password: str = Field(..., min_length=8)
    role: UserRole = UserRole.USER


class LoginRequest(BaseModel):
    email: str = Field(..., pattern=r'^[^@]+@[^@]+\.[^@]+$')
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


# === Promo Code Schemas ===
class PromoCodeCreate(BaseModel):
    code: str = Field(..., pattern=r'^[A-Z0-9_]{4,20}$', description="Уникальный код (только заглавные буквы)")
    discount_type: PromoDiscountType
    discount_value: float = Field(..., gt=0)
    min_order_amount: float = Field(default=0, ge=0)
    max_uses: int = Field(default=1, ge=1)
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None
    active: bool = True

    @field_validator('code')
    @classmethod
    def code_uppercase(cls, v):
        if v != v.upper():
            raise ValueError('code must be UPPERCASE only (A-Z, 0-9, _)')
        return v


class PromoCodeResponse(BaseModel):
    id: str
    code: str
    discount_type: PromoDiscountType
    discount_value: float
    min_order_amount: float
    max_uses: int
    current_uses: int
    valid_from: Optional[datetime]
    valid_until: Optional[datetime]
    active: bool
    created_at: Optional[datetime]

    class Config:
        from_attributes = True


class PromoCodeListResponse(BaseModel):
    items: List[PromoCodeResponse]
    total: int


# === Error Schema ===
class ErrorResponse(BaseModel):
    error_code: str
    message: str
    details: Optional[dict] = None