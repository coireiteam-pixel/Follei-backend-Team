from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Any

from app import schema
from app.database.session import get_db
# from app.models.identity.tenancy import Tenant, User

router = APIRouter(
    prefix="/api/v1/auth",
    tags=["Identity & Auth"]
)

@router.post("/register", response_model=schema.Tenant, status_code=status.HTTP_201_CREATED)
def register_tenant(tenant_in: schema.TenantCreate, db: Session = Depends(get_db)) -> Any:
    """
    Create a new tenant and an initial admin user.
    """
    # TODO: Add logic to create the Tenant and User models in the database
    # tenant = Tenant(name=tenant_in.name, domain=tenant_in.domain)
    # db.add(tenant)
    # db.commit()
    # db.refresh(tenant)
    # return tenant
    
    raise HTTPException(status_code=501, detail="Not implemented")

@router.post("/login")
def login(db: Session = Depends(get_db)) -> Any:
    """
    Authenticate a user and return a JWT token.
    """
    # TODO: Verify credentials against db and return JWT
    return {"access_token": "placeholder_token", "token_type": "bearer"}

@router.get("/me", response_model=schema.User)
def get_current_user(db: Session = Depends(get_db)) -> Any:
    """
    Get the current authenticated user's profile.
    """
    # TODO: Create a `get_current_active_user` dependency that extracts the JWT payload
    # and retrieves the User from the database using db.query(User).filter(...)
    
    raise HTTPException(status_code=501, detail="Not implemented")
