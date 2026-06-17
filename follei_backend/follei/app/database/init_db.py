from pathlib import Path

from sqlalchemy import text

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
from app.models.domain import (  # noqa: F401
    AnalyticsDaily,
    AnalyticsMonthly,
    Competitor,
    CompetitorFeature,
    Credit,
    CreditTransaction,
    EvaluationResult,
    Event,
    FAQ,
    Invoice,
    ModelUsage,
    Payment,
    Plan,
    Policy,
    PricingModel,
    PricingRule,
    Procedure,
    Product,
    RetrievalLog,
    Service,
    Subscription,
)
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
from app.models.knowledge.entity import (  # noqa: F401
    Entity,
    EntityAlias,
    EntityAttribute,
    EntityRelation,
)
from app.models.leads.lead import Lead  # noqa: F401
from app.models.tenancy import Tenant, User  # noqa: F401


def init_db() -> None:
    _apply_complete_domain_schema()
    Base.metadata.create_all(bind=engine)
    _apply_sqlite_auth_compat_schema()


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


def _apply_sqlite_auth_compat_schema() -> None:
    if engine.url.get_backend_name() != "sqlite":
        return

    required_columns = {
        "tenants": {
            "slug": "VARCHAR(160)",
            "status": "VARCHAR(80) DEFAULT 'active'",
            "is_active": "BOOLEAN DEFAULT 1",
            "updated_at": "DATETIME",
        },
        "users": {
            "full_name": "VARCHAR(255)",
            "status": "VARCHAR(80) DEFAULT 'active'",
            "last_login_at": "DATETIME",
            "updated_at": "DATETIME",
        },
        "agents": {
            "agent_type": "VARCHAR(80)",
            "model": "VARCHAR(160)",
            "is_active": "BOOLEAN DEFAULT 1",
            "updated_at": "DATETIME",
        },
    }

    with engine.begin() as connection:
        for table_name, columns in required_columns.items():
            existing = {
                row[1]
                for row in connection.exec_driver_sql(f"PRAGMA table_info({table_name})")
            }
            for column_name, column_type in columns.items():
                if column_name not in existing:
                    connection.execute(
                        text(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}")
                    )
