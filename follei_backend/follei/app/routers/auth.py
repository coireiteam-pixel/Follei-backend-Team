from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session
from typing import Any

from app import schema
from app.database.session import get_db
from app.models.tenancy import Tenant, User

bearer_scheme = HTTPBearer()

router = APIRouter(
    prefix="/api/v1/auth",
    tags=["Identity & Auth"]
)

@router.post("/register", response_model=schema.Tenant, status_code=status.HTTP_201_CREATED)
def register_tenant(tenant_in: schema.TenantCreate, db: Session = Depends(get_db)) -> Any:
    """
    Create a new tenant and an initial admin user.
    """
    existing = db.query(Tenant).filter(Tenant.domain == tenant_in.domain).first()
    if tenant_in.domain and existing:
        raise HTTPException(status_code=409, detail="Tenant domain already exists")

    tenant = Tenant(name=tenant_in.name, domain=tenant_in.domain)
    db.add(tenant)
    db.commit()
    db.refresh(tenant)
    return tenant

@router.post("/login")
def login(db: Session = Depends(get_db)) -> Any:
    """
    Authenticate a user and return a JWT token.
    """
    # TODO: Verify credentials against db and return JWT
    return {"access_token": "placeholder_token", "token_type": "bearer"}

@router.get("/me", response_model=schema.User)
def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> Any:
    """
    Get the current authenticated user's profile.
    """
    # TODO: Create a `get_current_active_user` dependency that extracts the JWT payload
    # and retrieves the User from the database using db.query(User).filter(...)
    # The bearer dependency exposes Swagger's Authorize button while JWT validation
    # is still pending.
    token = credentials.credentials
    if token != "placeholder_token":
        raise HTTPException(status_code=401, detail="Invalid token")

    user = db.query(User).first()
    if not user:
        raise HTTPException(status_code=404, detail="No users found")
    return user
