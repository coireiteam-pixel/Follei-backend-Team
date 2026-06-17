# Work Done So Far

This document summarizes the backend work completed in this project so far.

## Backend App Startup

- Updated the FastAPI app in `follei_backend/follei/app/main.py`.
- Added a modern FastAPI lifespan startup function.
- Startup now calls `init_db()` so SQLAlchemy creates registered tables.
- Added the shared API prefix:

```text
/api
```

- Mounted the routers under that prefix:
  - `/api/auth`
  - `/api/agents`
  - `/api/tenants`
  - `/api/users`
  - `/api/conversations`
  - `/api/messages`

- Kept system endpoints outside the API prefix:
  - `/`
  - `/health`
  - `/docs`

## Database Setup

- Local development uses PostgreSQL.
- Current local PostgreSQL database URL:

```text
postgresql://postgres:Vignesh%40123@127.0.0.1:5432/follei_db
```

- Docker Compose is configured for PostgreSQL.
- Docker PostgreSQL settings currently use:

```text
POSTGRES_USER=postgres
POSTGRES_PASSWORD=Vignesh@123
POSTGRES_DB=follei_db
host port: 5432
container port: 5432
```

- The Docker backend service uses:

```text
postgresql://postgres:Vignesh%40123@postgres:5432/follei_db
```

- Docker Compose also mounts database init SQL files:

```text
./db/init:/docker-entrypoint-initdb.d:ro
```

## Dependency And Environment Fixes

- Fixed local Python package tooling so `python -m pip` resolves correctly.
- Upgraded user-site pip tooling to pip `26.1.2`.
- Added the missing `anthropic` dependency to `requirements.txt`.
- Verified backend dependencies enough to run tests and import the app.

## Authentication Work

- JWT authentication is implemented through:
  - `POST /api/auth/register`
  - `POST /api/auth/login`
  - `GET /api/auth/me`

- Fixed authenticated user lookup by converting the JWT `sub` string back into a UUID before querying SQLAlchemy.
- Swagger Authorize works through FastAPI's bearer-token support.

## Agent API Fixes

- Fixed the agent list endpoint so it receives the authenticated `current_user`.
- Agent listing is tenant-scoped through `current_user.tenant_id`.
- Agent creation uses the authenticated user's tenant instead of trusting a tenant id from the request body.

## SQLAlchemy Compatibility Work

- Updated models to use SQLAlchemy's generic `Uuid` type where needed.
- Added SQLite-compatible JSON variants for fields that previously used PostgreSQL arrays.
- This allows the same ORM model layer to work in local SQLite development and PostgreSQL-backed Docker development.
- Updated SQLAlchemy base usage to the modern `sqlalchemy.orm.declarative_base` pattern in the shared base module.
- `metadata` database columns are mapped as `metadata_` in ORM models where needed because `metadata` is reserved by SQLAlchemy declarative models.

## Core Models And Relationships

The following base domain models exist or were updated with relationships:

- `Tenant`
- `User`
- `Agent`
- `Conversation`
- `Message`
- `Customer`
- `Lead`
- `Document`
- `Integration`
- `IntegrationConnection`

Important relationships now supported:

- `Tenant.users`
- `Tenant.agents`
- `Tenant.conversations`
- `Tenant.messages`
- `Tenant.customers`
- `Tenant.documents`
- `Tenant.integration_connections`
- `Tenant.leads`
- `User.tenant`
- `Agent.tenant`
- `Agent.conversations`
- `Conversation.tenant`
- `Conversation.agent`
- `Conversation.customer`
- `Conversation.lead`
- `Conversation.messages`
- `Message.conversation`
- `Message.tenant`
- `Customer.tenant`
- `Customer.lead`
- `Customer.conversations`
- `Lead.customers`
- `Lead.conversations`
- `Integration.connections`
- `IntegrationConnection.integration`
- `IntegrationConnection.tenant`

## Agent Lifecycle Models Added

The following agent-related models were created from the schema:

- `AgentSession`
- `AgentTask`
- `AgentAction`
- `AgentAnalytics`
- `AgentConfidenceScore`
- `AgentError`
- `AgentFeedback`
- `AgentLearningEvent`
- `AgentMemory`
- `AgentPlan`
- `AgentPromptVersion`
- `AgentToolCall`
- `AgentVersion`

Important relationships include:

- `Agent.sessions`
- `Agent.tasks`
- `Agent.actions`
- `Agent.analytics`
- `Agent.confidence_scores`
- `Agent.errors`
- `Agent.feedback`
- `Agent.learning_events`
- `Agent.memories`
- `Agent.plans`
- `Agent.prompt_versions`
- `Agent.tool_calls`
- `Agent.versions`
- `AgentSession.agent`
- `AgentSession.conversation`
- `AgentTask.agent`
- `AgentTask.assignee`
- `AgentTask.actions`
- `AgentTask.plans`
- `AgentAction.agent`
- `AgentAction.session`
- `AgentAction.task`
- `AgentMemory.agent`
- `AgentMemory.customer`
- `AgentFeedback.agent`
- `AgentFeedback.message`
- `AgentFeedback.creator`
- `AgentPromptVersion.creator`
- `AgentVersion.creator`

## Knowledge And Document Models Added

The following knowledge/document models were created:

- `KnowledgeSource`
- `Document`
- `DocumentChunk`
- `DocumentPage`
- `DocumentVersion`
- `ChunkCitation`
- `ChunkEmbedding`
- `KnowledgeFeedback`
- `KnowledgeTag`

Important relationships include:

- `KnowledgeSource.documents`
- `Document.source`
- `Document.tenant`
- `Document.chunks`
- `Document.pages`
- `Document.versions`
- `Document.conversation_citations`
- `DocumentChunk.document`
- `DocumentChunk.citations`
- `DocumentChunk.embeddings`
- `DocumentChunk.conversation_citations`
- `ChunkCitation.chunk`
- `ChunkCitation.message`
- `ChunkEmbedding.chunk`
- `KnowledgeFeedback.user`
- `KnowledgeFeedback.tenant`
- `KnowledgeTag.tenant`

## Conversation And Message Models Added

The following conversation/message supporting models were created:

- `ConversationAction`
- `ConversationAnalytics`
- `ConversationBuyingSignal`
- `ConversationCitation`
- `ConversationEmotion`
- `ConversationEntity`
- `ConversationFeedback`
- `ConversationIntent`
- `ConversationMetric`
- `ConversationObjection`
- `ConversationParticipant`
- `ConversationSentiment`
- `ConversationSummary`
- `ConversationTranscript`
- `MessageAttachment`
- `MessageDeliveryStatus`
- `MessageReaction`
- `ResponseMetric`

Important relationships include:

- `Conversation.actions`
- `Conversation.analytics`
- `Conversation.buying_signals`
- `Conversation.emotions`
- `Conversation.entities`
- `Conversation.feedback`
- `Conversation.intents`
- `Conversation.metrics`
- `Conversation.objections`
- `Conversation.participants`
- `Conversation.sentiments`
- `Conversation.summaries`
- `Conversation.transcripts`
- `Conversation.agent_sessions`
- `Message.attachments`
- `Message.delivery_statuses`
- `Message.reactions`
- `Message.conversation_citations`
- `Message.chunk_citations`
- `Message.response_metrics`
- `Message.emotions`
- `Message.feedback`
- `Message.sentiments`
- `ConversationCitation.message`
- `ConversationCitation.document`
- `ConversationCitation.chunk`
- `ConversationSummary.creator`
- `MessageReaction.user`

## Pydantic Schema Updates

- Updated response schemas to use Pydantic v2 style `ConfigDict(from_attributes=True)`.
- This replaced the older class-based `Config` pattern and removed the project-side Pydantic deprecation warnings.

## Model Registration

- New models were registered in `follei_backend/follei/app/models/__init__.py`.
- New models were imported in `follei_backend/follei/app/database/init_db.py`.
- This ensures `Base.metadata.create_all(bind=engine)` can create all registered tables.

## Tests Added

- Added smoke tests under:

```text
follei_backend/follei/tests/test_app.py
```

- Tests cover:
  - `/health`
  - API v1 route mounting
  - old non-prefixed auth route returning `404`

## Verification Commands Used

The following commands were used repeatedly to verify the backend:

```powershell
python -m compileall -q app tests
python -m pytest
```

Additional smoke checks were run for:

- FastAPI app import.
- Uvicorn startup.
- `/health`.
- `POST /api/auth/register`.
- `GET /api/auth/me`.
- `POST /api/agents`.
- `GET /api/agents`.
- Agent lifecycle ORM relationships.
- Knowledge/document ORM relationships.
- Conversation/message/citation ORM relationships.
- In-memory SQLite table creation through `init_db()`.

## Current Run Commands

From the backend folder:

```powershell
cd C:\Users\User\Desktop\Follei15pc\Follei-backend-Team\follei_backend\follei
python -m uvicorn app.main:app --reload
```

Then open:

```text
http://127.0.0.1:8000/docs
```

## Notes And Next Steps

- Local SQLite is good for quick development, but production should use PostgreSQL.
- Docker requires Docker Desktop to be installed and available in PATH.
- The pasted database schema contains many more tables than have been modeled so far.
- The next useful model groups to add are:
  - customer analytics and customer contacts
  - lead scoring and lead activity
  - integrations sync jobs and webhooks
  - billing/subscriptions/payments
  - roles/permissions/user sessions
  - tools and usage tracking
