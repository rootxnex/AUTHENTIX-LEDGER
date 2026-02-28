"""Auth router — login, register, profile."""
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.auth.jwt import create_access_token, hash_password, verify_password
from app.auth.rbac import get_current_user, require_admin
from app.database import get_db
from app.models import User, UserRole, AuditLog
from app.schemas import LoginRequest, TokenResponse, UserCreate, UserOut

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=TokenResponse)
def login(request: Request, body: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == body.username, User.is_active == True).first()
    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    # Update last login
    user.last_login = datetime.now(timezone.utc)
    db.commit()

    # Audit
    log = AuditLog(user_id=user.id, action="LOGIN", ip_address=request.client.host if request.client else None)
    db.add(log)
    db.commit()

    token = create_access_token({"sub": str(user.id), "role": user.role.value, "username": user.username})
    return TokenResponse(access_token=token, role=user.role.value, username=user.username)


@router.post("/register", response_model=UserOut, status_code=201)
def register(body: UserCreate, db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    """Admin-only: register new users."""
    if db.query(User).filter(User.username == body.username).first():
        raise HTTPException(status_code=400, detail="Username already exists")
    if db.query(User).filter(User.email == body.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        username=body.username,
        email=body.email,
        hashed_password=hash_password(body.password),
        full_name=body.full_name,
        role=body.role,
        unit=body.unit,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.get("/me", response_model=UserOut)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.get("/users", response_model=list[UserOut])
def list_users(db: Session = Depends(get_db), _: User = Depends(require_admin)):
    return db.query(User).all()
