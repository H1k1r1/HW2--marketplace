from sqlalchemy.orm import Session

from src.models import User, UserRoleEnum
from src.core.security import (
    get_password_hash, verify_password,
    create_access_token, create_refresh_token
)
from src.core.exceptions import create_error


class AuthService:
    def __init__(self, db):
        self.db = db

    def register(self, email, password, role):
        existing = self.db.query(User).filter(User.email == email).first()
        if existing:
            raise create_error("VALIDATION_ERROR", details={"email": "already registered"})
        
        new_user = User(
            email=email,
            password_hash=get_password_hash(password),
            role=UserRoleEnum[role]
        )
        
        self.db.add(new_user)
        self.db.commit()
        self.db.refresh(new_user)
        
        return new_user

    def authenticate(self, email, password):
        user = self.db.query(User).filter(User.email == email).first()
        if not user or not verify_password(password, user.password_hash):
            raise create_error("TOKEN_INVALID", message="Invalid credentials")
        return user

    def create_tokens(self, user):
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
