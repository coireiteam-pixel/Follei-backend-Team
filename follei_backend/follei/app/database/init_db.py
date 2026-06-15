from pathlib import Path

from app.database.base import Base
from app.database.session import engine

# Import models so SQLAlchemy registers them before create_all.
from app.models.agents.agent import (  # noqa: F401
    Agent,
    AgentAction,
    AgentAnalytics,
    AgentConfidenceScore,
    AgentError,
    AgentFeedback,
    AgentLearningEvent,
    AgentMemory,
    AgentPlan,
    AgentPromptVersion,
    AgentSession,
    AgentTask,
    AgentToolCall,
    AgentVersion,
)
from app.models.conversations.conversation import (  # noqa: F401
    Conversation,
    ConversationAction,
    ConversationAnalytics,
    ConversationBuyingSignal,
    ConversationCitation,
    ConversationEmotion,
    ConversationEntity,
    ConversationFeedback,
    ConversationIntent,
    ConversationMetric,
    ConversationObjection,
    ConversationParticipant,
    ConversationSentiment,
    ConversationSummary,
    ConversationTranscript,
    Message,
    MessageAttachment,
    MessageDeliveryStatus,
    MessageReaction,
    ResponseMetric,
)
from app.models.customers.customer import Customer  # noqa: F401
from app.models.integrations.integration import Integration, IntegrationConnection  # noqa: F401
from app.models.knowledge.document import (  # noqa: F401
    ChunkCitation,
    ChunkEmbedding,
    Document,
    DocumentChunk,
    DocumentPage,
    DocumentVersion,
    KnowledgeFeedback,
    KnowledgeSource,
    KnowledgeTag,
)
from app.models.leads.lead import Lead  # noqa: F401
from app.models.tenancy import Tenant, User  # noqa: F401


def init_db() -> None:
    _apply_complete_domain_schema()
    Base.metadata.create_all(bind=engine)


def _apply_complete_domain_schema() -> None:
    if engine.url.get_backend_name() != "postgresql":
        return

    schema_path = Path(__file__).resolve().parents[2] / "db" / "init" / "002_complete_domain_schema.sql"
    if not schema_path.exists():
        return

    raw_connection = engine.raw_connection()
    try:
        with raw_connection.cursor() as cursor:
            cursor.execute(schema_path.read_text(encoding="utf-8"))
        raw_connection.commit()
    except Exception:
        raw_connection.rollback()
        raise
    finally:
        raw_connection.close()
