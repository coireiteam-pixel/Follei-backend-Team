from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Any

from app import schema
from app.database.session import get_db
from app.models.agents.agent import Agent
from app.models.tenancy import User
from app.routers.auth import get_current_user
from app.services.mcp.email import build_email_context
from app.services.mistral import MistralAPIError, MistralConfigurationError, chat_completion

router = APIRouter(
    prefix="/agents",
    tags=["AI Agents"]
)

EMAIL_TOOL_NAMES = {"email", "gmail", "outlook", "gmail_read", "read_email"}

@router.post("", response_model=schema.Agent, status_code=status.HTTP_201_CREATED)
def create_agent(
    agent_in: schema.AgentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Create a new AI worker (e.g., "SDR Agent").
    """
    new_agent = Agent(
        tenant_id=current_user.tenant_id,
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
def list_agents(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    List active agents.
    """
    agents = db.query(Agent).filter(Agent.tenant_id == current_user.tenant_id).all()
    return agents

@router.post("/{agent_id}/chat", response_model=schema.AIChatResponse)
def chat_with_agent(
    agent_id: str,
    chat_request: schema.AIChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Chat with a specific AI agent using the Mistral API.
    """
    agent = db.query(Agent).filter(
        Agent.id == agent_id,
        Agent.tenant_id == current_user.tenant_id
    ).first()

    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found or unauthorized")

    try:
        agent_tools = set(agent.tools or [])
        email_context = (
            build_email_context(chat_request.message)
            if agent_tools.intersection(EMAIL_TOOL_NAMES)
            else None
        )
        response = chat_completion(
            system_prompt=agent.system_prompt,
            user_message=chat_request.message,
            context=email_context,
        )
        return {"response": response}
    except MistralConfigurationError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except MistralAPIError as exc:
        raise HTTPException(status_code=502, detail=str(exc))
