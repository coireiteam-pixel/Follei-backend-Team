from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.ids import short_id
from app.core.security import create_access_token, decode_access_token, hash_password, verify_password
from app.database.session import get_db
from app.models.tenancy import Tenant, User
from app.schemas.auth import (
    AuthTenantResponse,
    AuthUserResponse,
    CurrentUserResponse,
    LoginRequest,
    RegisterRequest,
    TokenResponse,
)

bearer_scheme = HTTPBearer()

router = APIRouter(prefix="/auth", tags=["Identity & Auth"])


def _unique_id(db: Session, model: type[Tenant] | type[User]) -> str:
    for _ in range(100):
        item_id = short_id()
        if db.get(model, item_id) is None:
            return item_id
    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not generate unique id")


def _user_status(user: User) -> str:
    return getattr(user, "status", None) or ("active" if user.is_active else "inactive")


def _tenant_response(tenant: Tenant) -> AuthTenantResponse:
    return AuthTenantResponse(
        id=tenant.id,
        name=tenant.name,
        domain=tenant.domain,
        status=getattr(tenant, "status", None) or "active",
    )


def _user_response(user: User) -> AuthUserResponse:
    return AuthUserResponse(
        id=user.id,
        email=user.email,
        role=user.role,
        tenant_id=user.tenant_id,
        first_name=user.first_name,
        last_name=user.last_name,
        status=_user_status(user),
    )


def _token_response(user: User, tenant: Tenant) -> TokenResponse:
    access_token = create_access_token({"sub": user.id, "tenant_id": user.tenant_id, "role": user.role})
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=_user_response(user),
        tenant=_tenant_response(tenant),
    )


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    try:
        payload = decode_access_token(credentials.credentials)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from exc

    user = db.get(User, str(payload["sub"]))
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    if user.is_active is False or _user_status(user) != "active":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User is inactive")
    return user


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register_tenant(payload: RegisterRequest, db: Session = Depends(get_db)) -> TokenResponse:
    existing_tenant = db.query(Tenant).filter(Tenant.domain == payload.domain).first()
    if existing_tenant is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Tenant domain already exists")

    existing_user = db.query(User).filter(User.email == payload.admin_email).first()
    if existing_user is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User email already exists")

    tenant = Tenant(id=_unique_id(db, Tenant), name=payload.tenant_name, domain=payload.domain, phone=payload.phone, status="active")
    db.add(tenant)
    db.flush()

    user = User(
        id=_unique_id(db, User),
        tenant_id=tenant.id,
        email=str(payload.admin_email),
        hashed_password=hash_password(payload.admin_password),
        first_name=payload.admin_first_name,
        last_name=payload.admin_last_name,
        role="admin",
        status="active",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(tenant)
    db.refresh(user)
    return _token_response(user, tenant)


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    user = db.query(User).filter(User.email == payload.email).first()
    if user is None or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    if user.is_active is False or _user_status(user) != "active":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User is inactive")

    tenant = db.get(Tenant, user.tenant_id)
    if tenant is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    return _token_response(user, tenant)


@router.get("/me", response_model=CurrentUserResponse)
def read_current_user(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CurrentUserResponse:
    tenant = db.get(Tenant, current_user.tenant_id)
    if tenant is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    base_user = _user_response(current_user).model_dump()
    return CurrentUserResponse(
        **base_user,
        tenant=_tenant_response(tenant),
        created_at=current_user.created_at,
        updated_at=getattr(current_user, "updated_at", None),
    )
