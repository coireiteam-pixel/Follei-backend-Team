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
    Base.metadata.create_all(bind=engine)
