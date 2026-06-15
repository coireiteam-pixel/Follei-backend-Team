import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Any

from app import schema
from app.database.session import get_db
from app.models.agents.agent import Agent
from app.models.tenancy import Tenant

router = APIRouter(
    prefix="/api/v1/agents",
    tags=["AI Agents"]
)

@router.post("", response_model=schema.Agent, status_code=status.HTTP_201_CREATED)
def create_agent(agent_in: schema.AgentCreate, db: Session = Depends(get_db)) -> Any:
    """
    Create a new AI worker (e.g., "SDR Agent").
    """
    tenant_id = agent_in.tenant_id
    if tenant_id is None:
        tenant = db.query(Tenant).first()
        if tenant is None:
            tenant = Tenant(name="Default Tenant", domain=f"default-{uuid.uuid4().hex[:8]}.local")
            db.add(tenant)
            db.flush()
        tenant_id = tenant.id
    elif db.get(Tenant, tenant_id) is None:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    new_agent = Agent(
        tenant_id=tenant_id,
        name=agent_in.name,
        role=agent_in.role,
        system_prompt=agent_in.system_prompt,
        tools=agent_in.tools
    )
    db.add(new_agent)
    db.commit()
    db.refresh(new_agent)
    return new_agent

@router.get("", response_model=List[schema.Agent])
def list_agents(db: Session = Depends(get_db)) -> Any:
    """
    List active agents.
    """
    # Note: This should also be filtered by the authenticated user's tenant_id.
    agents = db.query(Agent).all()
    return agents
