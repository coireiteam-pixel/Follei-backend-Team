from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.ids import short_id
from app.core.security import hash_password
from app.models.tenancy import Tenant, User
from app.schemas.tenant import TenantCreate, TenantRead

router = APIRouter(prefix="/tenants", tags=["tenants"])


def _unique_id(db: Session, model: type[Tenant] | type[User]) -> str:
    for _ in range(100):
        item_id = short_id()
        if db.get(model, item_id) is None:
            return item_id
    raise HTTPException(status_code=500, detail="Could not generate unique id")


@router.post("/", response_model=TenantRead)
def create_tenant(payload: TenantCreate, db: Session = Depends(get_db)):
    if payload.domain:
        existing = db.query(Tenant).filter(
            Tenant.domain == payload.domain
        ).first()

        if existing:
            raise HTTPException(
                status_code=409,
                detail="Tenant domain already exists"
            ) 

    existing_user = db.query(User).filter(User.email == payload.admin_email).first()
    if existing_user:
        raise HTTPException(status_code=409, detail="User email already exists")

    tenant = Tenant(
        id=_unique_id(db, Tenant),
        name=payload.name,
        domain=payload.domain,
        phone=payload.phone,
    )

    db.add(tenant)
    db.flush()

    admin_user = User(
        id=_unique_id(db, User),
        tenant_id=tenant.id,
        email=payload.admin_email,
        hashed_password=hash_password(payload.admin_password),
        first_name=payload.admin_first_name,
        last_name=payload.admin_last_name,
        role="admin",
    )
    db.add(admin_user)
    db.commit()
    db.refresh(tenant)

    return tenant


@router.get("/{tenant_id}", response_model=TenantRead)
def get_tenant(
    tenant_id: str,
    db: Session = Depends(get_db)
):
    tenant = db.get(Tenant, tenant_id)

    if not tenant:
        raise HTTPException(
            status_code=404,
            detail="Tenant not found"
        )

    return tenant


@router.get("/", response_model=list[TenantRead])
def list_tenants(db: Session = Depends(get_db)):
    return db.query(Tenant).all()


@router.delete("/{tenant_id}")
def delete_tenant(
    tenant_id: str,
    db: Session = Depends(get_db)
):
    tenant = db.get(Tenant, tenant_id)

    if not tenant:
        raise HTTPException(
            status_code=404,
            detail="Tenant not found"
        )

    db.delete(tenant)
    db.commit()

    return {
    }
