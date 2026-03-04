# src/api/promo_codes.py
from fastapi import APIRouter, Depends, Query, Body
from sqlalchemy.orm import Session
from datetime import datetime
import re

from src.database import get_db
from src.models import PromoCode, User
from src.core.security import get_current_user, require_role
from src.core.exceptions import create_error
from src.schemas import PromoCodeCreate, PromoCodeUpdate, PromoCodeResponse

router = APIRouter(prefix="/promo-codes", tags=["PromoCodes"])


@router.get("", response_model=dict)
def list_promo_codes(
    page: int = Query(default=0, ge=0),
    size: int = Query(default=20, ge=1, le=100),
    active: bool = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("SELLER", "ADMIN"))
):
    """Список промокодов"""
    query = db.query(PromoCode)
    
    if active is not None:
        query = query.filter(PromoCode.active == active)
    
    total = query.count()
    items = query.offset(page * size).limit(size).all()
    
    return {
        "items": [
            {
                "id": str(p.id),
                "code": p.code,
                "discount_type": p.discount_type,
                "discount_value": float(p.discount_value),
                "min_order_amount": float(p.min_order_amount) if p.min_order_amount else None,
                "max_uses": p.max_uses,
                "current_uses": p.current_uses,
                "valid_from": p.valid_from.isoformat() if p.valid_from else None,
                "valid_until": p.valid_until.isoformat() if p.valid_until else None,
                "active": p.active,
            }
            for p in items
        ],
        "totalElements": total,
        "page": page,
        "size": size
    }


@router.get("/{promo_id}", response_model=PromoCodeResponse)
def get_promo_code(
    promo_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("SELLER", "ADMIN"))
):
    """Получение промокода по ID"""
    promo = db.query(PromoCode).filter(PromoCode.id == promo_id).first()
    if not promo:
        raise create_error("PROMO_CODE_INVALID")
    
    return {
        "id": str(promo.id),
        "code": promo.code,
        "discount_type": promo.discount_type,
        "discount_value": float(promo.discount_value),
        "min_order_amount": float(promo.min_order_amount) if promo.min_order_amount else None,
        "max_uses": promo.max_uses,
        "current_uses": promo.current_uses,
        "valid_from": promo.valid_from.isoformat() if promo.valid_from else None,
        "valid_until": promo.valid_until.isoformat() if promo.valid_until else None,
        "active": promo.active,
    }


@router.post("", status_code=201, response_model=PromoCodeResponse)
def create_promo_code(
    promo_: PromoCodeCreate = Body(...),  # ← ✅ ИСПРАВЛЕНО: promo_: PromoCodeCreate
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("SELLER", "ADMIN"))
):
    """Создание промокода"""
    
    # ← ✅ ИСПОЛЬЗУЙТЕ promo_, а не promo_data!
    code = promo_.code.strip()              # ← promo_.code
    
    if not re.match(r'^[A-Z0-9_]{4,20}$', code):
        raise create_error(
            "VALIDATION_ERROR",
            details={"code": "must match pattern ^[A-Z0-9_]{4,20}$"}
        )
    
    existing = db.query(PromoCode).filter(PromoCode.code == code).first()
    if existing:
        raise create_error("VALIDATION_ERROR", details={"code": "already exists"})
    
    if promo_.discount_value <= 0:           # ← promo_.discount_value
        raise create_error("VALIDATION_ERROR", details={"discount_value": "must be > 0"})
    
    if promo_.discount_type == "PERCENTAGE" and promo_.discount_value > 100:
        raise create_error("VALIDATION_ERROR", details={"discount_value": "percentage cannot exceed 100"})
    
    new_promo = PromoCode(
        code=code,
        discount_type=promo_.discount_type,      # ← promo_.discount_type
        discount_value=promo_.discount_value,    # ← promo_.discount_value
        min_order_amount=promo_.min_order_amount, # ← promo_.min_order_amount
        max_uses=promo_.max_uses,                # ← promo_.max_uses
        current_uses=0,
        valid_from=promo_.valid_from,            # ← promo_.valid_from
        valid_until=promo_.valid_until,          # ← promo_.valid_until
        active=promo_.active                     # ← promo_.active
    )
    
    db.add(new_promo)
    db.commit()
    db.refresh(new_promo)
    
    return {
        "id": str(new_promo.id),
        "code": new_promo.code,
        "discount_type": new_promo.discount_type,
        "discount_value": float(new_promo.discount_value),
        "min_order_amount": float(new_promo.min_order_amount) if new_promo.min_order_amount else None,
        "max_uses": new_promo.max_uses,
        "current_uses": new_promo.current_uses,
        "valid_from": new_promo.valid_from.isoformat() if new_promo.valid_from else None,
        "valid_until": new_promo.valid_until.isoformat() if new_promo.valid_until else None,
        "active": new_promo.active,
    }


@router.put("/{promo_id}", response_model=PromoCodeResponse)
def update_promo_code(
    promo_id: str,
    promo_: PromoCodeUpdate = Body(...),  # ← ✅ ИСПРАВЛЕНО: promo_: PromoCodeUpdate
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("SELLER", "ADMIN"))
):
    """Обновление промокода"""
    
    promo = db.query(PromoCode).filter(PromoCode.id == promo_id).first()
    if not promo:
        raise create_error("PROMO_CODE_INVALID")
    
    # ← ✅ ИСПОЛЬЗУЙТЕ promo_, а не promo_data!
    update_data = promo_.dict(exclude_unset=True)  # ← promo_.dict()
    for field, value in update_data.items():
        setattr(promo, field, value)
    
    db.commit()
    db.refresh(promo)
    
    return {
        "id": str(promo.id),
        "code": promo.code,
        "discount_type": promo.discount_type,
        "discount_value": float(promo.discount_value),
        "min_order_amount": float(promo.min_order_amount) if promo.min_order_amount else None,
        "max_uses": promo.max_uses,
        "current_uses": promo.current_uses,
        "valid_from": promo.valid_from.isoformat() if promo.valid_from else None,
        "valid_until": promo.valid_until.isoformat() if promo.valid_until else None,
        "active": promo.active,
    }


@router.delete("/{promo_id}", status_code=204)
def delete_promo_code(
    promo_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("ADMIN"))
):
    """Удаление промокода"""
    
    promo = db.query(PromoCode).filter(PromoCode.id == promo_id).first()
    if not promo:
        raise create_error("PROMO_CODE_INVALID")
    
    db.delete(promo)
    db.commit()
    
    return None