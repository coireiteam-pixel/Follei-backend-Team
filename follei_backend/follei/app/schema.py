from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime
from uuid import UUID

# --- TENANCY & IDENTITY ---

class TenantBase(BaseModel):
    name: str
    domain: Optional[str] = None

class TenantCreate(TenantBase):
    pass

class Tenant(TenantBase):
    id: UUID
    created_at: datetime
    
    class Config:
        from_attributes = True

class UserBase(BaseModel):
    email: EmailStr
    first_name: str
    last_name: str
    role: str

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: UUID
    tenant_id: UUID
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

class RegisterRequest(TenantCreate):
    admin_email: EmailStr
    admin_password: str
    admin_first_name: str = "Admin"
    admin_last_name: str = "User"

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

# --- KNOWLEDGE ---

class DocumentBase(BaseModel):
    title: str
    source_type: str
    tags: List[str] = []

class DocumentCreate(DocumentBase):
    pass

class Document(DocumentBase):
    id: UUID
    tenant_id: UUID
    status: str
    created_at: datetime

    class Config:
        from_attributes = True

# --- AGENTS ---

class AgentBase(BaseModel):
    name: str
    role: str
    system_prompt: str

class AgentCreate(AgentBase):
    tenant_id: Optional[UUID] = None
    tools: List[str] = []

class Agent(AgentBase):
    id: UUID
    tenant_id: UUID
    tools: List[str] = []
    created_at: datetime

    class Config:
        from_attributes = True
