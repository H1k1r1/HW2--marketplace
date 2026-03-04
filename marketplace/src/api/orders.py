# src/api/orders.py
from fastapi import APIRouter, Depends, Query, Body
from sqlalchemy.orm import Session

from src.database import get_db
from src.models import User, Order, OrderStatusEnum
from src.core.security import get_current_user, require_role
from src.core.exceptions import create_error
from src.services.order_service import OrderService
from src.schemas import OrderCreate, OrderResponse, OrderListResponse

router = APIRouter(prefix="/orders", tags=["Orders"])


@router.get("", response_model=OrderListResponse)
def list_orders(
    page: int = Query(default=0, ge=0),
    size: int = Query(default=20, ge=1, le=100),
    status: str = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Список заказов с пагинацией"""
    
    query = db.query(Order)
    
    if current_user.role.value == "SELLER":
        raise create_error("ACCESS_DENIED")
    
    if current_user.role.value == "USER":
        query = query.filter(Order.user_id == current_user.id)
    
    if status:
        query = query.filter(Order.status == status)
    
    total = query.count()
    items = query.offset(page * size).limit(size).all()
    
    return {
        "items": [
            {
                "id": str(o.id),
                "user_id": str(o.user_id),
                "status": o.status.value,
                "total_amount": float(o.total_amount),
                "discount_amount": float(o.discount_amount),
                "created_at": o.created_at.isoformat() if o.created_at else None,
                "updated_at": o.updated_at.isoformat() if o.updated_at else None,
                "items": [
                    {
                        "product_id": str(i.product_id),
                        "quantity": i.quantity,
                        "price_at_order": float(i.price_at_order)
                    }
                    for i in o.items
                ]
            }
            for o in items
        ],
        "totalElements": total,
        "page": page,
        "size": size
    }


@router.post("", status_code=201, response_model=OrderResponse)
def create_order(
    order_: OrderCreate = Body(...),  # ← ✅ ИСПРАВЛЕНО: order_: OrderCreate
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("USER", "ADMIN"))
):
    """Создание заказа"""
    
    if current_user.role.value == "SELLER":
        raise create_error("ACCESS_DENIED")
    
    service = OrderService(db, current_user)
    order = service.create_order(
        items_data=[item.dict() for item in order_.items],  # ← ✅ order_.items
        promo_code_str=order_.promo_code                      # ← ✅ order_.promo_code
    )
    
    return {
        "id": str(order.id),
        "user_id": str(order.user_id),
        "status": order.status.value,
        "total_amount": float(order.total_amount),
        "discount_amount": float(order.discount_amount),
        "created_at": order.created_at.isoformat() if order.created_at else None,
        "updated_at": order.updated_at.isoformat() if order.updated_at else None,
        "items": [
            {
                "product_id": str(i.product_id),
                "quantity": i.quantity,
                "price_at_order": float(i.price_at_order)
            }
            for i in order.items
        ]
    }


@router.get("/{order_id}", response_model=OrderResponse)
def get_order(
    order_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Получение заказа по ID"""
    
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise create_error("ORDER_NOT_FOUND")
    
    if current_user.role.value == "SELLER":
        raise create_error("ACCESS_DENIED")
    if current_user.role.value == "USER" and order.user_id != current_user.id:
        raise create_error("ORDER_OWNERSHIP_VIOLATION")
    
    return {
        "id": str(order.id),
        "user_id": str(order.user_id),
        "status": order.status.value,
        "total_amount": float(order.total_amount),
        "discount_amount": float(order.discount_amount),
        "created_at": order.created_at.isoformat() if order.created_at else None,
        "updated_at": order.updated_at.isoformat() if order.updated_at else None,
        "items": [
            {
                "product_id": str(i.product_id),
                "quantity": i.quantity,
                "price_at_order": float(i.price_at_order)
            }
            for i in order.items
        ]
    }


@router.put("/{order_id}", response_model=OrderResponse)
def update_order(
    order_id: str,
    order_: OrderCreate = Body(...),  # ← ✅ ИСПРАВЛЕНО: order_: OrderCreate
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Обновление заказа"""
    
    if current_user.role.value == "SELLER":
        raise create_error("ACCESS_DENIED")
    
    service = OrderService(db, current_user)
    order = service.update_order(
        order_id=order_id,
        items_data=[item.dict() for item in order_.items]  # ← ✅ order_.items
    )
    
    return {
        "id": str(order.id),
        "user_id": str(order.user_id),
        "status": order.status.value,
        "total_amount": float(order.total_amount),
        "discount_amount": float(order.discount_amount),
        "created_at": order.created_at.isoformat() if order.created_at else None,
        "updated_at": order.updated_at.isoformat() if order.updated_at else None,
        "items": [
            {
                "product_id": str(i.product_id),
                "quantity": i.quantity,
                "price_at_order": float(i.price_at_order)
            }
            for i in order.items
        ]
    }


@router.post("/{order_id}/cancel", response_model=OrderResponse)
def cancel_order(
    order_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Отмена заказа"""
    
    if current_user.role.value == "SELLER":
        raise create_error("ACCESS_DENIED")
    
    service = OrderService(db, current_user)
    order = service.cancel_order(order_id=order_id)
    
    return {
        "id": str(order.id),
        "user_id": str(order.user_id),
        "status": order.status.value,
        "total_amount": float(order.total_amount),
        "discount_amount": float(order.discount_amount),
        "created_at": order.created_at.isoformat() if order.created_at else None,
        "updated_at": order.updated_at.isoformat() if order.updated_at else None,
        "items": [
            {
                "product_id": str(i.product_id),
                "quantity": i.quantity,
                "price_at_order": float(i.price_at_order)
            }
            for i in order.items
        ]
    }