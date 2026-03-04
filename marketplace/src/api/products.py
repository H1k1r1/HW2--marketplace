from fastapi import APIRouter, Depends, Query, Body
from sqlalchemy.orm import Session
from datetime import datetime

from src.database import get_db
from src.models import Product, ProductStatusEnum, User
from src.core.security import get_current_user, require_role
from src.core.exceptions import create_error
from src.schemas import ProductCreate, ProductUpdate, ProductResponse, ProductListResponse

router = APIRouter(prefix="/products", tags=["Products"])


@router.get("", response_model=ProductListResponse)
def list_products(
    page: int = Query(default=0, ge=0),
    size: int = Query(default=20, ge=1, le=100),
    status: str = Query(default=None),
    category: str = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Product)
    if status:
        query = query.filter(Product.status == status)
    if category:
        query = query.filter(Product.category == category)
    
    total = query.count()
    items = query.offset(page * size).limit(size).all()
    
    return {
        "items": [
            {
                "id": str(p.id),
                "name": p.name,
                "description": p.description,
                "price": float(p.price),
                "stock": p.stock,
                "category": p.category,
                "status": p.status.value,
                "created_at": p.created_at.isoformat() if p.created_at else None,
                "updated_at": p.updated_at.isoformat() if p.updated_at else None,
                "seller_id": str(p.seller_id) if p.seller_id else None,
            }
            for p in items
        ],
        "totalElements": total,
        "page": page,
        "size": size
    }


@router.get("/{product_id}", response_model=ProductResponse)
def get_product(
    product_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise create_error("PRODUCT_NOT_FOUND")
    
    return {
        "id": str(product.id),
        "name": product.name,
        "description": product.description,
        "price": float(product.price),
        "stock": product.stock,
        "category": product.category,
        "status": product.status.value,
        "created_at": product.created_at.isoformat() if product.created_at else None,
        "updated_at": product.updated_at.isoformat() if product.updated_at else None,
        "seller_id": str(product.seller_id) if product.seller_id else None,
    }


@router.post("", status_code=201, response_model=ProductResponse)
def create_product(
    product_: ProductCreate = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("SELLER", "ADMIN"))
):
    new_product = Product(
        name=product_.name,
        description=product_.description,
        price=product_.price,
        stock=product_.stock,
        category=product_.category,
        status=product_.status,
        seller_id=current_user.id if current_user.role.value == "SELLER" else None
    )
    
    db.add(new_product)
    db.commit()
    db.refresh(new_product)
    
    return {
        "id": str(new_product.id),
        "name": new_product.name,
        "description": new_product.description,
        "price": float(new_product.price),
        "stock": new_product.stock,
        "category": new_product.category,
        "status": new_product.status.value,
        "created_at": new_product.created_at.isoformat(),
        "updated_at": new_product.updated_at.isoformat(),
        "seller_id": str(new_product.seller_id) if new_product.seller_id else None,
    }


@router.put("/{product_id}", response_model=ProductResponse)
def update_product(
    product_id: str,
    product_: ProductUpdate = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("SELLER", "ADMIN"))
):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise create_error("PRODUCT_NOT_FOUND")
    
    if current_user.role.value == "SELLER" and product.seller_id != current_user.id:
        raise create_error("ACCESS_DENIED")
    
    update_data = product_.dict(exclude_unset=True)
    for field, value in update_data.items():
        if field == "status" and value:
            value = ProductStatusEnum[value] if isinstance(value, str) else value
        setattr(product, field, value)
    
    product.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(product)
    
    return {
        "id": str(product.id),
        "name": product.name,
        "description": product.description,
        "price": float(product.price),
        "stock": product.stock,
        "category": product.category,
        "status": product.status.value,
        "created_at": product.created_at.isoformat(),
        "updated_at": product.updated_at.isoformat(),
        "seller_id": str(product.seller_id) if product.seller_id else None,
    }


@router.delete("/{product_id}", status_code=204)
def delete_product(
    product_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("SELLER", "ADMIN"))
):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise create_error("PRODUCT_NOT_FOUND")
    
    if current_user.role.value == "SELLER" and product.seller_id != current_user.id:
        raise create_error("ACCESS_DENIED")
    
    product.status = ProductStatusEnum.ARCHIVED
    product.updated_at = datetime.utcnow()
    db.commit()
    
    return None
