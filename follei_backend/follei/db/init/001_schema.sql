CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS tenants (
    id VARCHAR(4) PRIMARY KEY DEFAULT lower(substr(md5(random()::text || clock_timestamp()::text), 1, 4)),
    name VARCHAR(255) NOT NULL,
    domain VARCHAR(255) UNIQUE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS users (
    id VARCHAR(4) PRIMARY KEY DEFAULT lower(substr(md5(random()::text || clock_timestamp()::text), 1, 4)),
    tenant_id VARCHAR(4) NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    email VARCHAR(320) NOT NULL UNIQUE,
    hashed_password TEXT NOT NULL,
    first_name VARCHAR(120) NOT NULL,
    last_name VARCHAR(120) NOT NULL,
    role VARCHAR(80) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS tenant_settings (
    id VARCHAR(4) PRIMARY KEY DEFAULT lower(substr(md5(random()::text || clock_timestamp()::text), 1, 4)),
    tenant_id VARCHAR(4) NOT NULL UNIQUE REFERENCES tenants(id) ON DELETE CASCADE,
    settings JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS agents (
    id VARCHAR(4) PRIMARY KEY DEFAULT lower(substr(md5(random()::text || clock_timestamp()::text), 1, 4)),
    tenant_id VARCHAR(4) NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    role VARCHAR(80) NOT NULL,
    system_prompt TEXT NOT NULL,
    tools TEXT[] NOT NULL DEFAULT '{}',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS agent_prompt_versions (
    id VARCHAR(4) PRIMARY KEY DEFAULT lower(substr(md5(random()::text || clock_timestamp()::text), 1, 4)),
    tenant_id VARCHAR(4) NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    agent_id VARCHAR(4) NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
    version INTEGER NOT NULL,
    system_prompt TEXT NOT NULL,
    created_by VARCHAR(4) REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (agent_id, version)
);

CREATE TABLE IF NOT EXISTS leads (
    id VARCHAR(4) PRIMARY KEY DEFAULT lower(substr(md5(random()::text || clock_timestamp()::text), 1, 4)),
    tenant_id VARCHAR(4) NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    email VARCHAR(320) NOT NULL,
    first_name VARCHAR(120),
    last_name VARCHAR(120),
    company VARCHAR(255),
    status VARCHAR(80) NOT NULL DEFAULT 'new',
    revenue_score INTEGER NOT NULL DEFAULT 0,
    source VARCHAR(120),
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (tenant_id, email)
);

CREATE TABLE IF NOT EXISTS customers (
    id VARCHAR(4) PRIMARY KEY DEFAULT lower(substr(md5(random()::text || clock_timestamp()::text), 1, 4)),
    tenant_id VARCHAR(4) NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    lead_id VARCHAR(4) REFERENCES leads(id) ON DELETE SET NULL,
    name VARCHAR(255) NOT NULL,
    health_score INTEGER NOT NULL DEFAULT 100,
    churn_risk VARCHAR(40) NOT NULL DEFAULT 'low',
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS customer_contacts (
    id VARCHAR(4) PRIMARY KEY DEFAULT lower(substr(md5(random()::text || clock_timestamp()::text), 1, 4)),
    tenant_id VARCHAR(4) NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    customer_id VARCHAR(4) NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    email VARCHAR(320),
    first_name VARCHAR(120),
    last_name VARCHAR(120),
    title VARCHAR(160),
    phone VARCHAR(60),
    is_primary BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS documents (
    id VARCHAR(4) PRIMARY KEY DEFAULT lower(substr(md5(random()::text || clock_timestamp()::text), 1, 4)),
    tenant_id VARCHAR(4) NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    source_id VARCHAR(4),
    title VARCHAR(255) NOT NULL,
    source_type VARCHAR(80) NOT NULL,
    source_uri TEXT,
    mime_type VARCHAR(160),
    path TEXT,
    file_size BIGINT,
    status VARCHAR(80) NOT NULL DEFAULT 'pending',
    tags TEXT[] NOT NULL DEFAULT '{}',
    summary TEXT,
    keywords TEXT[] NOT NULL DEFAULT '{}',
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    indexed_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS document_chunks (
    id VARCHAR(4) PRIMARY KEY DEFAULT lower(substr(md5(random()::text || clock_timestamp()::text), 1, 4)),
    tenant_id VARCHAR(4) NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    document_id VARCHAR(4) NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    token_count INTEGER,
    weaviate_object_id VARCHAR(4),
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (document_id, chunk_index)
);

CREATE TABLE IF NOT EXISTS chunk_embeddings (
    id VARCHAR(4) PRIMARY KEY DEFAULT lower(substr(md5(random()::text || clock_timestamp()::text), 1, 4)),
    tenant_id VARCHAR(4) NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    chunk_id VARCHAR(4) NOT NULL REFERENCES document_chunks(id) ON DELETE CASCADE,
    embedding_model VARCHAR(160) NOT NULL,
    vector_id TEXT NOT NULL,
    dimensions INTEGER,
    distance_metric VARCHAR(80),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (chunk_id, embedding_model)
);

CREATE TABLE IF NOT EXISTS entities (
    id VARCHAR(4) PRIMARY KEY DEFAULT lower(substr(md5(random()::text || clock_timestamp()::text), 1, 4)),
    tenant_id VARCHAR(4) NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    entity_type VARCHAR(120) NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    confidence NUMERIC(5, 4),
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS entity_aliases (
    id VARCHAR(4) PRIMARY KEY DEFAULT lower(substr(md5(random()::text || clock_timestamp()::text), 1, 4)),
    tenant_id VARCHAR(4) NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    entity_id VARCHAR(4) NOT NULL REFERENCES entities(id) ON DELETE CASCADE,
    alias VARCHAR(255) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (entity_id, alias)
);

CREATE TABLE IF NOT EXISTS entity_attributes (
    id VARCHAR(4) PRIMARY KEY DEFAULT lower(substr(md5(random()::text || clock_timestamp()::text), 1, 4)),
    tenant_id VARCHAR(4) NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    entity_id VARCHAR(4) NOT NULL REFERENCES entities(id) ON DELETE CASCADE,
    key VARCHAR(160) NOT NULL,
    value JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (entity_id, key)
);

CREATE TABLE IF NOT EXISTS entity_relations (
    id VARCHAR(4) PRIMARY KEY DEFAULT lower(substr(md5(random()::text || clock_timestamp()::text), 1, 4)),
    tenant_id VARCHAR(4) NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    source_entity_id VARCHAR(4) NOT NULL REFERENCES entities(id) ON DELETE CASCADE,
    target_entity_id VARCHAR(4) NOT NULL REFERENCES entities(id) ON DELETE CASCADE,
    relation_type VARCHAR(160) NOT NULL,
    confidence NUMERIC(5, 4),
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS conversations (
    id VARCHAR(4) PRIMARY KEY DEFAULT lower(substr(md5(random()::text || clock_timestamp()::text), 1, 4)),
    tenant_id VARCHAR(4) NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    agent_id VARCHAR(4) REFERENCES agents(id) ON DELETE SET NULL,
    lead_id VARCHAR(4) REFERENCES leads(id) ON DELETE SET NULL,
    customer_id VARCHAR(4) REFERENCES customers(id) ON DELETE SET NULL,
    title VARCHAR(255),
    channel VARCHAR(80),
    status VARCHAR(80) NOT NULL DEFAULT 'open',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS conversation_messages (
    id VARCHAR(4) PRIMARY KEY DEFAULT lower(substr(md5(random()::text || clock_timestamp()::text), 1, 4)),
    tenant_id VARCHAR(4) NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    conversation_id VARCHAR(4) NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    role VARCHAR(40) NOT NULL,
    content TEXT NOT NULL,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS conversation_citations (
    id VARCHAR(4) PRIMARY KEY DEFAULT lower(substr(md5(random()::text || clock_timestamp()::text), 1, 4)),
    tenant_id VARCHAR(4) NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    message_id VARCHAR(4) NOT NULL REFERENCES conversation_messages(id) ON DELETE CASCADE,
    document_id VARCHAR(4) REFERENCES documents(id) ON DELETE SET NULL,
    chunk_id VARCHAR(4) REFERENCES document_chunks(id) ON DELETE SET NULL,
    quote TEXT,
    confidence NUMERIC(5, 4),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS integrations (
    id VARCHAR(4) PRIMARY KEY DEFAULT lower(substr(md5(random()::text || clock_timestamp()::text), 1, 4)),
    name VARCHAR(160) NOT NULL UNIQUE,
    description TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS integration_connections (
    id VARCHAR(4) PRIMARY KEY DEFAULT lower(substr(md5(random()::text || clock_timestamp()::text), 1, 4)),
    tenant_id VARCHAR(4) NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    integration_id VARCHAR(4) NOT NULL REFERENCES integrations(id) ON DELETE CASCADE,
    status VARCHAR(80) NOT NULL DEFAULT 'active',
    config JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (tenant_id, integration_id)
);

CREATE TABLE IF NOT EXISTS tool_executions (
    id VARCHAR(4) PRIMARY KEY DEFAULT lower(substr(md5(random()::text || clock_timestamp()::text), 1, 4)),
    tenant_id VARCHAR(4) NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    agent_id VARCHAR(4) REFERENCES agents(id) ON DELETE SET NULL,
    integration_connection_id VARCHAR(4) REFERENCES integration_connections(id) ON DELETE SET NULL,
    tool_name VARCHAR(160) NOT NULL,
    status VARCHAR(80) NOT NULL DEFAULT 'queued',
    request JSONB NOT NULL DEFAULT '{}'::jsonb,
    response JSONB,
    error TEXT,
    started_at TIMESTAMPTZ,
    finished_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS subscriptions (
    id VARCHAR(4) PRIMARY KEY DEFAULT lower(substr(md5(random()::text || clock_timestamp()::text), 1, 4)),
    tenant_id VARCHAR(4) NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    plan_name VARCHAR(120) NOT NULL,
    status VARCHAR(80) NOT NULL DEFAULT 'active',
    current_period_start TIMESTAMPTZ,
    current_period_end TIMESTAMPTZ,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS usage_events (
    id VARCHAR(4) PRIMARY KEY DEFAULT lower(substr(md5(random()::text || clock_timestamp()::text), 1, 4)),
    tenant_id VARCHAR(4) NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    user_id VARCHAR(4) REFERENCES users(id) ON DELETE SET NULL,
    agent_id VARCHAR(4) REFERENCES agents(id) ON DELETE SET NULL,
    event_name VARCHAR(160) NOT NULL,
    quantity INTEGER NOT NULL DEFAULT 1,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS audit_logs (
    id VARCHAR(4) PRIMARY KEY DEFAULT lower(substr(md5(random()::text || clock_timestamp()::text), 1, 4)),
    tenant_id VARCHAR(4) REFERENCES tenants(id) ON DELETE CASCADE,
    user_id VARCHAR(4) REFERENCES users(id) ON DELETE SET NULL,
    action VARCHAR(160) NOT NULL,
    entity_type VARCHAR(120),
    entity_id VARCHAR(4),
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS analytics_daily (
    id VARCHAR(4) PRIMARY KEY DEFAULT lower(substr(md5(random()::text || clock_timestamp()::text), 1, 4)),
    tenant_id VARCHAR(4) NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    metric_date DATE NOT NULL,
    metric_name VARCHAR(160) NOT NULL,
    metric_value NUMERIC(18, 4) NOT NULL DEFAULT 0,
    dimensions JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (tenant_id, metric_date, metric_name, dimensions)
);

CREATE INDEX IF NOT EXISTS idx_users_tenant_id ON users(tenant_id);
CREATE INDEX IF NOT EXISTS idx_agents_tenant_id ON agents(tenant_id);
CREATE INDEX IF NOT EXISTS idx_leads_tenant_status ON leads(tenant_id, status);
CREATE INDEX IF NOT EXISTS idx_customers_tenant_id ON customers(tenant_id);
CREATE INDEX IF NOT EXISTS idx_documents_tenant_status ON documents(tenant_id, status);
CREATE INDEX IF NOT EXISTS idx_document_chunks_document_id ON document_chunks(document_id);
CREATE INDEX IF NOT EXISTS idx_conversations_tenant_created ON conversations(tenant_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_messages_conversation_created ON conversation_messages(conversation_id, created_at);
CREATE INDEX IF NOT EXISTS idx_integration_connections_tenant_id ON integration_connections(tenant_id);
CREATE INDEX IF NOT EXISTS idx_tool_executions_tenant_created ON tool_executions(tenant_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_usage_events_tenant_created ON usage_events(tenant_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_logs_tenant_created ON audit_logs(tenant_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_analytics_daily_tenant_date ON analytics_daily(tenant_id, metric_date DESC);

CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS set_tenants_updated_at ON tenants;
CREATE TRIGGER set_tenants_updated_at
BEFORE UPDATE ON tenants
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

DROP TRIGGER IF EXISTS set_users_updated_at ON users;
CREATE TRIGGER set_users_updated_at
BEFORE UPDATE ON users
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

DROP TRIGGER IF EXISTS set_tenant_settings_updated_at ON tenant_settings;
CREATE TRIGGER set_tenant_settings_updated_at
BEFORE UPDATE ON tenant_settings
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

DROP TRIGGER IF EXISTS set_agents_updated_at ON agents;
CREATE TRIGGER set_agents_updated_at
BEFORE UPDATE ON agents
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

DROP TRIGGER IF EXISTS set_leads_updated_at ON leads;
CREATE TRIGGER set_leads_updated_at
BEFORE UPDATE ON leads
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

DROP TRIGGER IF EXISTS set_customers_updated_at ON customers;
CREATE TRIGGER set_customers_updated_at
BEFORE UPDATE ON customers
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

DROP TRIGGER IF EXISTS set_documents_updated_at ON documents;
CREATE TRIGGER set_documents_updated_at
BEFORE UPDATE ON documents
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

DROP TRIGGER IF EXISTS set_conversations_updated_at ON conversations;
CREATE TRIGGER set_conversations_updated_at
BEFORE UPDATE ON conversations
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

DROP TRIGGER IF EXISTS set_integration_connections_updated_at ON integration_connections;
CREATE TRIGGER set_integration_connections_updated_at
BEFORE UPDATE ON integration_connections
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

DROP TRIGGER IF EXISTS set_subscriptions_updated_at ON subscriptions;
CREATE TRIGGER set_subscriptions_updated_at
BEFORE UPDATE ON subscriptions
FOR EACH ROW EXECUTE FUNCTION set_updated_at();
