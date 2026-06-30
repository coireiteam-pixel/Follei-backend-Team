"""Database access for tenant-owned integrations."""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.integrations.integration import Integration
from app.models.tenancy import Tenant


class IntegrationRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_tenant(self, tenant_id: str) -> Tenant | None:
        return self.db.get(Tenant, tenant_id)

    def create_integration(self, integration: Integration) -> Integration:
        self.db.add(integration)
        self.db.flush()
        return integration

    def get_by_id(self, integration_id: str) -> Integration | None:
        return self.db.get(Integration, integration_id)

    def get_by_tenant(self, tenant_id: str) -> list[Integration]:
        return list(
            self.db.scalars(
                select(Integration)
                .where(Integration.tenant_id == tenant_id)
                .order_by(Integration.created_at.desc())
            )
        )

    def get_by_provider(self, tenant_id: str, provider: str) -> list[Integration]:
        return list(
            self.db.scalars(
                select(Integration).where(
                    Integration.tenant_id == tenant_id,
                    Integration.provider == provider,
                )
            )
        )

    def get_by_name(self, tenant_id: str, name: str) -> Integration | None:
        return self.db.scalar(
            select(Integration).where(
                Integration.tenant_id == tenant_id,
                func.lower(Integration.name) == name.lower(),
            )
        )

    def get_by_phone(self, phone_number: str) -> Integration | None:
        return self.db.scalar(select(Integration).where(Integration.phone_number == phone_number))
