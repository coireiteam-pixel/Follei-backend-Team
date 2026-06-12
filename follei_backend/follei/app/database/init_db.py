from app.database.base import Base
from app.database.session import engine

# Import models so SQLAlchemy registers them before create_all.
from app.models.agents.agent import Agent  # noqa: F401
from app.models.conversations.conversation import Conversation, Message  # noqa: F401
from app.models.customers.customer import Customer  # noqa: F401
from app.models.integrations.integration import Integration, IntegrationConnection  # noqa: F401
from app.models.knowledge.document import Document  # noqa: F401
from app.models.leads.lead import Lead  # noqa: F401
from app.models.tenancy import Tenant, User  # noqa: F401


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
