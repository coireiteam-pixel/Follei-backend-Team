# Follei API Endpoints

Total paths: 143
Total operations: 230

## AI Agents

- `GET    /agents`
- `POST   /agents`
- `POST   /agents/{agent_id}/chat`

## Analytics & Observability

- `GET    /api/analytics/agents/{agent_id}`
- `GET    /api/analytics/conversations`
- `GET    /api/analytics/customers`
- `GET    /api/analytics/daily`
- `GET    /api/analytics/dashboard`
- `GET    /api/analytics/leads`
- `GET    /api/analytics/model-usage`
- `GET    /api/analytics/monthly`
- `GET    /api/evaluation-results`
- `POST   /api/evaluation-results`
- `POST   /api/events`
- `GET    /api/events`
- `POST   /api/retrieval-logs`
- `GET    /api/retrieval-logs`

## Billing

- `GET    /api/credits`
- `POST   /api/credits/transactions`
- `GET    /api/invoices`
- `POST   /api/invoices`
- `GET    /api/payments`
- `POST   /api/payments`
- `GET    /api/plans`
- `POST   /api/plans`
- `GET    /api/subscriptions`
- `POST   /api/subscriptions`
- `PATCH  /api/subscriptions/{subscription_id}`

## Chunks

- `POST   /api/chunks/{chunk_id}/embeddings`

## Conversations & Messages

- `POST   /api/conversations`
- `GET    /api/conversations`
- `GET    /api/conversations/{conversation_id}`
- `PATCH  /api/conversations/{conversation_id}`
- `DELETE /api/conversations/{conversation_id}`
- `POST   /api/conversations/{conversation_id}/buying-signals`
- `POST   /api/conversations/{conversation_id}/emotions`
- `POST   /api/conversations/{conversation_id}/intents`
- `POST   /api/conversations/{conversation_id}/messages`
- `GET    /api/conversations/{conversation_id}/messages`
- `GET    /api/conversations/{conversation_id}/metrics`
- `POST   /api/conversations/{conversation_id}/objections`
- `POST   /api/conversations/{conversation_id}/participants`
- `GET    /api/conversations/{conversation_id}/participants`
- `DELETE /api/conversations/{conversation_id}/participants/{participant_id}`
- `POST   /api/conversations/{conversation_id}/sentiments`
- `POST   /api/conversations/{conversation_id}/summaries`
- `GET    /api/conversations/{conversation_id}/summaries`
- `GET    /api/messages/{message_id}`
- `PATCH  /api/messages/{message_id}`
- `DELETE /api/messages/{message_id}`
- `POST   /api/messages/{message_id}/attachments`
- `GET    /api/messages/{message_id}/attachments`
- `POST   /api/messages/{message_id}/reactions`

## Customers & Customer Success

- `POST   /api/customers`
- `GET    /api/customers`
- `GET    /api/customers/{customer_id}`
- `PATCH  /api/customers/{customer_id}`
- `DELETE /api/customers/{customer_id}`
- `POST   /api/customers/{customer_id}/contacts`
- `GET    /api/customers/{customer_id}/contacts`
- `POST   /api/customers/{customer_id}/events`
- `GET    /api/customers/{customer_id}/events`
- `POST   /api/customers/{customer_id}/health-scores`
- `GET    /api/customers/{customer_id}/health-scores`
- `POST   /api/customers/{customer_id}/renewals`
- `GET    /api/customers/{customer_id}/renewals`
- `PATCH  /api/renewals/{renewal_id}`

## Database CRUD

- `GET    /database/tables`
- `GET    /database/{table_name}/records`
- `POST   /database/{table_name}/records`
- `GET    /database/{table_name}/records/{record_id}`
- `PATCH  /database/{table_name}/records/{record_id}`
- `DELETE /database/{table_name}/records/{record_id}`
- `GET    /database/{table_name}/schema`

## Documents

- `POST   /api/documents`
- `GET    /api/documents`
- `GET    /api/documents/{document_id}`
- `PATCH  /api/documents/{document_id}`
- `DELETE /api/documents/{document_id}`
- `POST   /api/documents/{document_id}/chunks`
- `GET    /api/documents/{document_id}/chunks`

## Domain 1 - Auth

- `POST   /api/v1/auth/login`
- `POST   /api/v1/auth/logout`
- `GET    /api/v1/auth/me`
- `PATCH  /api/v1/auth/me`
- `POST   /api/v1/auth/password/change`
- `POST   /api/v1/auth/password/reset`
- `POST   /api/v1/auth/password/reset-request`
- `POST   /api/v1/auth/refresh`
- `POST   /api/v1/auth/register`

## Domain 2 - Tenants & Users

- `GET    /api/v1/permissions`
- `GET    /api/v1/roles`
- `POST   /api/v1/roles`
- `GET    /api/v1/tenant-api-keys`
- `POST   /api/v1/tenant-api-keys`
- `DELETE /api/v1/tenant-api-keys/{key_id}`
- `POST   /api/v1/tenants`
- `GET    /api/v1/tenants`
- `GET    /api/v1/tenants/{tenant_id}`
- `PATCH  /api/v1/tenants/{tenant_id}`
- `DELETE /api/v1/tenants/{tenant_id}`
- `GET    /api/v1/tenants/{tenant_id}/settings`
- `PATCH  /api/v1/tenants/{tenant_id}/settings`
- `GET    /api/v1/tenants/{tenant_id}/usage`
- `POST   /api/v1/users`
- `GET    /api/v1/users`
- `GET    /api/v1/users/{user_id}`
- `PATCH  /api/v1/users/{user_id}`
- `DELETE /api/v1/users/{user_id}`
- `POST   /api/v1/users/{user_id}/roles`
- `DELETE /api/v1/users/{user_id}/roles/{role_id}`

## Domain 3 - Agents & AI Workforce

- `PATCH  /api/v1/agent-tasks/{task_id}`
- `POST   /api/v1/agents`
- `GET    /api/v1/agents`
- `GET    /api/v1/agents/{agent_id}`
- `PATCH  /api/v1/agents/{agent_id}`
- `DELETE /api/v1/agents/{agent_id}`
- `POST   /api/v1/agents/{agent_id}/chat`
- `POST   /api/v1/agents/{agent_id}/feedback`
- `GET    /api/v1/agents/{agent_id}/feedback`
- `POST   /api/v1/agents/{agent_id}/memories`
- `GET    /api/v1/agents/{agent_id}/memories`
- `POST   /api/v1/agents/{agent_id}/sessions`
- `GET    /api/v1/agents/{agent_id}/sessions`
- `PATCH  /api/v1/agents/{agent_id}/sessions/{session_id}`
- `POST   /api/v1/agents/{agent_id}/tasks`
- `GET    /api/v1/agents/{agent_id}/tasks`
- `POST   /api/v1/agents/{agent_id}/tool-permissions`
- `GET    /api/v1/agents/{agent_id}/tool-permissions`
- `POST   /api/v1/agents/{agent_id}/versions`
- `GET    /api/v1/agents/{agent_id}/versions`

## Domain 4 - System, Health & Jobs

- `GET    /api/v1/api-request-logs`
- `GET    /api/v1/audit-logs`
- `GET    /api/v1/background-jobs`
- `POST   /api/v1/background-jobs`
- `GET    /api/v1/background-jobs/{job_id}`
- `GET    /api/v1/feature-flags`
- `POST   /api/v1/feature-flags`
- `PATCH  /api/v1/feature-flags/{flag_id}`
- `GET    /api/v1/health`
- `GET    /api/v1/notifications`
- `POST   /api/v1/notifications`
- `PATCH  /api/v1/notifications/{id}/read`

## Entities

- `POST   /api/entities`
- `GET    /api/entities`
- `GET    /api/entities/{entity_id}`
- `PATCH  /api/entities/{entity_id}`
- `DELETE /api/entities/{entity_id}`

## Identity & Auth

- `POST   /auth/login`
- `GET    /auth/me`
- `POST   /auth/register`

## Integrations

- `POST   /api/integration-connections`
- `GET    /api/integration-connections`
- `GET    /api/integration-connections/{connection_id}`
- `PATCH  /api/integration-connections/{connection_id}`
- `DELETE /api/integration-connections/{connection_id}`
- `POST   /api/integration-connections/{connection_id}/sync`
- `GET    /api/integration-connections/{connection_id}/sync-jobs`
- `POST   /api/integration-connections/{connection_id}/webhooks`
- `GET    /api/integration-connections/{connection_id}/webhooks`
- `DELETE /api/integration-connections/{connection_id}/webhooks/{webhook_id}`
- `GET    /api/integrations`
- `GET    /api/integrations/{integration_id}`

## Knowledge & RAG

- `GET    /api/faqs`
- `POST   /api/faqs`
- `PATCH  /api/faqs/{faq_id}`
- `DELETE /api/faqs/{faq_id}`
- `POST   /api/knowledge/search`
- `GET    /api/knowledge/sources`
- `POST   /api/knowledge/sources`
- `GET    /api/knowledge/sources/{source_id}`
- `PATCH  /api/knowledge/sources/{source_id}`
- `DELETE /api/knowledge/sources/{source_id}`
- `GET    /api/policies`
- `POST   /api/policies`
- `GET    /api/procedures`
- `POST   /api/procedures`

## Leads & Revenue

- `POST   /api/leads`
- `GET    /api/leads`
- `GET    /api/leads/{lead_id}`
- `PATCH  /api/leads/{lead_id}`
- `DELETE /api/leads/{lead_id}`
- `POST   /api/leads/{lead_id}/activities`
- `GET    /api/leads/{lead_id}/activities`
- `POST   /api/leads/{lead_id}/qualifications`
- `GET    /api/leads/{lead_id}/qualifications`
- `POST   /api/leads/{lead_id}/scores`
- `GET    /api/leads/{lead_id}/scores`
- `POST   /api/meetings`
- `GET    /api/meetings`
- `PATCH  /api/meetings/{meeting_id}`
- `DELETE /api/meetings/{meeting_id}`
- `POST   /api/opportunities`
- `GET    /api/opportunities`
- `GET    /api/opportunities/{opportunity_id}`
- `PATCH  /api/opportunities/{opportunity_id}`
- `POST   /api/opportunities/{opportunity_id}/proposals`
- `POST   /api/opportunities/{opportunity_id}/quotes`
- `POST   /api/qualification-frameworks`
- `GET    /api/qualification-frameworks`

## Products & Pricing

- `GET    /api/competitors`
- `POST   /api/competitors`
- `POST   /api/competitors/{competitor_id}/features`
- `GET    /api/pricing-models`
- `POST   /api/pricing-models`
- `POST   /api/pricing-models/{model_id}/rules`
- `GET    /api/products`
- `POST   /api/products`
- `GET    /api/products/{product_id}`
- `PATCH  /api/products/{product_id}`
- `DELETE /api/products/{product_id}`
- `GET    /api/services`
- `POST   /api/services`

## System

- `GET    /`
- `GET    /health`

## Tools, MCP & Registry

- `GET    /api/connector-logs`
- `GET    /api/tool-executions`
- `POST   /api/tools`
- `GET    /api/tools`
- `GET    /api/tools/{tool_id}`
- `POST   /api/tools/{tool_id}/execute`
- `POST   /api/tools/{tool_id}/permissions`

## Webhooks & Events

- `GET    /api/webhook-events`
- `POST   /api/webhooks/receive/{integration_id}`

## tenants

- `GET    /tenants/`
- `POST   /tenants/`
- `GET    /tenants/{tenant_id}`
- `DELETE /tenants/{tenant_id}`

## users

- `POST   /users/`
- `GET    /users/{user_id}`
