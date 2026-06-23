# Follei API Workflow with JSON Examples

This document provides a complete workflow guide for all API endpoints across 7 domains, including request/response JSON examples.

---

## Domain 1 - Identity & Auth

### 1.1 Register New Tenant
**Endpoint:** `POST /auth/register`

**Purpose:** Create a new tenant with an admin user and return authentication tokens.

**Request JSON:**
```json
{
  "domain": "acme.com",
  "name": "Acme Corporation",
  "admin_email": "admin@acme.com",
  "admin_password": "SecurePass123!",
  "admin_first_name": "John",
  "admin_last_name": "Doe"
}
```

**Response JSON:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Workflow:**
1. Client sends registration payload with tenant details
2. System checks if domain already exists (409 if duplicate)
3. System checks if email already exists (409 if duplicate)
4. Creates tenant record
5. Creates admin user with hashed password
6. Returns JWT access token for immediate authentication

---

### 1.2 Login
**Endpoint:** `POST /auth/login`

**Purpose:** Authenticate user and return JWT token.

**Request JSON:**
```json
{
  "email": "admin@acme.com",
  "password": "SecurePass123!"
}
```

**Response JSON:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Workflow:**
1. Client sends credentials
2. System verifies email exists and password matches hash
3. Checks if user is active (403 if inactive)
4. Updates last_login_at timestamp
5. Returns JWT token

---

### 1.3 Get Current User
**Endpoint:** `GET /auth/me`

**Purpose:** Retrieve authenticated user's profile.

**Headers:** `Authorization: Bearer <token>`

**Response JSON:**
```json
{
  "id": "11111111-1111-4111-8111-111111111111",
  "email": "admin@acme.com",
  "first_name": "John",
  "last_name": "Doe",
  "role": "admin",
  "is_active": true,
  "tenant_id": "22222222-2222-4222-8222-222222222222",
  "created_at": "2026-01-15T10:30:00",
  "updated_at": "2026-01-15T10:30:00"
}
```

**Workflow:**
1. Client sends Bearer token in Authorization header
2. System decodes and validates JWT
3. Fetches user from database
4. Returns user profile (excluding hashed_password)

---

## Domain 2 - Tenants & Users

### 2.1 Create Tenant
**Endpoint:** `POST /api/v1/tenants`

**Purpose:** Create a new tenant organization.

**Headers:** `Authorization: Bearer <token>`

**Request JSON:**
```json
{
  "name": "Acme Corporation",
  "slug": "acme-corp",
  "plan_id": "33333333-3333-4333-8333-333333333333",
  "settings": {
    "timezone": "Asia/Kolkata",
    "language": "en",
    "features": {
      "advanced_analytics": true,
      "api_access": true
    },
    "branding": {
      "logo_url": "https://example.com/logo.png",
      "primary_color": "#007bff"
    }
  }
}
```

**Response JSON:**
```json
{
  "id": "22222222-2222-4222-8222-222222222222",
  "name": "Acme Corporation",
  "slug": "acme-corp",
  "status": "active",
  "created_at": "2026-01-15T10:30:00"
}
```

**Workflow:**
1. Validates request payload
2. Generates new UUID for tenant
3. Inserts tenant record with 'active' status
4. Creates default tenant_settings entry
5. Returns created tenant

---

### 2.2 List Tenants
**Endpoint:** `GET /api/v1/tenants`

**Purpose:** Retrieve paginated list of tenants.

**Query Parameters:**
- `page` (default: 1)
- `page_size` (default: 20)

**Response JSON:**
```json
{
  "items": [
    {
      "id": "22222222-2222-4222-8222-222222222222",
      "name": "Acme Corporation",
      "slug": "acme-corp",
      "status": "active",
      "created_at": "2026-01-15T10:30:00",
      "updated_at": "2026-01-15T10:30:00"
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 20
}
```

**Workflow:**
1. Calculates offset from page parameter
2. Executes paginated SQL query
3. Returns items with pagination metadata

---

### 2.3 Get Tenant Details
**Endpoint:** `GET /api/v1/tenants/{tenant_id}`

**Purpose:** Retrieve full tenant details with settings and usage stats.

**Response JSON:**
```json
{
  "id": "22222222-2222-4222-8222-222222222222",
  "name": "Acme Corporation",
  "slug": "acme-corp",
  "status": "active",
  "domain": "acme.com",
  "created_at": "2026-01-15T10:30:00",
  "updated_at": "2026-01-15T10:30:00",
  "settings": {
    "timezone": "Asia/Kolkata",
    "language": "en",
    "features": {}
  },
  "usage": {
    "users": 5,
    "documents": 120,
    "api_calls": 15420
  }
}
```

**Workflow:**
1. Fetches tenant by ID
2. Fetches associated settings
3. Calculates usage metrics (users, documents, API calls)
4. Returns combined response

---

### 2.4 Update Tenant
**Endpoint:** `PATCH /api/v1/tenants/{tenant_id}`

**Purpose:** Update tenant details and settings.

**Request JSON:**
```json
{
  "name": "Acme Corp Updated",
  "status": "active",
  "settings": {
    "timezone": "America/New_York",
    "features": {
      "advanced_analytics": true
    }
  }
}
```

**Response JSON:**
```json
{
  "id": "22222222-2222-4222-8222-222222222222",
  "name": "Acme Corp Updated",
  "slug": "acme-corp",
  "status": "active",
  "settings": {
    "timezone": "America/New_York",
    "features": {
      "advanced_analytics": true
    }
  },
  "usage": {
    "users": 5,
    "documents": 120,
    "api_calls": 15420
  }
}
```

**Workflow:**
1. Fetches current tenant
2. Updates provided fields using COALESCE (keeps existing if null)
3. Merges settings if provided
4. Returns updated tenant with fresh usage stats

---

### 2.5 Delete Tenant
**Endpoint:** `DELETE /api/v1/tenants/{tenant_id}`

**Purpose:** Permanently delete a tenant.

**Response:** `204 No Content`

**Workflow:**
1. Deletes tenant record (cascades to related records)
2. Returns empty 204 response

---

### 2.6 Create User
**Endpoint:** `POST /api/v1/users`

**Purpose:** Create a new user within a tenant.

**Headers:** `Authorization: Bearer <token>`

**Request JSON:**
```json
{
  "email": "jane@acme.com",
  "password": "UserPass123!",
  "full_name": "Jane Smith",
  "role_ids": [
    "44444444-4444-4444-8444-444444444444"
  ],
  "tenant_id": "22222222-2222-4222-8222-222222222222"
}
```

**Response JSON:**
```json
{
  "id": "55555555-5555-4555-8555-555555555555",
  "tenant_id": "22222222-2222-4222-8222-222222222222",
  "email": "jane@acme.com",
  "full_name": "Jane Smith",
  "first_name": "Jane",
  "last_name": "Smith",
  "role": "member",
  "status": "active",
  "is_active": true,
  "roles": ["member"],
  "permissions": ["read", "write", "delete"],
  "created_at": "2026-01-15T10:30:00",
  "updated_at": "2026-01-15T10:30:00"
}
```

**Workflow:**
1. Validates tenant exists
2. Checks email uniqueness (409 if exists)
3. Hashes password
4. Creates user with 'member' role by default
5. Assigns specified roles via user_roles table
6. Returns user with computed roles and permissions

---

### 2.7 List Users
**Endpoint:** `GET /api/v1/users`

**Purpose:** List users with filtering.

**Query Parameters:**
- `tenant_id` (optional)
- `role` (optional)
- `status` (optional)
- `page` (default: 1)
- `page_size` (default: 20)

**Response JSON:**
```json
{
  "items": [
    {
      "id": "55555555-5555-4555-8555-555555555555",
      "tenant_id": "22222222-2222-4222-8222-222222222222",
      "email": "jane@acme.com",
      "full_name": "Jane Smith",
      "role": "member",
      "status": "active",
      "roles": ["member"],
      "permissions": ["read", "write", "delete"],
      "created_at": "2026-01-15T10:30:00"
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 20
}
```

**Workflow:**
1. Builds dynamic WHERE clause from filters
2. Executes paginated query
3. Enriches each user with roles and permissions
4. Returns paginated results

---

### 2.8 Get User
**Endpoint:** `GET /api/v1/users/{user_id}`

**Purpose:** Retrieve single user details.

**Response JSON:**
```json
{
  "id": "55555555-5555-4555-8555-555555555555",
  "tenant_id": "22222222-2222-4222-8222-222222222222",
  "email": "jane@acme.com",
  "full_name": "Jane Smith",
  "role": "member",
  "status": "active",
  "roles": ["member", "admin"],
  "permissions": ["users.read", "users.write", "tenants.read"],
  "created_at": "2026-01-15T10:30:00",
  "updated_at": "2026-01-15T10:30:00"
}
```

---

### 2.9 Update User
**Endpoint:** `PATCH /api/v1/users/{user_id}`

**Purpose:** Update user details.

**Request JSON:**
```json
{
  "full_name": "Jane Doe",
  "status": "active",
  "role_ids": [
    "44444444-4444-4444-8444-444444444444",
    "55555555-5555-4555-8555-555555555555"
  ]
}
```

**Response JSON:** Same as Get User

**Workflow:**
1. Updates full_name (splits into first/last)
2. Updates status and is_active
3. Replaces all role assignments
4. Returns updated user

---

### 2.10 Delete/Deactivate User
**Endpoint:** `DELETE /api/v1/users/{user_id}`

**Purpose:** Deactivate user (soft delete).

**Response:** `204 No Content`

**Workflow:**
1. Sets status='inactive' and is_active=false
2. Returns 204

---

### 2.11 Assign Role
**Endpoint:** `POST /api/v1/users/{user_id}/roles`

**Purpose:** Assign a role to a user.

**Request JSON:**
```json
{
  "role_id": "44444444-4444-4444-8444-444444444444"
}
```

**Response JSON:**
```json
{
  "message": "Role assigned"
}
```

---

### 2.12 Remove Role
**Endpoint:** `DELETE /api/v1/users/{user_id}/roles/{role_id}`

**Purpose:** Remove a role from a user.

**Response:** `204 No Content`

---

### 2.13 Create Role
**Endpoint:** `POST /api/v1/roles`

**Purpose:** Create a new role with permissions.

**Request JSON:**
```json
{
  "name": "sales_manager",
  "display_name": "Sales Manager",
  "permissions": [
    "leads.read",
    "leads.write",
    "opportunities.read",
    "meetings.create"
  ],
  "tenant_id": "22222222-2222-4222-8222-222222222222"
}
```

**Response JSON:**
```json
{
  "id": "66666666-6666-4666-8666-666666666666",
  "name": "sales_manager",
  "permissions": [
    "leads.read",
    "leads.write",
    "opportunities.read",
    "meetings.create"
  ]
}
```

**Workflow:**
1. Creates role record
2. For each permission string, parses resource.action
3. Creates permission if not exists
4. Links permission to role via role_permissions
5. Returns role with permissions

---

### 2.14 List Roles
**Endpoint:** `GET /api/v1/roles`

**Response JSON:**
```json
{
  "items": [
    {
      "id": "66666666-6666-4666-8666-666666666666",
      "tenant_id": "22222222-2222-4222-8222-222222222222",
      "name": "sales_manager",
      "description": "Sales Manager",
      "created_at": "2026-01-15T10:30:00"
    }
  ]
}
```

---

### 2.15 List Permissions
**Endpoint:** `GET /api/v1/permissions`

**Response JSON:**
```json
{
  "items": [
    {
      "id": "77777777-7777-4777-8777-777777777777",
      "resource": "leads",
      "action": "read",
      "created_at": "2026-01-15T10:30:00"
    },
    {
      "id": "88888888-8888-4888-8888-888888888888",
      "resource": "leads",
      "action": "write",
      "created_at": "2026-01-15T10:30:00"
    }
  ]
}
```

---

### 2.16 Create API Key
**Endpoint:** `POST /api/v1/tenant-api-keys`

**Purpose:** Generate API key for tenant.

**Headers:** `Authorization: Bearer <token>`

**Request JSON:**
```json
{
  "name": "Production API Key",
  "permissions": [
    "api.read",
    "api.write"
  ]
}
```

**Response JSON:**
```json
{
  "id": "99999999-9999-4999-8999-999999999999",
  "key": "fl_live_abc123def456...",
  "name": "Production API Key"
}
```

**Workflow:**
1. Generates secure API key with prefix 'fl_live_'
2. Hashes key for storage
3. Stores key_hash and scopes
4. Returns plaintext key (only shown once!)

---

### 2.17 List API Keys
**Endpoint:** `GET /api/v1/tenant-api-keys`

**Response JSON:**
```json
{
  "items": [
    {
      "id": "99999999-9999-4999-8999-999999999999",
      "name": "Production API Key",
      "prefix": "fl_live_abc1",
      "created_at": "2026-01-15T10:30:00"
    }
  ]
}
```

**Note:** Only shows key prefix, never full key.

---

### 2.18 Revoke API Key
**Endpoint:** `DELETE /api/v1/tenant-api-keys/{key_id}`

**Purpose:** Deactivate an API key.

**Response:** `204 No Content`

---

## Domain 3 - Agents & AI Workforce

### 3.1 Create Agent
**Endpoint:** `POST /api/v1/agents`

**Purpose:** Create a new AI agent.

**Headers:** `Authorization: Bearer <token>`

**Request JSON:**
```json
{
  "name": "SDR Agent",
  "type": "sdr",
  "description": "Handles sales development conversations",
  "tenant_id": "22222222-2222-4222-8222-222222222222",
  "config": {
    "system_prompt": "You are a helpful sales assistant.",
    "model": "claude-3-5-sonnet-20240620",
    "tools": ["search_knowledge", "create_lead"],
    "temperature": 0.7,
    "max_tokens": 1024
  },
  "status": "active"
}
```

**Response JSON:**
```json
{
  "id": "aaaaaaaa-aaaa-4aaa-aaaa-aaaaaaaaaaaa",
  "name": "SDR Agent",
  "type": "sdr",
  "tenant_id": "22222222-2222-4222-8222-222222222222",
  "config": {
    "system_prompt": "You are a helpful sales assistant.",
    "model": "claude-3-5-sonnet-20240620",
    "tools": ["search_knowledge", "create_lead"],
    "temperature": 0.7,
    "max_tokens": 1024
  },
  "status": "active",
  "created_at": "2026-01-15T10:30:00",
  "version": 1
}
```

**Workflow:**
1. Validates agent configuration
2. Creates agent record
3. Creates initial version (v1) in agent_versions
4. Returns agent with version info

---

### 3.2 List Agents
**Endpoint:** `GET /api/v1/agents`

**Query Parameters:**
- `tenant_id` (optional)
- `type` (optional)
- `status` (optional)
- `page` (default: 1)
- `page_size` (default: 20)

**Response JSON:**
```json
{
  "items": [
    {
      "id": "aaaaaaaa-aaaa-4aaa-aaaa-aaaaaaaaaaaa",
      "name": "SDR Agent",
      "type": "sdr",
      "tenant_id": "22222222-2222-4222-8222-222222222222",
      "created_at": "2026-01-15T10:30:00"
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 20
}
```

---

### 3.3 Get Agent
**Endpoint:** `GET /api/v1/agents/{agent_id}`

**Response JSON:**
```json
{
  "id": "aaaaaaaa-aaaa-4aaa-aaaa-aaaaaaaaaaaa",
  "name": "SDR Agent",
  "type": "sdr",
  "description": "You are a helpful sales assistant.",
  "tenant_id": "22222222-2222-4222-8222-222222222222",
  "config": {
    "system_prompt": "You are a helpful sales assistant.",
    "model": "claude-3-5-sonnet-20240620",
    "tools": ["search_knowledge", "create_lead"],
    "temperature": 0.7,
    "max_tokens": 1024
  },
  "status": "active",
  "created_at": "2026-01-15T10:30:00",
  "updated_at": "2026-01-15T10:30:00",
  "version": 1,
  "stats": {
    "conversations": 45,
    "messages": 320,
    "avg_confidence": 0.87,
    "avg_response_time_ms": 1250
  }
}
```

**Workflow:**
1. Fetches agent by ID
2. Fetches latest version config
3. Computes stats (conversations, messages, confidence)
4. Merges config with agent table fields
5. Returns enriched agent object

---

### 3.4 Update Agent
**Endpoint:** `PATCH /api/v1/agents/{agent_id}`

**Request JSON:**
```json
{
  "name": "SDR Agent v2",
  "config": {
    "temperature": 0.8,
    "max_tokens": 2048
  },
  "status": "active"
}
```

**Response JSON:** Same as Get Agent (with updated version)

**Workflow:**
1. Updates basic fields (name, status)
2. Merges config with existing version
3. Creates new agent version
4. Returns updated agent

---

### 3.5 Delete Agent
**Endpoint:** `DELETE /api/v1/agents/{agent_id}`

**Response:** `204 No Content`

---

### 3.6 Chat with Agent
**Endpoint:** `POST /api/v1/agents/{agent_id}/chat`

**Purpose:** Send message to agent and get AI response.

**Request JSON:**
```json
{
  "message": "What are your pricing plans?",
  "conversation_id": "bbbbbbbb-bbbb-4bbb-bbbb-bbbbbbbbbbbb",
  "session_id": "cccccccc-cccc-4ccc-cccc-cccccccccccc",
  "context": {
    "customer_id": "33333333-3333-4333-8333-333333333333",
    "lead_id": "22222222-2222-4222-8222-222222222222"
  },
  "metadata": {
    "source": "web",
    "page_url": "https://acme.com/pricing"
  }
}
```

**Response JSON:**
```json
{
  "message_id": "dddddddd-dddd-4ddd-dddd-dddddddddddd",
  "conversation_id": "bbbbbbbb-bbbb-4bbb-bbbb-bbbbbbbbbbbb",
  "agent_id": "aaaaaaaa-aaaa-4aaa-aaaa-aaaaaaaaaaaa",
  "content": "Stub response from SDR Agent: What are your pricing plans?",
  "role": "assistant",
  "citations": [],
  "confidence": 0.0,
  "supported": false,
  "tool_calls": [],
  "latency_ms": 0,
  "tokens_used": {
    "input": 0,
    "output": 0,
    "total": 0
  },
  "created_at": "2026-01-15T10:30:00"
}
```

**Workflow:**
1. Validates agent exists
2. Creates conversation if not provided
3. Stores user message
4. Generates AI response (stub or via Claude API)
5. Stores assistant message with metadata
6. Returns response with citations, confidence, tool calls

---

### 3.7 Create Agent Version (Snapshot)
**Endpoint:** `POST /api/v1/agents/{agent_id}/versions`

**Purpose:** Create versioned snapshot of agent config.

**Request JSON:**
```json
{
  "name": "v2 - Improved prompts",
  "notes": "Updated system prompt for better handling of pricing questions"
}
```

**Response JSON:**
```json
{
  "version": 2,
  "name": "v2 - Improved prompts",
  "created_at": "2026-01-15T10:30:00"
}
```

---

### 3.8 List Agent Versions
**Endpoint:** `GET /api/v1/agents/{agent_id}/versions`

**Response JSON:**
```json
{
  "items": [
    {
      "version": 1,
      "name": "Initial version",
      "created_at": "2026-01-15T10:30:00"
    },
    {
      "version": 2,
      "name": "v2 - Improved prompts",
      "created_at": "2026-01-15T11:00:00"
    }
  ]
}
```

---

### 3.9 Start Agent Session
**Endpoint:** `POST /api/v1/agents/{agent_id}/sessions`

**Purpose:** Start a new agent session.

**Request JSON:**
```json
{
  "user_id": "55555555-5555-4555-8555-555555555555",
  "conversation_id": "bbbbbbbb-bbbb-4bbb-bbbb-bbbbbbbbbbbb",
  "metadata": {
    "channel": "web",
    "ip_address": "192.168.1.1"
  }
}
```

**Response JSON:**
```json
{
  "id": "eeeeeeee-eeee-4eee-eeee-eeeeeeeeeeee",
  "status": "active",
  "started_at": "2026-01-15T10:30:00"
}
```

---

### 3.10 List Agent Sessions
**Endpoint:** `GET /api/v1/agents/{agent_id}/sessions`

**Response JSON:**
```json
{
  "items": [
    {
      "id": "eeeeeeee-eeee-4eee-eeee-eeeeeeeeeeee",
      "status": "active",
      "started_at": "2026-01-15T10:30:00",
      "ended_at": null
    }
  ]
}
```

---

### 3.11 Update Agent Session
**Endpoint:** `PATCH /api/v1/agents/{agent_id}/sessions/{session_id}`

**Request JSON:**
```json
{
  "status": "ended",
  "end_reason": "user_disconnected"
}
```

**Response JSON:**
```json
{
  "id": "eeeeeeee-eeee-4eee-eeee-eeeeeeeeeeee",
  "status": "ended",
  "end_reason": "user_disconnected"
}
```

---

### 3.12 Create Agent Task
**Endpoint:** `POST /api/v1/agents/{agent_id}/tasks`

**Purpose:** Create a background task for agent.

**Request JSON:**
```json
{
  "type": "research",
  "description": "Research competitor pricing",
  "priority": "high",
  "due_at": "2026-01-16T10:00:00",
  "context": {
    "competitor": "CompetitorCorp",
    "product": "Enterprise Plan"
  }
}
```

**Response JSON:**
```json
{
  "id": "ffffffff-ffff-4fff-ffff-ffffffffffff",
  "type": "research",
  "status": "pending",
  "priority": "high"
}
```

---

### 3.13 List Agent Tasks
**Endpoint:** `GET /api/v1/agents/{agent_id}/tasks`

**Response JSON:**
```json
{
  "items": [
    {
      "id": "ffffffff-ffff-4fff-ffff-ffffffffffff",
      "type": "research",
      "status": "pending",
      "priority": "high",
      "due_at": "2026-01-16T10:00:00"
    }
  ]
}
```

---

### 3.14 Update Agent Task
**Endpoint:** `PATCH /api/v1/agent-tasks/{task_id}`

**Request JSON:**
```json
{
  "status": "completed",
  "result": {
    "findings": "CompetitorCorp pricing is 20% higher",
    "confidence": 0.9
  }
}
```

**Response JSON:**
```json
{
  "id": "ffffffff-ffff-4fff-ffff-ffffffffffff",
  "status": "completed",
  "result": {
    "findings": "CompetitorCorp pricing is 20% higher",
    "confidence": 0.9
  }
}
```

---

### 3.15 Store Agent Memory
**Endpoint:** `POST /api/v1/agents/{agent_id}/memories`

**Purpose:** Store memory for agent context.

**Request JSON:**
```json
{
  "type": "preference",
  "key": "customer_pricing_tier",
  "value": "enterprise",
  "ttl_days": 30,
  "context": {
    "customer_id": "33333333-3333-4333-8333-333333333333"
  }
}
```

**Response JSON:**
```json
{
  "id": "11111111-1111-4111-8111-111111111111",
  "type": "preference",
  "key": "customer_pricing_tier",
  "value": "enterprise"
}
```

---

### 3.16 List Agent Memories
**Endpoint:** `GET /api/v1/agents/{agent_id}/memories`

**Response JSON:**
```json
{
  "items": [
    {
      "id": "11111111-1111-4111-8111-111111111111",
      "type": "preference",
      "key": "customer_pricing_tier",
      "value": "enterprise",
      "created_at": "2026-01-15T10:30:00"
    }
  ]
}
```

---

### 3.17 Submit Agent Feedback
**Endpoint:** `POST /api/v1/agents/{agent_id}/feedback`

**Purpose:** Submit feedback for agent response.

**Request JSON:**
```json
{
  "rating": 5,
  "comment": "Great response, very helpful!",
  "message_id": "dddddddd-dddd-4ddd-dddd-dddddddddddd",
  "category": "accuracy"
}
```

**Response JSON:**
```json
{
  "id": "22222222-2222-4222-8222-222222222222",
  "rating": 5,
  "comment": "Great response, very helpful!",
  "category": "accuracy"
}
```

---

### 3.18 List Agent Feedback
**Endpoint:** `GET /api/v1/agents/{agent_id}/feedback`

**Response JSON:**
```json
{
  "items": [
    {
      "id": "22222222-2222-4222-8222-222222222222",
      "rating": 5,
      "comment": "Great response, very helpful!",
      "created_at": "2026-01-15T10:30:00"
    }
  ],
  "avg_rating": 4.5,
  "total": 2
}
```

---

### 3.19 Grant Tool Permission
**Endpoint:** `POST /api/v1/agents/{agent_id}/tool-permissions`

**Purpose:** Allow agent to use specific tool.

**Request JSON:**
```json
{
  "tool_id": "33333333-3333-4333-8333-333333333333",
  "permission": "execute",
  "constraints": {
    "max_calls_per_day": 100,
    "allowed_entities": ["leads", "contacts"]
  }
}
```

**Response JSON:**
```json
{
  "id": "44444444-4444-4444-8444-444444444444",
  "tool_id": "33333333-3333-4333-8333-333333333333",
  "permission": "execute",
  "constraints": {
    "max_calls_per_day": 100,
    "allowed_entities": ["leads", "contacts"]
  }
}
```

---

### 3.20 List Tool Permissions
**Endpoint:** `GET /api/v1/agents/{agent_id}/tool-permissions`

**Response JSON:**
```json
{
  "items": [
    {
      "tool_id": "33333333-3333-4333-8333-333333333333",
      "tool_name": "search_knowledge",
      "is_allowed": true
    }
  ]
}
```

---

## Domain 4 - System, Health & Jobs

### 4.1 Health Check
**Endpoint:** `GET /api/v1/health`

**Purpose:** Check API and service health.

**Response JSON:**
```json
{
  "status": "healthy",
  "services": {
    "api": "ok",
    "postgres": "ok",
    "redis": "not_configured",
    "qdrant": "not_configured",
    "kafka": "not_configured",
    "mistral": "not_configured"
  },
  "version": "0.1.0",
  "timestamp": "2026-01-15T10:30:00"
}
```

---

### 4.2 Audit Logs
**Endpoint:** `GET /api/v1/audit-logs`

**Query Parameters:**
- `tenant_id` (optional)
- `user_id` (optional)
- `action` (optional)
- `resource` (optional)
- `from` (optional, datetime)
- `to` (optional, datetime)

**Response JSON:**
```json
{
  "items": [
    {
      "id": "55555555-5555-4555-8555-555555555555",
      "tenant_id": "22222222-2222-4222-8222-222222222222",
      "user_id": "66666666-6666-4666-8666-666666666666",
      "action": "user.create",
      "resource_type": "user",
      "entity_id": "77777777-7777-4777-8777-777777777777",
      "details": {"email": "jane@acme.com"},
      "created_at": "2026-01-15T10:30:00"
    }
  ]
}
```

---

### 4.3 Create Background Job
**Endpoint:** `POST /api/v1/background-jobs`

**Purpose:** Queue a background job.

**Request JSON:**
```json
{
  "type": "document_processing",
  "payload": {
    "document_id": "88888888-8888-4888-8888-888888888888",
    "priority": "high"
  },
  "priority": "high",
  "scheduled_at": "2026-01-15T11:00:00"
}
```

**Response JSON:**
```json
{
  "id": "99999999-9999-4999-8999-999999999999",
  "type": "document_processing",
  "status": "queued",
  "progress": 0
}
```

---

### 4.4 List Background Jobs
**Endpoint:** `GET /api/v1/background-jobs`

**Response JSON:**
```json
{
  "items": [
    {
      "id": "99999999-9999-4999-8999-999999999999",
      "job_type": "document_processing",
      "status": "queued",
      "payload": {
        "document_id": "88888888-8888-4888-8888-888888888888",
        "priority": "high"
      },
      "created_at": "2026-01-15T10:30:00"
    }
  ]
}
```

---

### 4.5 Get Background Job
**Endpoint:** `GET /api/v1/background-jobs/{job_id}`

**Response JSON:**
```json
{
  "id": "99999999-9999-4999-8999-999999999999",
  "job_type": "document_processing",
  "status": "completed",
  "payload": {
    "document_id": "88888888-8888-4888-8888-888888888888"
  },
  "progress": 100,
  "result": {
    "document_id": "88888888-8888-4888-8888-888888888888",
    "chunks_created": 25
  },
  "created_at": "2026-01-15T10:30:00",
  "updated_at": "2026-01-15T10:30:15"
}
```

---

### 4.6 Create Feature Flag
**Endpoint:** `POST /api/v1/feature-flags`

**Purpose:** Create a feature flag for gradual rollouts.

**Request JSON:**
```json
{
  "name": "new_dashboard",
  "description": "Enable new analytics dashboard",
  "enabled": false,
  "target": {
    "tenant_ids": ["22222222-2222-4222-8222-222222222222"],
    "user_percentage": 10,
    "environments": ["staging", "production"]
  }
}
```

**Response JSON:**
```json
{
  "id": "aaaaaaaa-aaaa-4aaa-aaaa-aaaaaaaaaaaa",
  "name": "new_dashboard",
  "enabled": false,
  "target": {
    "tenant_ids": ["22222222-2222-4222-8222-222222222222"],
    "user_percentage": 10,
    "environments": ["staging", "production"]
  }
}
```

---

### 4.7 List Feature Flags
**Endpoint:** `GET /api/v1/feature-flags`

**Response JSON:**
```json
{
  "items": [
    {
      "id": "aaaaaaaa-aaaa-4aaa-aaaa-aaaaaaaaaaaa",
      "name": "new_dashboard",
      "enabled": false,
      "target": {
        "tenant_ids": ["22222222-2222-4222-8222-222222222222"]
      },
      "created_at": "2026-01-15T10:30:00"
    }
  ]
}
```

---

### 4.8 Toggle Feature Flag
**Endpoint:** `PATCH /api/v1/feature-flags/{flag_id}`

**Request JSON:**
```json
{
  "enabled": true
}
```

**Response JSON:**
```json
{
  "id": "aaaaaaaa-aaaa-4aaa-aaaa-aaaaaaaaaaaa",
  "enabled": true
}
```

---

### 4.9 Send Notification
**Endpoint:** `POST /api/v1/notifications`

**Purpose:** Create and send notification.

**Request JSON:**
```json
{
  "user_id": "55555555-5555-4555-8555-555555555555",
  "type": "email",
  "title": "New lead assigned",
  "body": "You have been assigned a new high-priority lead",
  "data": {
    "lead_id": "bbbbbbbb-bbbb-4bbb-bbbb-bbbbbbbbbbbb",
    "priority": "high"
  },
  "priority": "high"
}
```

**Response JSON:**
```json
{
  "id": "cccccccc-cccc-4ccc-cccc-cccccccccccc",
  "title": "New lead assigned",
  "read": false,
  "created_at": "2026-01-15T10:30:00"
}
```

---

### 4.10 List Notifications
**Endpoint:** `GET /api/v1/notifications`

**Response JSON:**
```json
{
  "items": [
    {
      "id": "cccccccc-cccc-4ccc-cccc-cccccccccccc",
      "title": "New lead assigned",
      "body": "You have been assigned a new high-priority lead",
      "read_at": null,
      "created_at": "2026-01-15T10:30:00"
    }
  ],
  "unread_count": 1
}
```

---

### 4.11 Mark Notification as Read
**Endpoint:** `PATCH /api/v1/notifications/{id}/read`

**Response JSON:**
```json
{
  "id": "cccccccc-cccc-4ccc-cccc-cccccccccccc",
  "read": true,
  "read_at": "2026-01-15T10:35:00"
}
```

---

### 4.12 API Request Logs
**Endpoint:** `GET /api/v1/api-request-logs`

**Query Parameters:**
- `tenant_id` (optional)
- `endpoint` (optional)
- `status` (optional, alias for status_code)
- `from` (optional, datetime)

**Response JSON:**
```json
{
  "items": [
    {
      "id": "dddddddd-dddd-4ddd-dddd-dddddddddddd",
      "tenant_id": "22222222-2222-4222-8222-222222222222",
      "path": "/api/v1/leads",
      "method": "POST",
      "status_code": 201,
      "latency_ms": 45,
      "created_at": "2026-01-15T10:30:00"
    }
  ]
}
```

---

## Domain 5 - Conversations & Messages

### 5.1 Create Conversation
**Endpoint:** `POST /api/conversations`

**Purpose:** Start a new conversation.

**Request JSON:**
```json
{
  "title": "Pricing inquiry",
  "type": "sales",
  "tenant_id": "22222222-2222-4222-8222-222222222222",
  "lead_id": "bbbbbbbb-bbbb-4bbb-bbbb-bbbbbbbbbbbb",
  "customer_id": "33333333-3333-4333-8333-333333333333",
  "agent_id": "aaaaaaaa-aaaa-4aaa-aaaa-aaaaaaaaaaaa",
  "channel": "web",
  "metadata": {
    "source": "website",
    "page": "/pricing"
  }
}
```

**Response JSON:**
```json
{
  "id": "eeeeeeee-eeee-4eee-eeee-eeeeeeeeeeee",
  "title": "Pricing inquiry",
  "type": "sales",
  "status": "active",
  "tenant_id": "22222222-2222-4222-8222-222222222222",
  "lead_id": "bbbbbbbb-bbbb-4bbb-bbbb-bbbbbbbbbbbb",
  "customer_id": "33333333-3333-4333-8333-333333333333",
  "agent_id": "aaaaaaaa-aaaa-4aaa-aaaa-aaaaaaaaaaaa",
  "channel": "web",
  "metadata": {
    "source": "website",
    "page": "/pricing"
  },
  "participants": [],
  "message_count": 0,
  "created_at": "2026-01-15T10:30:00",
  "updated_at": "2026-01-15T10:30:00"
}
```

**Workflow:**
1. Validates related entities (lead, customer, agent)
2. Creates conversation with 'active' status
3. Initializes empty participants and messages
4. Returns conversation object

---

### 5.2 List Conversations
**Endpoint:** `GET /api/conversations`

**Query Parameters:**
- `tenant_id` (optional)
- `agent_id` (optional)
- `status` (optional)
- `type` (optional)
- `page` (default: 1)
- `page_size` (default: 20)

**Response JSON:**
```json
{
  "items": [
    {
      "id": "eeeeeeee-eeee-4eee-eeee-eeeeeeeeeeee",
      "title": "Pricing inquiry",
      "type": "sales",
      "status": "active",
      "tenant_id": "22222222-2222-4222-8222-222222222222",
      "agent_id": "aaaaaaaa-aaaa-4aaa-aaaa-aaaaaaaaaaaa",
      "channel": "web",
      "participants": [],
      "message_count": 5,
      "created_at": "2026-01-15T10:30:00",
      "updated_at": "2026-01-15T10:35:00"
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 20
}
```

---

### 5.3 Get Conversation
**Endpoint:** `GET /api/conversations/{conversation_id}`

**Response JSON:**
```json
{
  "id": "eeeeeeee-eeee-4eee-eeee-eeeeeeeeeeee",
  "title": "Pricing inquiry",
  "type": "sales",
  "status": "active",
  "tenant_id": "22222222-2222-4222-8222-222222222222",
  "lead_id": "bbbbbbbb-bbbb-4bbb-bbbb-bbbbbbbbbbbb",
  "customer_id": "33333333-3333-4333-8333-333333333333",
  "agent_id": "aaaaaaaa-aaaa-4aaa-aaaa-aaaaaaaaaaaa",
  "channel": "web",
  "metadata": {
    "source": "website"
  },
  "participants": [
    {
      "id": "ffffffff-ffff-4fff-ffff-ffffffffffff",
      "conversation_id": "eeeeeeee-eeee-4eee-eeee-eeeeeeeeeeee",
      "user_id": "55555555-5555-4555-8555-555555555555",
      "type": "lead",
      "role": "buyer",
      "name": "Asha Kumar",
      "metadata": {
        "timezone": "Asia/Kolkata"
      },
      "joined_at": "2026-01-15T10:30:00"
    }
  ],
  "message_count": 5,
  "created_at": "2026-01-15T10:30:00",
  "updated_at": "2026-01-15T10:35:00"
}
```

---

### 5.4 Update Conversation
**Endpoint:** `PATCH /api/conversations/{conversation_id}`

**Request JSON:**
```json
{
  "title": "Pricing inquiry - Updated",
  "status": "escalated",
  "metadata": {
    "priority": "high",
    "escalation_reason": "complex_pricing"
  }
}
```

**Response JSON:** Same as Get Conversation

---

### 5.5 Delete Conversation
**Endpoint:** `DELETE /api/conversations/{conversation_id}`

**Response:** `204 No Content`

**Workflow:**
1. Removes conversation
2. Cascades to delete participants, messages, summaries
3. Returns 204

---

### 5.6 Add Participant
**Endpoint:** `POST /api/conversations/{conversation_id}/participants`

**Purpose:** Add participant to conversation.

**Request JSON:**
```json
{
  "user_id": "55555555-5555-4555-8555-555555555555",
  "type": "agent",
  "role": "assistant",
  "name": "SDR Bot",
  "metadata": {
    "agent_type": "sdr",
    "model": "claude-3-5-sonnet"
  }
}
```

**Response JSON:**
```json
{
  "id": "11111111-1111-4111-8111-111111111111",
  "conversation_id": "eeeeeeee-eeee-4eee-eeee-eeeeeeeeeeee",
  "user_id": "55555555-5555-4555-8555-555555555555",
  "type": "agent",
  "role": "assistant",
  "name": "SDR Bot",
  "metadata": {
    "agent_type": "sdr",
    "model": "claude-3-5-sonnet"
  },
  "joined_at": "2026-01-15T10:30:00"
}
```

---

### 5.7 List Participants
**Endpoint:** `GET /api/conversations/{conversation_id}/participants`

**Response JSON:**
```json
{
  "items": [
    {
      "id": "11111111-1111-4111-8111-111111111111",
      "conversation_id": "eeeeeeee-eeee-4eee-eeee-eeeeeeeeeeee",
      "user_id": "55555555-5555-4555-8555-555555555555",
      "type": "agent",
      "role": "assistant",
      "name": "SDR Bot",
      "joined_at": "2026-01-15T10:30:00"
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 20
}
```

---

### 5.8 Remove Participant
**Endpoint:** `DELETE /api/conversations/{conversation_id}/participants/{participant_id}`

**Response:** `204 No Content`

---

### 5.9 Create Message
**Endpoint:** `POST /api/conversations/{conversation_id}/messages`

**Purpose:** Send message in conversation (supports RAG).

**Request JSON:**
```json
{
  "content": "What is your enterprise pricing?",
  "role": "user",
  "user_id": "55555555-5555-4555-8555-555555555555",
  "agent_id": "aaaaaaaa-aaaa-4aaa-aaaa-aaaaaaaaaaaa",
  "citations": [
    {
      "chunk_id": "22222222-2222-4222-8222-222222222222",
      "document_id": "33333333-3333-4333-8333-333333333333",
      "text": "Enterprise plan starts at $999/month",
      "score": 0.95
    }
  ],
  "confidence": 0.92,
  "tool_calls": [
    {
      "tool": "search_pricing",
      "input": {"plan": "enterprise"},
      "output": {"price": 999, "currency": "USD"}
    }
  ],
  "metadata": {
    "rag_used": true,
    "source": "knowledge_base"
  }
}
```

**Response JSON:**
```json
{
  "id": "44444444-4444-4444-8444-444444444444",
  "conversation_id": "eeeeeeee-eeee-4eee-eeee-eeeeeeeeeeee",
  "content": "What is your enterprise pricing?",
  "role": "user",
  "user_id": "55555555-5555-4555-8555-555555555555",
  "agent_id": "aaaaaaaa-aaaa-4aaa-aaaa-aaaaaaaaaaaa",
  "citations": [
    {
      "chunk_id": "22222222-2222-4222-8222-222222222222",
      "document_id": "33333333-3333-4333-8333-333333333333",
      "text": "Enterprise plan starts at $999/month",
      "score": 0.95
    }
  ],
  "confidence": 0.92,
  "tool_calls": [
    {
      "tool": "search_pricing",
      "input": {"plan": "enterprise"},
      "output": {"price": 999, "currency": "USD"}
    }
  ],
  "metadata": {
    "rag_used": true,
    "source": "knowledge_base"
  },
  "status": "delivered",
  "created_at": "2026-01-15T10:30:00"
}
```

**Workflow:**
1. Validates conversation exists
2. Auto-sets rag_used flag if citations/tool_calls present
3. Creates message record
4. Updates conversation timestamp
5. Returns message with all metadata

---

### 5.10 List Messages
**Endpoint:** `GET /api/conversations/{conversation_id}/messages`

**Query Parameters:**
- `page` (default: 1)
- `page_size` (default: 50)

**Response JSON:**
```json
{
  "items": [
    {
      "id": "44444444-4444-4444-8444-444444444444",
      "conversation_id": "eeeeeeee-eeee-4eee-eeee-eeeeeeeeeeee",
      "content": "What is your enterprise pricing?",
      "role": "user",
      "user_id": "55555555-5555-4555-8555-555555555555",
      "citations": [],
      "confidence": null,
      "tool_calls": [],
      "metadata": {},
      "status": "delivered",
      "created_at": "2026-01-15T10:30:00"
    },
    {
      "id": "55555555-5555-4555-8555-555555555555",
      "conversation_id": "eeeeeeee-eeee-4eee-eeee-eeeeeeeeeeee",
      "content": "Our enterprise plan starts at $999/month with unlimited users.",
      "role": "assistant",
      "agent_id": "aaaaaaaa-aaaa-4aaa-aaaa-aaaaaaaaaaaa",
      "citations": [
        {
          "chunk_id": "22222222-2222-4222-8222-222222222222",
          "text": "Enterprise plan starts at $999/month",
          "score": 0.95
        }
      ],
      "confidence": 0.92,
      "tool_calls": [],
      "metadata": {
        "rag_used": true
      },
      "status": "delivered",
      "created_at": "2026-01-15T10:30:05"
    }
  ],
  "total": 2,
  "page": 1,
  "page_size": 50
}
```

---

### 5.11 Get Message
**Endpoint:** `GET /api/messages/{message_id}`

**Response JSON:**
```json
{
  "id": "44444444-4444-4444-8444-444444444444",
  "conversation_id": "eeeeeeee-eeee-4eee-eeee-eeeeeeeeeeee",
  "content": "What is your enterprise pricing?",
  "role": "user",
  "user_id": "55555555-5555-4555-8555-555555555555",
  "citations": [],
  "confidence": null,
  "tool_calls": [],
  "metadata": {},
  "status": "delivered",
  "created_at": "2026-01-15T10:30:00"
}
```

---

### 5.12 Update Message
**Endpoint:** `PATCH /api/messages/{message_id}`

**Request JSON:**
```json
{
  "content": "What is your enterprise pricing for 50+ users?",
  "metadata": {
    "edited": true,
    "edit_reason": "clarification"
  }
}
```

**Response JSON:** Updated message object

---

### 5.13 Delete Message
**Endpoint:** `DELETE /api/messages/{message_id}`

**Response:** `204 No Content`

---

### 5.14 Add Attachment
**Endpoint:** `POST /api/messages/{message_id}/attachments`

**Purpose:** Attach file to message.

**Request JSON:**
```json
{
  "filename": "pricing_question.pdf",
  "url": "https://storage.example.com/files/pricing_question.pdf",
  "mime_type": "application/pdf",
  "size_bytes": 245760,
  "caption": "Pricing details from our current vendor",
  "metadata": {
    "uploaded_by": "55555555-5555-4555-8555-555555555555",
    "source": "desktop"
  }
}
```

**Response JSON:**
```json
{
  "id": "66666666-6666-4666-8666-666666666666",
  "message_id": "44444444-4444-4444-8444-444444444444",
  "filename": "pricing_question.pdf",
  "url": "https://storage.example.com/files/pricing_question.pdf",
  "mime_type": "application/pdf",
  "size_bytes": 245760,
  "caption": "Pricing details from our current vendor",
  "metadata": {
    "uploaded_by": "55555555-5555-4555-8555-555555555555",
    "source": "desktop"
  },
  "created_at": "2026-01-15T10:30:00"
}
```

---

### 5.15 List Attachments
**Endpoint:** `GET /api/messages/{message_id}/attachments`

**Response JSON:**
```json
{
  "items": [
    {
      "id": "66666666-6666-4666-8666-666666666666",
      "message_id": "44444444-4444-4444-8444-444444444444",
      "filename": "pricing_question.pdf",
      "url": "https://storage.example.com/files/pricing_question.pdf",
      "mime_type": "application/pdf",
      "size_bytes": 245760,
      "created_at": "2026-01-15T10:30:00"
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 20
}
```

---

### 5.16 Add Reaction
**Endpoint:** `POST /api/messages/{message_id}/reactions`

**Purpose:** React to a message.

**Request JSON:**
```json
{
  "emoji": "👍",
  "user_id": "55555555-5555-4555-8555-555555555555",
  "metadata": {
    "reaction_type": "thumbs_up"
  }
}
```

**Response JSON:**
```json
{
  "id": "77777777-7777-4777-8777-777777777777",
  "message_id": "44444444-4444-4444-8444-444444444444",
  "emoji": "👍",
  "user_id": "55555555-5555-4555-8555-555555555555",
  "metadata": {
    "reaction_type": "thumbs_up"
  },
  "created_at": "2026-01-15T10:30:00"
}
```

---

### 5.17 Create Summary
**Endpoint:** `POST /api/conversations/{conversation_id}/summaries`

**Purpose:** Generate conversation summary.

**Request JSON:**
```json
{
  "max_length": 200,
  "focus": "pricing_decision",
  "metadata": {
    "generated_by": "ai",
    "model": "claude-3-5-sonnet"
  }
}
```

**Response JSON:**
```json
{
  "id": "88888888-8888-4888-8888-888888888888",
  "conversation_id": "eeeeeeee-eeee-4eee-eeee-eeeeeeeeeeee",
  "summary": "Pricing inquiry conversation with 5 messages. Customer asked about enterprise pricing for 50+ users. Agent provided pricing details and scheduled follow-up demo.",
  "key_points": [
    "Customer needs enterprise plan for 50+ users",
    "Budget concern raised",
    "Demo scheduled for next week"
  ],
  "action_items": [
    "Follow up with customer after demo",
    "Send custom quote for 50-user tier"
  ],
  "sentiment": "positive",
  "metadata": {
    "generated_by": "ai",
    "focus": "pricing_decision"
  },
  "created_at": "2026-01-15T10:30:00"
}
```

---

### 5.18 List Summaries
**Endpoint:** `GET /api/conversations/{conversation_id}/summaries`

**Response JSON:**
```json
{
  "items": [
    {
      "id": "88888888-8888-4888-8888-888888888888",
      "conversation_id": "eeeeeeee-eeee-4eee-eeee-eeeeeeeeeeee",
      "summary": "Pricing inquiry conversation...",
      "key_points": ["Customer needs enterprise plan"],
      "action_items": ["Follow up after demo"],
      "sentiment": "positive",
      "created_at": "2026-01-15T10:30:00"
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 20
}
```

---

### 5.19 Get Conversation Metrics
**Endpoint:** `GET /api/conversations/{conversation_id}/metrics`

**Response JSON:**
```json
{
  "conversation_id": "eeeeeeee-eeee-4eee-eeee-eeeeeeeeeeee",
  "message_count": 10,
  "participant_count": 2,
  "user_message_count": 5,
  "assistant_message_count": 5,
  "attachment_count": 2,
  "reaction_count": 3,
  "summary_count": 1,
  "avg_confidence": 0.87,
  "rag_used_count": 4,
  "updated_at": "2026-01-15T10:35:00"
}
```

---

### 5.20 Log Intent
**Endpoint:** `POST /api/conversations/{conversation_id}/intents`

**Purpose:** Log detected user intent.

**Request JSON:**
```json
{
  "message_id": "44444444-4444-4444-8444-444444444444",
  "intent": "pricing_inquiry",
  "confidence": 0.95,
  "entities": [
    {
      "type": "plan",
      "value": "enterprise"
    },
    {
      "type": "user_count",
      "value": "50+"
    }
  ],
  "metadata": {
    "detected_by": "intent_classifier",
    "model": "claude-3-5-sonnet"
  }
}
```

**Response JSON:**
```json
{
  "id": "99999999-9999-4999-8999-999999999999",
  "conversation_id": "eeeeeeee-eeee-4eee-eeee-eeeeeeeeeeee",
  "message_id": "44444444-4444-4444-8444-444444444444",
  "intent": "pricing_inquiry",
  "confidence": 0.95,
  "entities": [
    {
      "type": "plan",
      "value": "enterprise"
    }
  ],
  "metadata": {
    "detected_by": "intent_classifier"
  },
  "created_at": "2026-01-15T10:30:00"
}
```

---

### 5.21 Log Sentiment
**Endpoint:** `POST /api/conversations/{conversation_id}/sentiments`

**Request JSON:**
```json
{
  "message_id": "44444444-4444-4444-8444-444444444444",
  "sentiment": "positive",
  "score": 0.78,
  "aspects": [
    {
      "topic": "pricing",
      "sentiment": "neutral"
    },
    {
      "topic": "support",
      "sentiment": "positive"
    }
  ],
  "metadata": {
    "analyzed_by": "sentiment_analyzer"
  }
}
```

**Response JSON:**
```json
{
  "id": "11111111-1111-4111-8111-111111111111",
  "conversation_id": "eeeeeeee-eeee-4eee-eeee-eeeeeeeeeeee",
  "message_id": "44444444-4444-4444-8444-444444444444",
  "sentiment": "positive",
  "score": 0.78,
  "aspects": [
    {
      "topic": "pricing",
      "sentiment": "neutral"
    }
  ],
  "metadata": {
    "analyzed_by": "sentiment_analyzer"
  },
  "created_at": "2026-01-15T10:30:00"
}
```

---

### 5.22 Log Emotion
**Endpoint:** `POST /api/conversations/{conversation_id}/emotions`

**Request JSON:**
```json
{
  "message_id": "44444444-4444-4444-8444-444444444444",
  "emotion": "curious",
  "intensity": 0.64,
  "metadata": {
    "detected_by": "emotion_detector"
  }
}
```

**Response JSON:**
```json
{
  "id": "22222222-2222-4222-8222-222222222222",
  "conversation_id": "eeeeeeee-eeee-4eee-eeee-eeeeeeeeeeee",
  "message_id": "44444444-4444-4444-8444-444444444444",
  "emotion": "curious",
  "intensity": 0.64,
  "metadata": {
    "detected_by": "emotion_detector"
  },
  "created_at": "2026-01-15T10:30:00"
}
```

---

### 5.23 Log Objection
**Endpoint:** `POST /api/conversations/{conversation_id}/objections`

**Purpose:** Log customer objection.

**Request JSON:**
```json
{
  "message_id": "44444444-4444-4444-8444-444444444444",
  "objection_type": "price",
  "description": "Customer thinks the enterprise plan is too expensive",
  "severity": "medium",
  "metadata": {
    "mentioned_price": 999,
    "budget": 500
  }
}
```

**Response JSON:**
```json
{
  "id": "33333333-3333-4333-8333-333333333333",
  "conversation_id": "eeeeeeee-eeee-4eee-eeee-eeeeeeeeeeee",
  "message_id": "44444444-4444-4444-8444-444444444444",
  "objection_type": "price",
  "description": "Customer thinks the enterprise plan is too expensive",
  "severity": "medium",
  "metadata": {
    "mentioned_price": 999,
    "budget": 500
  },
  "created_at": "2026-01-15T10:30:00"
}
```

---

### 5.24 Log Buying Signal
**Endpoint:** `POST /api/conversations/{conversation_id}/buying-signals`

**Purpose:** Log positive buying signal.

**Request JSON:**
```json
{
  "message_id": "44444444-4444-4444-8444-444444444444",
  "signal_type": "demo_requested",
  "description": "Customer asked for a product demo",
  "strength": 0.9,
  "metadata": {
    "preferred_date": "2026-01-20",
    "attendees": 3
  }
}
```

**Response JSON:**
```json
{
  "id": "44444444-4444-4444-8444-444444444444",
  "conversation_id": "eeeeeeee-eeee-4eee-eeee-eeeeeeeeeeee",
  "message_id": "44444444-4444-4444-8444-444444444444",
  "signal_type": "demo_requested",
  "description": "Customer asked for a product demo",
  "strength": 0.9,
  "metadata": {
    "preferred_date": "2026-01-20",
    "attendees": 3
  },
  "created_at": "2026-01-15T10:30:00"
}
```

---

## Domain 6 - Leads & Revenue

### 6.1 Create Lead
**Endpoint:** `POST /api/leads`

**Purpose:** Create a new lead.

**Request JSON:**
```json
{
  "email": "asha.kumar@techcorp.com",
  "full_name": "Asha Kumar",
  "company": "TechCorp Inc",
  "phone": "+1-555-0100",
  "source": "website",
  "tenant_id": "22222222-2222-4222-8222-222222222222",
  "status": "new",
  "priority": "high",
  "tags": ["enterprise", "pricing_inquiry"],
  "custom_fields": {
    "industry": "Technology",
    "company_size": "50-200",
    "annual_revenue": "5M-10M"
  },
  "assigned_to": "55555555-5555-4555-8555-555555555555"
}
```

**Response JSON:**
```json
{
  "id": "55555555-5555-4555-8555-555555555555",
  "email": "asha.kumar@techcorp.com",
  "full_name": "Asha Kumar",
  "company": "TechCorp Inc",
  "phone": "+1-555-0100",
  "source": "website",
  "tenant_id": "22222222-2222-4222-8222-222222222222",
  "status": "new",
  "priority": "high",
  "tags": ["enterprise", "pricing_inquiry"],
  "custom_fields": {
    "industry": "Technology",
    "company_size": "50-200"
  },
  "assigned_to": "55555555-5555-4555-8555-555555555555",
  "score": 0,
  "created_at": "2026-01-15T10:30:00",
  "updated_at": "2026-01-15T10:30:00"
}
```

---

### 6.2 List Leads
**Endpoint:** `GET /api/leads`

**Query Parameters:**
- `tenant_id` (optional)
- `status` (optional)
- `priority` (optional)
- `assigned_to` (optional)
- `source` (optional)
- `page` (default: 1)
- `page_size` (default: 20)

**Response JSON:**
```json
{
  "items": [
    {
      "id": "55555555-5555-4555-8555-555555555555",
      "email": "asha.kumar@techcorp.com",
      "full_name": "Asha Kumar",
      "company": "TechCorp Inc",
      "status": "new",
      "priority": "high",
      "score": 0,
      "source": "website",
      "created_at": "2026-01-15T10:30:00"
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 20
}
```

---

### 6.3 Get Lead
**Endpoint:** `GET /api/leads/{lead_id}`

**Response JSON:**
```json
{
  "id": "55555555-5555-4555-8555-555555555555",
  "email": "asha.kumar@techcorp.com",
  "full_name": "Asha Kumar",
  "company": "TechCorp Inc",
  "phone": "+1-555-0100",
  "source": "website",
  "tenant_id": "22222222-2222-4222-8222-222222222222",
  "status": "new",
  "priority": "high",
  "tags": ["enterprise", "pricing_inquiry"],
  "custom_fields": {
    "industry": "Technology"
  },
  "assigned_to": "55555555-5555-4555-8555-555555555555",
  "score": 0,
  "created_at": "2026-01-15T10:30:00",
  "updated_at": "2026-01-15T10:30:00"
}
```

---

### 6.4 Update Lead
**Endpoint:** `PATCH /api/leads/{lead_id}`

**Request JSON:**
```json
{
  "status": "qualified",
  "priority": "high",
  "custom_fields": {
    "industry": "Technology",
    "budget": "10000-20000",
    "timeline": "Q1-2026"
  }
}
```

**Response JSON:** Updated lead object

---

### 6.5 Delete Lead
**Endpoint:** `DELETE /api/leads/{lead_id}`

**Response:** `204 No Content`

---

### 6.6 Log Lead Activity
**Endpoint:** `POST /api/leads/{lead_id}/activities`

**Purpose:** Track lead interaction.

**Request JSON:**
```json
{
  "activity_type": "email_sent",
  "title": "Sent pricing information",
  "description": "Emailed enterprise pricing details and case studies",
  "channel": "email",
  "metadata": {
    "email_subject": "Enterprise Pricing - TechCorp",
    "attachments": ["pricing.pdf", "case_study.pdf"]
  }
}
```

**Response JSON:**
```json
{
  "id": "66666666-6666-4666-8666-666666666666",
  "lead_id": "55555555-5555-4555-8555-555555555555",
  "activity_type": "email_sent",
  "title": "Sent pricing information",
  "description": "Emailed enterprise pricing details",
  "channel": "email",
  "metadata": {
    "email_subject": "Enterprise Pricing - TechCorp"
  },
  "created_at": "2026-01-15T10:30:00"
}
```

---

### 6.7 List Lead Activities
**Endpoint:** `GET /api/leads/{lead_id}/activities`

**Response JSON:**
```json
{
  "items": [
    {
      "id": "66666666-6666-4666-8666-666666666666",
      "lead_id": "55555555-5555-4555-8555-555555555555",
      "activity_type": "email_sent",
      "title": "Sent pricing information",
      "channel": "email",
      "created_at": "2026-01-15T10:30:00"
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 20
}
```

---

### 6.8 Calculate Lead Score
**Endpoint:** `POST /api/leads/{lead_id}/scores`

**Purpose:** Compute/update lead score.

**Request JSON:**
```json
{
  "model": "predictive_v2",
  "force_recalculate": true,
  "metadata": {
    "factors_considered": ["company_size", "budget", "timeline"]
  }
}
```

**Response JSON:**
```json
{
  "id": "77777777-7777-4777-8777-777777777777",
  "lead_id": "55555555-5555-4555-8555-555555555555",
  "score": 85,
  "model": "predictive_v2",
  "factors": {
    "profile_fit": 25,
    "engagement": 30,
    "intent": 20,
    "company_size": 10
  },
  "metadata": {
    "factors_considered": ["company_size", "budget", "timeline"]
  },
  "calculated_at": "2026-01-15T10:30:00"
}
```

---

### 6.9 List Lead Scores
**Endpoint:** `GET /api/leads/{lead_id}/scores`

**Response JSON:**
```json
{
  "items": [
    {
      "id": "77777777-7777-4777-8777-777777777777",
      "lead_id": "55555555-5555-4555-8555-555555555555",
      "score": 85,
      "model": "predictive_v2",
      "factors": {
        "profile_fit": 25,
        "engagement": 30
      },
      "calculated_at": "2026-01-15T10:30:00"
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 20
}
```

---

### 6.10 Create Qualification Framework
**Endpoint:** `POST /api/qualification-frameworks`

**Purpose:** Create lead qualification criteria.

**Request JSON:**
```json
{
  "name": "Enterprise Qualification",
  "description": "Framework for qualifying enterprise leads",
  "criteria": [
    {
      "name": "company_size",
      "weight": 25,
      "options": {
        "50-200": 20,
        "200-1000": 25,
        "1000+": 25
      }
    },
    {
      "name": "budget",
      "weight": 35,
      "options": {
        "under_5k": 10,
        "5k-20k": 20,
        "20k+": 35
      }
    }
  ],
  "passing_score": 60
}
```

**Response JSON:**
```json
{
  "id": "88888888-8888-4888-8888-888888888888",
  "name": "Enterprise Qualification",
  "description": "Framework for qualifying enterprise leads",
  "criteria": [
    {
      "name": "company_size",
      "weight": 25
    }
  ],
  "passing_score": 60,
  "created_at": "2026-01-15T10:30:00"
}
```

---

### 6.11 List Qualification Frameworks
**Endpoint:** `GET /api/qualification-frameworks`

**Response JSON:**
```json
{
  "items": [
    {
      "id": "88888888-8888-4888-8888-888888888888",
      "name": "Enterprise Qualification",
      "passing_score": 60,
      "created_at": "2026-01-15T10:30:00"
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 20
}
```

---

### 6.12 Start Qualification
**Endpoint:** `POST /api/leads/{lead_id}/qualifications`

**Purpose:** Begin lead qualification process.

**Request JSON:**
```json
{
  "framework_id": "88888888-8888-4888-8888-888888888888",
  "answers": {
    "company_size": "200-1000",
    "budget": "20k+",
    "timeline": "Q1-2026",
    "decision_maker": "yes"
  },
  "notes": "Very interested, wants demo next week",
  "qualified_by": "55555555-5555-4555-8555-555555555555"
}
```

**Response JSON:**
```json
{
  "id": "99999999-9999-4999-8999-999999999999",
  "lead_id": "55555555-5555-4555-8555-555555555555",
  "framework_id": "88888888-8888-4888-8888-888888888888",
  "score": 75,
  "answers": {
    "company_size": "200-1000",
    "budget": "20k+"
  },
  "notes": "Very interested, wants demo next week",
  "qualified_by": "55555555-5555-4555-8555-555555555555",
  "created_at": "2026-01-15T10:30:00"
}
```

---

### 6.13 List Lead Qualifications
**Endpoint:** `GET /api/leads/{lead_id}/qualifications`

**Response JSON:**
```json
{
  "items": [
    {
      "id": "99999999-9999-4999-8999-999999999999",
      "lead_id": "55555555-5555-4555-8555-555555555555",
      "framework_id": "88888888-8888-4888-8888-888888888888",
      "score": 75,
      "created_at": "2026-01-15T10:30:00"
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 20
}
```

---

### 6.14 Create Opportunity
**Endpoint:** `POST /api/opportunities`

**Purpose:** Convert lead to opportunity.

**Request JSON:**
```json
{
  "lead_id": "55555555-5555-4555-8555-555555555555",
  "name": "TechCorp Enterprise Deal",
  "stage": "proposal",
  "amount": 15000,
  "currency": "USD",
  "probability": 70,
  "expected_close_date": "2026-02-15",
  "tenant_id": "22222222-2222-4222-8222-222222222222"
}
```

**Response JSON:**
```json
{
  "id": "aaaaaaaa-aaaa-4aaa-aaaa-aaaaaaaaaaaa",
  "lead_id": "55555555-5555-4555-8555-555555555555",
  "name": "TechCorp Enterprise Deal",
  "stage": "proposal",
  "amount": 15000,
  "currency": "USD",
  "probability": 70,
  "expected_close_date": "2026-02-15",
  "tenant_id": "22222222-2222-4222-8222-222222222222",
  "created_at": "2026-01-15T10:30:00",
  "updated_at": "2026-01-15T10:30:00"
}
```

---

### 6.15 List Opportunities
**Endpoint:** `GET /api/opportunities`

**Response JSON:**
```json
{
  "items": [
    {
      "id": "aaaaaaaa-aaaa-4aaa-aaaa-aaaaaaaaaaaa",
      "name": "TechCorp Enterprise Deal",
      "stage": "proposal",
      "amount": 15000,
      "probability": 70,
      "created_at": "2026-01-15T10:30:00"
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 20
}
```

---

### 6.16 Get Opportunity
**Endpoint:** `GET /api/opportunities/{opportunity_id}`

**Response JSON:**
```json
{
  "id": "aaaaaaaa-aaaa-4aaa-aaaa-aaaaaaaaaaaa",
  "lead_id": "55555555-5555-4555-8555-555555555555",
  "name": "TechCorp Enterprise Deal",
  "stage": "proposal",
  "amount": 15000,
  "currency": "USD",
  "probability": 70,
  "expected_close_date": "2026-02-15",
  "tenant_id": "22222222-2222-4222-8222-222222222222",
  "created_at": "2026-01-15T10:30:00",
  "updated_at": "2026-01-15T10:30:00"
}
```

---

### 6.17 Update Opportunity
**Endpoint:** `PATCH /api/opportunities/{opportunity_id}`

**Request JSON:**
```json
{
  "stage": "negotiation",
  "probability": 85,
  "amount": 18000
}
```

**Response JSON:** Updated opportunity object

---

### 6.18 Create Proposal
**Endpoint:** `POST /api/opportunities/{opportunity_id}/proposals`

**Purpose:** Generate proposal for opportunity.

**Request JSON:**
```json
{
  "title": "Enterprise Plan Proposal - TechCorp",
  "content": "Dear Asha, We are pleased to present...",
  "pricing": {
    "plan": "enterprise",
    "users": 50,
    "monthly_price": 999,
    "annual_discount": 20
  },
  "valid_until": "2026-02-15",
  "created_by": "55555555-5555-4555-8555-555555555555"
}
```

**Response JSON:**
```json
{
  "id": "bbbbbbbb-bbbb-4bbb-bbbb-bbbbbbbbbbbb",
  "opportunity_id": "aaaaaaaa-aaaa-4aaa-aaaa-aaaaaaaaaaaa",
  "document_id": "cccccccc-cccc-4ccc-cccc-cccccccccccc",
  "status": "draft",
  "title": "Enterprise Plan Proposal - TechCorp",
  "pricing": {
    "plan": "enterprise",
    "monthly_price": 999
  },
  "created_at": "2026-01-15T10:30:00"
}
```

---

### 6.19 Create Quote
**Endpoint:** `POST /api/opportunities/{opportunity_id}/quotes`

**Purpose:** Generate quote for opportunity.

**Request JSON:**
```json
{
  "items": [
    {
      "product": "Enterprise Plan",
      "quantity": 50,
      "unit_price": 20,
      "discount_percent": 20
    },
    {
      "product": "Premium Support",
      "quantity": 1,
      "unit_price": 500,
      "discount_percent": 0
    }
  ],
  "valid_days": 30,
  "notes": "Includes 20% annual discount"
}
```

**Response JSON:**
```json
{
  "id": "dddddddd-dddd-4ddd-dddd-dddddddddddd",
  "opportunity_id": "aaaaaaaa-aaaa-4aaa-aaaa-aaaaaaaaaaaa",
  "status": "draft",
  "items": [
    {
      "product": "Enterprise Plan",
      "quantity": 50,
      "unit_price": 20,
      "discount_percent": 20
    }
  ],
  "total": 15000,
  "created_at": "2026-01-15T10:30:00"
}
```

---

### 6.20 Create Meeting
**Endpoint:** `POST /api/meetings`

**Purpose:** Schedule a meeting.

**Request JSON:**
```json
{
  "lead_id": "55555555-5555-4555-8555-555555555555",
  "opportunity_id": "aaaaaaaa-aaaa-4aaa-aaaa-aaaaaaaaaaaa",
  "title": "Enterprise Demo - TechCorp",
  "type": "demo",
  "scheduled_at": "2026-01-20T14:00:00",
  "duration_minutes": 60,
  "attendees": [
    "asha.kumar@techcorp.com",
    "sales@acme.com"
  ],
  "location": "Zoom",
  "notes": "Focus on enterprise features and pricing"
}
```

**Response JSON:**
```json
{
  "id": "eeeeeeee-eeee-4eee-eeee-eeeeeeeeeeee",
  "lead_id": "55555555-5555-4555-8555-555555555555",
  "opportunity_id": "aaaaaaaa-aaaa-4aaa-aaaa-aaaaaaaaaaaa",
  "title": "Enterprise Demo - TechCorp",
  "type": "demo",
  "status": "scheduled",
  "scheduled_at": "2026-01-20T14:00:00",
  "duration_minutes": 60,
  "attendees": [
    "asha.kumar@techcorp.com",
    "sales@acme.com"
  ],
  "location": "Zoom",
  "notes": "Focus on enterprise features",
  "created_at": "2026-01-15T10:30:00",
  "updated_at": "2026-01-15T10:30:00"
}
```

---

### 6.21 List Meetings
**Endpoint:** `GET /api/meetings`

**Response JSON:**
```json
{
  "items": [
    {
      "id": "eeeeeeee-eeee-4eee-eeee-eeeeeeeeeeee",
      "title": "Enterprise Demo - TechCorp",
      "type": "demo",
      "status": "scheduled",
      "scheduled_at": "2026-01-20T14:00:00",
      "created_at": "2026-01-15T10:30:00"
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 20
}
```

---

### 6.22 Update Meeting
**Endpoint:** `PATCH /api/meetings/{meeting_id}`

**Request JSON:**
```json
{
  "status": "confirmed",
  "scheduled_at": "2026-01-20T15:00:00",
  "notes": "Confirmed with customer, added second attendee"
}
```

**Response JSON:** Updated meeting object

---

### 6.23 Delete/Cancel Meeting
**Endpoint:** `DELETE /api/meetings/{meeting_id}`

**Response:** `204 No Content`

---

## Domain 7 - Customers & Customer Success

### 7.1 Create Customer
**Endpoint:** `POST /api/customers`

**Purpose:** Create a new customer (converted from lead).

**Request JSON:**
```json
{
  "name": "TechCorp Inc",
  "email": "billing@techcorp.com",
  "phone": "+1-555-0100",
  "tenant_id": "22222222-2222-4222-8222-222222222222",
  "status": "active",
  "plan_id": "33333333-3333-4333-8333-333333333333",
  "mrr": 999,
  "arr": 11988,
  "industry": "Technology",
  "company_size": "50-200",
  "billing_address": {
    "street": "123 Tech Street",
    "city": "San Francisco",
    "state": "CA",
    "zip": "94105",
    "country": "USA"
  },
  "custom_fields": {
    "tax_id": "12-3456789",
    "payment_method": "credit_card"
  }
}
```

**Response JSON:**
```json
{
  "id": "ffffffff-ffff-4fff-ffff-ffffffffffff",
  "name": "TechCorp Inc",
  "email": "billing@techcorp.com",
  "phone": "+1-555-0100",
  "tenant_id": "22222222-2222-4222-8222-222222222222",
  "status": "active",
  "plan_id": "33333333-3333-4333-8333-333333333333",
  "mrr": 999,
  "arr": 11988,
  "industry": "Technology",
  "company_size": "50-200",
  "billing_address": {
    "street": "123 Tech Street",
    "city": "San Francisco"
  },
  "health_score": 0,
  "churn_risk": "unknown",
  "expansion_score": 0,
  "contacts": [],
  "conversations": [],
  "events": [],
  "created_at": "2026-01-15T10:30:00",
  "updated_at": "2026-01-15T10:30:00"
}
```

---

### 7.2 List Customers
**Endpoint:** `GET /api/customers`

**Query Parameters:**
- `tenant_id` (optional)
- `status` (optional)
- `plan_id` (optional)
- `page` (default: 1)
- `page_size` (default: 20)

**Response JSON:**
```json
{
  "items": [
    {
      "id": "ffffffff-ffff-4fff-ffff-ffffffffffff",
      "name": "TechCorp Inc",
      "email": "billing@techcorp.com",
      "status": "active",
      "mrr": 999,
      "arr": 11988,
      "health_score": 0,
      "created_at": "2026-01-15T10:30:00"
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 20
}
```

---

### 7.3 Get Customer
**Endpoint:** `GET /api/customers/{customer_id}`

**Response JSON:**
```json
{
  "id": "ffffffff-ffff-4fff-ffff-ffffffffffff",
  "name": "TechCorp Inc",
  "email": "billing@techcorp.com",
  "phone": "+1-555-0100",
  "tenant_id": "22222222-2222-4222-8222-222222222222",
  "status": "active",
  "plan_id": "33333333-3333-4333-8333-333333333333",
  "mrr": 999,
  "arr": 11988,
  "industry": "Technology",
  "company_size": "50-200",
  "billing_address": {
    "street": "123 Tech Street",
    "city": "San Francisco",
    "state": "CA",
    "zip": "94105"
  },
  "health_score": 0,
  "churn_risk": "unknown",
  "expansion_score": 0,
  "contacts": [],
  "conversations": [],
  "events": [],
  "created_at": "2026-01-15T10:30:00",
  "updated_at": "2026-01-15T10:30:00"
}
```

---

### 7.4 Update Customer
**Endpoint:** `PATCH /api/customers/{customer_id}`

**Request JSON:**
```json
{
  "status": "active",
  "mrr": 1200,
  "arr": 14400,
  "custom_fields": {
    "tax_id": "12-3456789",
    "renewal_date": "2027-01-15"
  }
}
```

**Response JSON:** Updated customer object

---

### 7.5 Delete Customer
**Endpoint:** `DELETE /api/customers/{customer_id}`

**Response:** `204 No Content`

---

### 7.6 Add Contact
**Endpoint:** `POST /api/customers/{customer_id}/contacts`

**Purpose:** Add contact person for customer.

**Request JSON:**
```json
{
  "name": "Asha Kumar",
  "email": "asha@techcorp.com",
  "phone": "+1-555-0101",
  "role": "primary_contact",
  "is_primary": true,
  "metadata": {
    "department": "Engineering",
    "decision_maker": true
  }
}
```

**Response JSON:**
```json
{
  "id": "11111111-1111-4111-8111-111111111111",
  "customer_id": "ffffffff-ffff-4fff-ffff-ffffffffffff",
  "name": "Asha Kumar",
  "email": "asha@techcorp.com",
  "phone": "+1-555-0101",
  "role": "primary_contact",
  "is_primary": true,
  "metadata": {
    "department": "Engineering"
  },
  "created_at": "2026-01-15T10:30:00"
}
```

---

### 7.7 List Customer Contacts
**Endpoint:** `GET /api/customers/{customer_id}/contacts`

**Response JSON:**
```json
{
  "items": [
    {
      "id": "11111111-1111-4111-8111-111111111111",
      "customer_id": "ffffffff-ffff-4fff-ffff-ffffffffffff",
      "name": "Asha Kumar",
      "email": "asha@techcorp.com",
      "role": "primary_contact",
      "is_primary": true,
      "created_at": "2026-01-15T10:30:00"
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 20
}
```

---

### 7.8 Calculate Health Score
**Endpoint:** `POST /api/customers/{customer_id}/health-scores`

**Purpose:** Compute customer health score.

**Request JSON:**
```json
{
  "model": "health_v2",
  "force_recalculate": true,
  "metadata": {
    "factors_considered": ["usage", "support", "payment", "engagement"]
  }
}
```

**Response JSON:**
```json
{
  "id": "22222222-2222-4222-8222-222222222222",
  "customer_id": "ffffffff-ffff-4fff-ffff-ffffffffffff",
  "score": 88,
  "model": "health_v2",
  "factors": {
    "usage": 30,
    "support": 20,
    "payment": 20,
    "engagement": 18
  },
  "trend": "up",
  "metadata": {
    "factors_considered": ["usage", "support"]
  },
  "calculated_at": "2026-01-15T10:30:00"
}
```

---

### 7.9 List Health Scores
**Endpoint:** `GET /api/customers/{customer_id}/health-scores`

**Response JSON:**
```json
{
  "items": [
    {
      "id": "22222222-2222-4222-8222-222222222222",
      "customer_id": "ffffffff-ffff-4fff-ffff-ffffffffffff",
      "score": 88,
      "factors": {
        "usage": 30,
        "support": 20
      },
      "trend": "up",
      "calculated_at": "2026-01-15T10:30:00"
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 20
}
```

---

### 7.10 Log Customer Event
**Endpoint:** `POST /api/customers/{customer_id}/events`

**Purpose:** Track customer event.

**Request JSON:**
```json
{
  "type": "feature_used",
  "feature": "advanced_analytics",
  "timestamp": "2026-01-15T10:30:00",
  "metadata": {
    "session_id": "eeeeeeee-eeee-4eee-eeee-eeeeeeeeeeee",
    "duration_seconds": 120,
    "pages_viewed": 5
  }
}
```

**Response JSON:**
```json
{
  "id": "33333333-3333-4333-8333-333333333333",
  "customer_id": "ffffffff-ffff-4fff-ffff-ffffffffffff",
  "type": "feature_used",
  "feature": "advanced_analytics",
  "timestamp": "2026-01-15T10:30:00",
  "metadata": {
    "session_id": "eeeeeeee-eeee-4eee-eeee-eeeeeeeeeeee",
    "duration_seconds": 120
  },
  "created_at": "2026-01-15T10:30:00"
}
```

---

### 7.11 List Customer Events
**Endpoint:** `GET /api/customers/{customer_id}/events`

**Response JSON:**
```json
{
  "items": [
    {
      "id": "33333333-3333-4333-8333-333333333333",
      "customer_id": "ffffffff-ffff-4fff-ffff-ffffffffffff",
      "type": "feature_used",
      "feature": "advanced_analytics",
      "timestamp": "2026-01-15T10:30:00",
      "created_at": "2026-01-15T10:30:00"
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 20
}
```

---

### 7.12 Create Renewal
**Endpoint:** `POST /api/customers/{customer_id}/renewals`

**Purpose:** Create renewal opportunity.

**Request JSON:**
```json
{
  "renewal_date": "2027-01-15",
  "contract_value": 14400,
  "currency": "USD",
  "status": "upcoming",
  "assigned_to": "55555555-5555-4555-8555-555555555555",
  "metadata": {
    "current_plan": "enterprise",
    "proposed_plan": "enterprise_plus",
    "expansion_opportunity": true
  }
}
```

**Response JSON:**
```json
{
  "id": "44444444-4444-4444-8444-444444444444",
  "customer_id": "ffffffff-ffff-4fff-ffff-ffffffffffff",
  "renewal_date": "2027-01-15",
  "contract_value": 14400,
  "currency": "USD",
  "status": "upcoming",
  "actual_value": null,
  "closed_date": null,
  "created_at": "2026-01-15T10:30:00",
  "updated_at": "2026-01-15T10:30:00"
}
```

---

### 7.13 List Renewals
**Endpoint:** `GET /api/customers/{customer_id}/renewals`

**Response JSON:**
```json
{
  "items": [
    {
      "id": "44444444-4444-4444-8444-444444444444",
      "customer_id": "ffffffff-ffff-4fff-ffff-ffffffffffff",
      "renewal_date": "2027-01-15",
      "contract_value": 14400,
      "status": "upcoming",
      "created_at": "2026-01-15T10:30:00"
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 20
}
```

---

### 7.14 Update Renewal
**Endpoint:** `PATCH /api/renewals/{renewal_id}`

**Request JSON:**
```json
{
  "status": "won",
  "actual_value": 18000,
  "closed_date": "2027-01-10"
}
```

**Response JSON:** Updated renewal object

---

## Additional Domains

### Analytics & Observability

#### Create Event
**Endpoint:** `POST /api/events`

**Request JSON:**
```json
{
  "event_type": "page_view",
  "tenant_id": "22222222-2222-4222-8222-222222222222",
  "user_id": "55555555-5555-4555-8555-555555555555",
  "properties": {
    "page": "/pricing",
    "referrer": "google",
    "duration_seconds": 45
  },
  "timestamp": "2026-01-15T10:30:00"
}
```

**Response JSON:**
```json
{
  "id": "55555555-5555-4555-8555-555555555555",
  "event_type": "page_view",
  "tenant_id": "22222222-2222-4222-8222-222222222222",
  "properties": {
    "page": "/pricing",
    "referrer": "google"
  },
  "created_at": "2026-01-15T10:30:00"
}
```

---

#### Daily Metrics
**Endpoint:** `GET /api/analytics/daily`

**Query Parameters:**
- `tenant_id` (optional)
- `date` (default: today)

**Response JSON:**
```json
{
  "date": "2026-01-15",
  "tenant_id": "22222222-2222-4222-8222-222222222222",
  "conversations": 45,
  "messages": 320,
  "leads_created": 12,
  "leads_converted": 3,
  "api_calls": 15420,
  "tokens_used": 125000,
  "avg_response_time_ms": 1250,
  "cost_usd": 2.5
}
```

---

#### Monthly Metrics
**Endpoint:** `GET /api/analytics/monthly`

**Query Parameters:**
- `tenant_id` (optional)
- `year` (default: 2026)
- `month` (default: 6)

**Response JSON:**
```json
{
  "tenant_id": "22222222-2222-4222-8222-222222222222",
  "year": 2026,
  "month": 1,
  "metrics": {
    "conversations": 1250,
    "messages": 8500,
    "leads_created": 320,
    "revenue": 45000
  }
}
```

---

#### Model Usage
**Endpoint:** `GET /api/analytics/model-usage`

**Response JSON:**
```json
{
  "models": [
    {
      "model": "claude-3-5-sonnet-20240620",
      "requests": 15420,
      "tokens_in": 1250000,
      "tokens_out": 850000,
      "tokens": 2100000,
      "cost_usd": 45.5
    }
  ]
}
```

---

### Knowledge & RAG

#### Create Knowledge Source
**Endpoint:** `POST /api/knowledge/sources`

**Request JSON:**
```json
{
  "name": "Product Documentation",
  "type": "document_store",
  "tenant_id": "22222222-2222-4222-8222-222222222222",
  "config": {
    "url": "https://docs.acme.com",
    "crawl_frequency": "daily",
    "max_pages": 1000
  },
  "status": "active"
}
```

**Response JSON:**
```json
{
  "id": "66666666-6666-4666-8666-666666666666",
  "name": "Product Documentation",
  "type": "document_store",
  "tenant_id": "22222222-2222-4222-8222-222222222222",
  "config": {
    "url": "https://docs.acme.com",
    "crawl_frequency": "daily"
  },
  "status": "active",
  "document_count": 0,
  "total_chunks": 0,
  "created_at": "2026-01-15T10:30:00"
}
```

---

#### Search Knowledge
**Endpoint:** `POST /api/knowledge/search`

**Request JSON:**
```json
{
  "query": "enterprise pricing plans",
  "tenant_id": "22222222-2222-4222-8222-222222222222",
  "source_ids": [
    "66666666-6666-4666-8666-666666666666"
  ],
  "top_k": 5,
  "filters": {
    "document_types": ["pricing", "faq"],
    "tags": ["enterprise"]
  }
}
```

**Response JSON:**
```json
{
  "query": "enterprise pricing plans",
  "results": [
    {
      "chunk_id": "77777777-7777-4777-8777-777777777777",
      "document_id": "88888888-8888-4888-8888-888888888888",
      "document_name": "pricing_guide.pdf",
      "page": 5,
      "heading": "Enterprise Plans",
      "text": "Enterprise plan starts at $999/month for 50+ users...",
      "score": 0.95,
      "metadata": {
        "section": "pricing",
        "tags": ["enterprise", "pricing"]
      }
    }
  ],
  "total_results": 1,
  "latency_ms": 45
}
```

---

#### Create FAQ
**Endpoint:** `POST /api/faqs`

**Request JSON:**
```json
{
  "question": "What are your enterprise pricing plans?",
  "answer": "Enterprise plan starts at $999/month for 50+ users, includes unlimited conversations, priority support, and custom integrations.",
  "tenant_id": "22222222-2222-4222-8222-222222222222",
  "category": "pricing",
  "tags": ["enterprise", "pricing", "plans"],
  "source_document_id": "88888888-8888-4888-8888-888888888888"
}
```

**Response JSON:**
```json
{
  "id": "99999999-9999-4999-8999-999999999999",
  "question": "What are your enterprise pricing plans?",
  "answer": "Enterprise plan starts at $999/month for 50+ users...",
  "category": "pricing",
  "tags": ["enterprise", "pricing"],
  "created_at": "2026-01-15T10:30:00"
}
```

---

### Integrations

#### List Integrations
**Endpoint:** `GET /api/integrations`

**Response JSON:**
```json
{
  "items": [
    {
      "id": "11111111-1111-4111-8111-111111111111",
      "name": "Salesforce",
      "category": "crm",
      "auth_type": "oauth2",
      "status": "available"
    },
    {
      "id": "22222222-2222-4222-8222-222222222222",
      "name": "HubSpot",
      "category": "crm",
      "auth_type": "api_key",
      "status": "available"
    }
  ],
  "total": 2,
  "page": 1,
  "page_size": 20
}
```

---

#### Create Integration Connection
**Endpoint:** `POST /api/integration-connections`

**Request JSON:**
```json
{
  "integration_id": "11111111-1111-4111-8111-111111111111",
  "tenant_id": "22222222-2222-4222-8222-222222222222",
  "auth_type": "oauth2",
  "settings": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "instance_url": "https://acme.my.salesforce.com"
  }
}
```

**Response JSON:**
```json
{
  "id": "33333333-3333-4333-8333-333333333333",
  "integration_id": "11111111-1111-4111-8111-111111111111",
  "integration_name": "Salesforce",
  "tenant_id": "22222222-2222-4222-8222-222222222222",
  "status": "connected",
  "connected_at": "2026-01-15T10:30:00",
  "last_sync": null
}
```

---

#### Trigger Sync
**Endpoint:** `POST /api/integration-connections/{connection_id}/sync`

**Request JSON:**
```json
{
  "sync_type": "full",
  "entities": ["leads", "contacts", "opportunities"]
}
```

**Response JSON:**
```json
{
  "id": "44444444-4444-4444-8444-444444444444",
  "job_id": "44444444-4444-4444-8444-444444444444",
  "connection_id": "33333333-3333-4333-8333-333333333333",
  "status": "queued",
  "sync_type": "full",
  "entities": ["leads", "contacts", "opportunities"],
  "records_synced": 0,
  "started_at": "2026-01-15T10:30:00",
  "completed_at": null
}
```

---

### Billing

#### Create Plan
**Endpoint:** `POST /api/plans`

**Request JSON:**
```json
{
  "name": "Enterprise",
  "description": "Enterprise plan for large organizations",
  "price": 999,
  "currency": "USD",
  "billing_period": "monthly",
  "features": [
    "unlimited_conversations",
    "priority_support",
    "custom_integrations",
    "advanced_analytics"
  ],
  "limits": {
    "users": 100,
    "api_calls_per_month": 100000,
    "storage_gb": 50
  }
}
```

**Response JSON:**
```json
{
  "id": "55555555-5555-4555-8555-555555555555",
  "name": "Enterprise",
  "description": "Enterprise plan for large organizations",
  "price": 999,
  "currency": "USD",
  "billing_period": "monthly",
  "features": [
    "unlimited_conversations",
    "priority_support"
  ],
  "limits": {
    "users": 100,
    "api_calls_per_month": 100000
  }
}
```

---

#### Create Subscription
**Endpoint:** `POST /api/subscriptions`

**Request JSON:**
```json
{
  "tenant_id": "22222222-2222-4222-8222-222222222222",
  "plan_id": "55555555-5555-4555-8555-555555555555",
  "customer_id": "ffffffff-ffff-4fff-ffff-ffffffffffff",
  "status": "active",
  "start_date": "2026-01-15",
  "billing_cycle": "monthly",
  "payment_method_id": "66666666-6666-4666-8666-666666666666"
}
```

**Response JSON:**
```json
{
  "id": "77777777-7777-4777-8777-777777777777",
  "plan": "Enterprise",
  "status": "active",
  "mrr": 999,
  "created_at": "2026-01-15T10:30:00"
}
```

---

#### Create Invoice
**Endpoint:** `POST /api/invoices`

**Request JSON:**
```json
{
  "subscription_id": "77777777-7777-4777-8777-777777777777",
  "tenant_id": "22222222-2222-4222-8222-222222222222",
  "items": [
    {
      "description": "Enterprise Plan - January 2026",
      "amount": 999,
      "quantity": 1
    },
    {
      "description": "Premium Support Add-on",
      "amount": 200,
      "quantity": 1
    }
  ],
  "due_date": "2026-01-30",
  "currency": "USD"
}
```

**Response JSON:**
```json
{
  "id": "88888888-8888-4888-8888-888888888888",
  "amount": 1199,
  "status": "draft",
  "due_date": "2026-01-30",
  "currency": "USD",
  "items": [
    {
      "description": "Enterprise Plan - January 2026",
      "amount": 999,
      "quantity": 1
    }
  ]
}
```

---

#### Create Payment
**Endpoint:** `POST /api/payments`

**Request JSON:**
```json
{
  "invoice_id": "88888888-8888-4888-8888-888888888888",
  "amount": 1199,
  "currency": "USD",
  "method": "stripe",
  "stripe_payment_intent_id": "pi_1234567890"
}
```

**Response JSON:**
```json
{
  "id": "99999999-9999-4999-8999-999999999999",
  "amount": 1199,
  "status": "succeeded",
  "method": "stripe",
  "created_at": "2026-01-15T10:30:00"
}
```

---

#### Get Credits
**Endpoint:** `GET /api/credits`

**Response JSON:**
```json
{
  "tenant_id": "22222222-2222-4222-8222-222222222222",
  "balance": 500,
  "currency": "USD",
  "last_updated": "2026-01-15T10:30:00"
}
```

---

#### Create Credit Transaction
**Endpoint:** `POST /api/credits/transactions`

**Request JSON:**
```json
{
  "type": "purchase",
  "amount": 100,
  "currency": "USD",
  "description": "Credit purchase - 100 USD"
}
```

**Response JSON:**
```json
{
  "id": "11111111-1111-4111-8111-111111111111",
  "type": "purchase",
  "amount": 100,
  "currency": "USD",
  "balance_after": 600,
  "description": "Credit purchase - 100 USD"
}
```

---

### Documents

#### Create Document
**Endpoint:** `POST /api/documents`

**Request JSON:**
```json
{
  "filename": "product_guide.pdf",
  "file_type": "pdf",
  "file_path": "/uploads/product_guide.pdf",
  "file_size": 245760,
  "tenant_id": "22222222-2222-4222-8222-222222222222",
  "source_id": "66666666-6666-4666-8666-666666666666",
  "metadata": {
    "author": "Product Team",
    "version": "2.0",
    "tags": ["product", "guide", "enterprise"]
  }
}
```

**Response JSON:**
```json
{
  "id": "22222222-2222-4222-8222-222222222222",
  "source_id": "66666666-6666-4666-8666-666666666666",
  "filename": "product_guide.pdf",
  "file_type": "pdf",
  "status": "pending",
  "total_pages": 0,
  "total_chunks": 0,
  "tenant_id": "22222222-2222-4222-8222-222222222222",
  "created_at": "2026-01-15T10:30:00"
}
```

---

#### List Documents
**Endpoint:** `GET /api/documents`

**Response JSON:**
```json
{
  "items": [
    {
      "id": "22222222-2222-4222-8222-222222222222",
      "filename": "product_guide.pdf",
      "status": "indexed",
      "total_chunks": 25,
      "created_at": "2026-01-15T10:30:00"
    }
  ]
}
```

---

#### Get Document
**Endpoint:** `GET /api/documents/{document_id}`

**Response JSON:**
```json
{
  "id": "22222222-2222-4222-8222-222222222222",
  "source_id": "66666666-6666-4666-8666-666666666666",
  "filename": "product_guide.pdf",
  "file_type": "pdf",
  "status": "indexed",
  "total_pages": 10,
  "total_chunks": 25,
  "tenant_id": "22222222-2222-4222-8222-222222222222",
  "summary": "Comprehensive product guide covering enterprise features...",
  "keywords": ["enterprise", "pricing", "features", "support"],
  "metadata": {
    "author": "Product Team",
    "version": "2.0"
  },
  "chunks": [
    {
      "id": "33333333-3333-4333-8333-333333333333",
      "index": 0,
      "page": 1,
      "heading": "Introduction"
    }
  ],
  "indexed_at": "2026-01-15T10:30:15",
  "created_at": "2026-01-15T10:30:00"
}
```

---

#### Create Document Chunks
**Endpoint:** `POST /api/documents/{document_id}/chunks`

**Request JSON:**
```json
{
  "chunks": [
    {
      "index": 0,
      "text": "Enterprise plan starts at $999/month for 50+ users...",
      "page": 5,
      "section": "Pricing",
      "heading": "Enterprise Plans",
      "tags": ["pricing", "enterprise"],
      "embedding_hash": "abc123",
      "vector_id": "vec_123"
    },
    {
      "index": 1,
      "text": "Premium support includes 24/7 availability...",
      "page": 5,
      "section": "Support",
      "heading": "Premium Support"
    }
  ]
}
```

**Response JSON:**
```json
{
  "document_id": "22222222-2222-4222-8222-222222222222",
  "chunks_created": 2,
  "chunks": [
    {
      "id": "44444444-4444-4444-8444-444444444444",
      "index": 0,
      "page": 5
    },
    {
      "id": "55555555-5555-4555-8555-555555555555",
      "index": 1,
      "page": 5
    }
  ]
}
```

---

### Tools & MCP

#### Create Tool
**Endpoint:** `POST /api/tools`

**Request JSON:**
```json
{
  "name": "search_knowledge",
  "display_name": "Search Knowledge Base",
  "description": "Search the knowledge base for relevant information",
  "category": "retrieval",
  "tenant_id": "22222222-2222-4222-8222-222222222222",
  "config": {
    "max_results": 5,
    "min_score": 0.7,
    "sources": ["documentation", "faqs"]
  }
}
```

**Response JSON:**
```json
{
  "id": "66666666-6666-4666-8666-666666666666",
  "name": "search_knowledge",
  "display_name": "Search Knowledge Base",
  "description": "Search the knowledge base for relevant information",
  "category": "retrieval",
  "tenant_id": "22222222-2222-4222-8222-222222222222",
  "executions_count": 0,
  "avg_latency_ms": 0,
  "success_rate": 1.0,
  "created_at": "2026-01-15T10:30:00"
}
```

---

#### Execute Tool
**Endpoint:** `POST /api/tools/{tool_id}/execute`

**Request JSON:**
```json
{
  "agent_id": "aaaaaaaa-aaaa-4aaa-aaaa-aaaaaaaaaaaa",
  "conversation_id": "eeeeeeee-eeee-4eee-eeee-eeeeeeeeeeee",
  "parameters": {
    "query": "enterprise pricing",
    "top_k": 5
  }
}
```

**Response JSON:**
```json
{
  "id": "77777777-7777-4777-8777-777777777777",
  "tool_id": "66666666-6666-4666-8666-666666666666",
  "tool_name": "search_knowledge",
  "agent_id": "aaaaaaaa-aaaa-4aaa-aaaa-aaaaaaaaaaaa",
  "conversation_id": "eeeeeeee-eeee-4eee-eeee-eeeeeeeeeeee",
  "status": "success",
  "result": {
    "contacts": [
      {
        "id": "88888888-8888-4888-8888-888888888888",
        "name": "Jane Lead",
        "company": "Acme Corp",
        "email": "jane@acme.com"
      }
    ]
  },
  "latency_ms": 125,
  "tokens_used": 0,
  "created_at": "2026-01-15T10:30:00"
}
```

---

### Database CRUD

#### List Tables
**Endpoint:** `GET /database/tables`

**Response JSON:**
```json
{
  "count": 25,
  "tables": [
    "agents",
    "conversations",
    "conversation_messages",
    "customers",
    "documents",
    "leads",
    "opportunities",
    "tenants",
    "users"
  ]
}
```

---

#### Get Table Schema
**Endpoint:** `GET /database/{table_name}/schema`

**Response JSON:**
```json
{
  "table": "leads",
  "columns": [
    {
      "name": "id",
      "type": "UUID",
      "nullable": false,
      "primary_key": true,
      "default": null
    },
    {
      "name": "email",
      "type": "VARCHAR(255)",
      "nullable": false,
      "primary_key": false,
      "default": null
    },
    {
      "name": "created_at",
      "type": "TIMESTAMP",
      "nullable": false,
      "primary_key": false,
      "default": null
    }
  ]
}
```

---

#### List Records
**Endpoint:** `GET /database/{table_name}/records`

**Query Parameters:**
- `limit` (default: 50, max: 500)
- `offset` (default: 0)

**Response JSON:**
```json
{
  "table": "leads",
  "limit": 50,
  "offset": 0,
  "records": [
    {
      "id": "55555555-5555-4555-8555-555555555555",
      "email": "asha.kumar@techcorp.com",
      "full_name": "Asha Kumar",
      "status": "new",
      "created_at": "2026-01-15T10:30:00"
    }
  ]
}
```

---

#### Create Record
**Endpoint:** `POST /database/{table_name}/records`

**Request JSON:**
```json
{
  "data": {
    "email": "new.lead@example.com",
    "full_name": "New Lead",
    "company": "Example Corp",
    "status": "new",
    "tenant_id": "22222222-2222-4222-8222-222222222222"
  }
}
```

**Response JSON:**
```json
{
  "table": "leads",
  "record": {
    "id": "99999999-9999-4999-8999-999999999999",
    "email": "new.lead@example.com",
    "full_name": "New Lead",
    "company": "Example Corp",
    "status": "new",
    "tenant_id": "22222222-2222-4222-8222-222222222222",
    "created_at": "2026-01-15T10:30:00"
  }
}
```

---

#### Update Record
**Endpoint:** `PATCH /database/{table_name}/records/{record_id}`

**Request JSON:**
```json
{
  "data": {
    "status": "qualified",
    "score": 85
  }
}
```

**Response JSON:**
```json
{
  "table": "leads",
  "record": {
    "id": "99999999-9999-4999-8999-999999999999",
    "email": "new.lead@example.com",
    "status": "qualified",
    "score": 85,
    "updated_at": "2026-01-15T10:35:00"
  }
}
```

---

#### Delete Record
**Endpoint:** `DELETE /database/{table_name}/records/{record_id}`

**Response JSON:**
```json
{
  "table": "leads",
  "deleted_id": "99999999-9999-4999-8999-999999999999"
}
```

---

## Common Workflow Patterns

### 1. Lead to Customer Conversion Flow

```json
// Step 1: Create Lead
POST /api/leads
{
  "email": "lead@example.com",
  "full_name": "John Doe",
  "company": "Acme Corp",
  "status": "new"
}

// Step 2: Qualify Lead
POST /api/leads/{lead_id}/qualifications
{
  "framework_id": "...",
  "answers": {...}
}

// Step 3: Create Opportunity
POST /api/opportunities
{
  "lead_id": "{lead_id}",
  "name": "Acme Deal",
  "stage": "proposal"
}

// Step 4: Create Customer (after deal won)
POST /api/customers
{
  "name": "Acme Corp",
  "email": "billing@acme.com",
  "mrr": 999
}
```

---

### 2. Conversation with RAG Flow

```json
// Step 1: Create Conversation
POST /api/conversations
{
  "type": "support",
  "customer_id": "{customer_id}",
  "agent_id": "{agent_id}"
}

// Step 2: Send User Message
POST /api/conversations/{conv_id}/messages
{
  "content": "How do I reset my password?",
  "role": "user"
}

// Step 3: AI Responds with RAG
POST /api/conversations/{conv_id}/messages
{
  "content": "To reset your password...",
  "role": "assistant",
  "citations": [...],
  "confidence": 0.92
}

// Step 4: Log Intent
POST /api/conversations/{conv_id}/intents
{
  "intent": "password_reset",
  "confidence": 0.95
}
```

---

### 3. Agent Chat Flow

```json
// Step 1: Create Agent
POST /api/v1/agents
{
  "name": "Support Bot",
  "type": "support",
  "config": {...}
}

// Step 2: Start Session
POST /api/v1/agents/{agent_id}/sessions
{
  "user_id": "{user_id}"
}

// Step 3: Chat
POST /api/v1/agents/{agent_id}/chat
{
  "message": "I need help",
  "session_id": "{session_id}",
  "context": {...}
}

// Step 4: Submit Feedback
POST /api/v1/agents/{agent_id}/feedback
{
  "rating": 5,
  "message_id": "{message_id}"
}
```

---

## Error Responses

All endpoints return standard HTTP error codes:

**400 Bad Request:**
```json
{
  "detail": "Invalid input data"
}
```

**401 Unauthorized:**
```json
{
  "detail": "Missing bearer token"
}
```

**403 Forbidden:**
```json
{
  "detail": "Tenant mismatch"
}
```

**404 Not Found:**
```json
{
  "detail": "Resource not found"
}
```

**409 Conflict:**
```json
{
  "detail": "Email already exists"
}
```

**422 Validation Error:**
```json
{
  "detail": [
    {
      "loc": ["body", "email"],
      "msg": "value is not a valid email address",
      "type": "value_error"
    }
  ]
}
```

**500 Internal Server Error:**
```json
{
  "detail": "Error communicating with Claude API: ..."
}
```

---

## Authentication

All protected endpoints require Bearer token:

```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

Token obtained from:
- `POST /auth/login`
- `POST /auth/register`
- `POST /api/v1/auth/login`
- `POST /api/v1/auth/register`

---

## Notes

1. **UUIDs**: All IDs are UUIDs (36-character strings with hyphens)
2. **Timestamps**: ISO 8601 format with timezone (UTC)
3. **Pagination**: Most list endpoints support `page` and `page_size`
4. **Tenant Isolation**: All data is scoped to tenant_id
5. **Soft Deletes**: Some entities use status='inactive' instead of hard delete
6. **In-Memory Storage**: Some endpoints use in-memory dictionaries (conversations, leads, etc.) for development
7. **Database Storage**: Other endpoints use PostgreSQL (tenants, users, agents, documents, etc.)

---

## Summary

This API provides comprehensive functionality for:
- **Multi-tenant SaaS platform** with role-based access
- **AI Agents** with chat, sessions, tasks, and memory
- **Conversations & Messages** with RAG support
- **Lead & Revenue Management** with qualification frameworks
- **Customer Success** with health scores and renewals
- **Knowledge Management** with RAG search
- **Integrations** with CRM and messaging platforms
- **Analytics & Observability** with metrics and logging
- **Billing** with plans, subscriptions, and invoices

Total: **143 endpoints** across **7 domains** with **230 operations**.