from pathlib import Path

from sqlalchemy import inspect, text

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
from app.models.integrations.sms import SmsContact, SmsConversation, SmsMessage  # noqa: F401
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
    _ensure_identity_columns()


def _ensure_identity_columns() -> None:
    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())
    if "tenants" not in existing_tables or "users" not in existing_tables:
        return

    is_postgres = engine.url.get_backend_name() == "postgresql"
    timestamp_spec = (
        "TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP"
        if is_postgres
        else "DATETIME"
    )
    json_spec = "JSONB" if is_postgres else "JSON"
    column_specs = {
        "tenants": {
            "phone": "VARCHAR",
            "status": "VARCHAR NOT NULL DEFAULT 'active'",
            "updated_at": timestamp_spec,
        },
        "users": {
            "status": "VARCHAR NOT NULL DEFAULT 'active'",
            "updated_at": timestamp_spec,
        },
    }
    if "integrations" in existing_tables:
        column_specs["integrations"] = {
            "provider": "VARCHAR NOT NULL DEFAULT 'legacy'",
            "description": "TEXT",
            "phone_number": "VARCHAR",
            "config": f"{json_spec} NOT NULL DEFAULT '{{}}'",
            "ai_config": f"{json_spec} NOT NULL DEFAULT '{{}}'",
            "updated_at": timestamp_spec,
        }

    with engine.begin() as connection:
        for table_name, specs in column_specs.items():
            existing_columns = {column["name"] for column in inspector.get_columns(table_name)}
            for column_name, column_spec in specs.items():
                if column_name not in existing_columns:
                    connection.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_spec}"))
        if "integrations" in existing_tables:
            connection.execute(
                text(
                    "CREATE UNIQUE INDEX IF NOT EXISTS uq_integrations_tenant_name_ci "
                    "ON integrations (tenant_id, lower(name)) WHERE tenant_id IS NOT NULL"
                )
            )
            connection.execute(
                text(
                    "CREATE UNIQUE INDEX IF NOT EXISTS uq_integrations_phone_number "
                    "ON integrations (phone_number) WHERE phone_number IS NOT NULL"
                )
            )


def _apply_complete_domain_schema() -> None:
    if engine.url.get_backend_name() != "postgresql":
        return

    schema_dir = Path(__file__).resolve().parents[2] / "db" / "init"
    schema_paths = [
        schema_dir / "001_schema.sql",
        schema_dir / "002_complete_domain_schema.sql",
    ]
    if not all(schema_path.exists() for schema_path in schema_paths):
        return

    raw_connection = engine.raw_connection()
    try:
        with raw_connection.cursor() as cursor:
            for schema_path in schema_paths:
                cursor.execute(schema_path.read_text(encoding="utf-8"))
        raw_connection.commit()
    except Exception:
        raw_connection.rollback()
        raise
    finally:
        raw_connection.close()
