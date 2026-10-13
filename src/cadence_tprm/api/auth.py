"""Authentication and current user endpoints."""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from src.cadence_tprm.database import get_db
from src.cadence_tprm.models.identity import User
from src.cadence_tprm.services.auth_service import AuthService, create_access_token, get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])

class LoginRequest(BaseModel):
    email: EmailStr
    password: Optional[str] = None

@router.post("/login")
def login(req: LoginRequest, db: Session = Depends(get_db)):
    profile = AuthService.get_user_profile(db, req.email.lower().strip())
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found in TPRM user directory."
        )

    token = create_access_token({"sub": profile["email"]})
    return {
        "user": profile,
        "access_token": token,
        "token_type": "bearer"
    }

@router.get("/me")
def get_current_session(user: dict = Depends(get_current_user)):
    return {"user": user}

@router.get("/users")
def list_users(db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    """Lists all active directory users and their assigned TPRM groups."""
    users = db.query(User).filter_by(is_active=True).all()
    output = []
    for u in users:
        p = AuthService.get_user_profile(db, u.email)
        if p:
            output.append(p)
    return {"users": output}
