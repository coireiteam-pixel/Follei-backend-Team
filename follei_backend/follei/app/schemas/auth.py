from datetime import datetime

from pydantic import AliasChoices, BaseModel, ConfigDict, EmailStr, Field


class RegisterRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    tenant_name: str = Field(validation_alias=AliasChoices("tenant_name", "name"), examples=["Acme Corp"])
    domain: str = Field(examples=["acme"])
    phone: str | None = Field(default=None, examples=["+15551234567"])
    admin_email: EmailStr = Field(examples=["admin@acme.com"])
    admin_password: str = Field(examples=["Admin@123"])
    admin_first_name: str = Field(default="Admin", examples=["Admin"])
    admin_last_name: str = Field(default="User", examples=["User"])


class LoginRequest(BaseModel):
    email: EmailStr = Field(examples=["admin@acme.com"])
    password: str = Field(examples=["Admin@123"])


class AuthUserResponse(BaseModel):
    id: str
    email: EmailStr
    role: str
    tenant_id: str
    first_name: str | None = None
    last_name: str | None = None
    status: str = "active"


class AuthTenantResponse(BaseModel):
    id: str
    name: str
    domain: str | None = None
    status: str = "active"


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: AuthUserResponse
    tenant: AuthTenantResponse


class CurrentUserResponse(AuthUserResponse):
    tenant: AuthTenantResponse
    created_at: datetime | None = None
    updated_at: datetime | None = None
