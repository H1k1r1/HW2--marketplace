from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.database import get_db
from src.models import User, UserRoleEnum
from src.schemas import RegisterRequest, LoginRequest, TokenResponse, RefreshRequest
from src.core.security import (
    get_password_hash, verify_password,
    create_access_token, create_refresh_token
)
from src.core.exceptions import create_error

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", status_code=201)
def register(
    request: RegisterRequest,
    db: Session = Depends(get_db)
):
    existing = db.query(User).filter(User.email == request.email).first()
    if existing:
        raise create_error("VALIDATION_ERROR", details={"email": "already registered"})
    
    new_user = User(
        email=request.email,
        password_hash=get_password_hash(request.password),
        role=UserRoleEnum[request.role.value]
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return {
        "id": str(new_user.id),
        "email": new_user.email,
        "role": new_user.role.value,
        "created_at": new_user.created_at.isoformat()
    }


@router.post("/login", response_model=TokenResponse)
def login(
    request: LoginRequest,
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.email == request.email).first()
    if not user or not verify_password(request.password, user.password_hash):
        raise create_error("TOKEN_INVALID", message="Invalid credentials")
    
    access_token = create_access_token(
        data={"sub": str(user.id), "role": user.role.value}
    )
    refresh_token = create_refresh_token(
        data={"sub": str(user.id), "role": user.role.value}
    )
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


@router.post("/refresh", response_model=TokenResponse)
def refresh_token_endpoint(
    request: RefreshRequest,
    db: Session = Depends(get_db)
):
    try:
        from jose import jwt, JWTError
        from src.config import settings
        
        payload = jwt.decode(
            request.refresh_token, 
            settings.JWT_SECRET_KEY, 
            algorithms=[settings.JWT_ALGORITHM]
        )
        user_id = payload.get("sub")
        
        if not user_id:
            raise create_error("REFRESH_TOKEN_INVALID")
        
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise create_error("REFRESH_TOKEN_INVALID")
        
        new_access = create_access_token(
            data={"sub": str(user.id), "role": user.role.value}
        )
        
        return {
            "access_token": new_access,
            "refresh_token": request.refresh_token,
            "token_type": "bearer"
        }
        
    except JWTError:
        raise create_error("REFRESH_TOKEN_INVALID")
