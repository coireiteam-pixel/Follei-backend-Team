"""Business rules for tenant integration management."""

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.ids import short_id
from app.models.integrations.integration import Integration
from app.models.tenancy import Tenant
from app.repositories.integration_repository import IntegrationRepository
from app.schemas.integration import CreateIntegrationRequest


class IntegrationService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repository = IntegrationRepository(db)

    def create_integration(self, payload: CreateIntegrationRequest) -> Integration:
        tenant = self.repository.get_tenant(payload.tenant_id)
        if tenant is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")
        if tenant.status.lower() != "active":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Tenant is inactive")
        if self.repository.get_by_name(payload.tenant_id, payload.name) is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Integration name already exists for this tenant",
            )
        integration = Integration(
            id=str(short_id()),
            tenant_id=payload.tenant_id,
            provider=payload.provider,
            name=payload.name,
            description=payload.description,
            status=payload.status,
            phone_number=payload.phone_number,
            config={},
            ai_config={},
            category="messaging",
            auth_type="api_key",
            scopes=[],
            webhook_support="true",
            actions=["receive_sms", "send_sms", "auto_reply"],
            metadata_={},
        )
        try:
            self.repository.create_integration(integration)
            self.db.commit()
            self.db.refresh(integration)
        except IntegrityError as exc:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Integration name already exists for this tenant",
            ) from exc
        return integration
