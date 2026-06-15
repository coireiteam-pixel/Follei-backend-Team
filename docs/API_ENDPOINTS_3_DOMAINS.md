# API Endpoints Added For 3 Domains

This document lists the API methods added from the provided endpoint reference.

## Domain 5: Conversations & Messages

| Method | Endpoint | Purpose |
| --- | --- | --- |
| POST | `/api/conversations` | Create conversation |
| GET | `/api/conversations` | List conversations |
| GET | `/api/conversations/{conversation_id}` | Get conversation |
| PATCH | `/api/conversations/{conversation_id}` | Update conversation |
| DELETE | `/api/conversations/{conversation_id}` | Archive conversation |
| POST | `/api/conversations/{conversation_id}/participants` | Add participant |
| GET | `/api/conversations/{conversation_id}/participants` | List participants |
| DELETE | `/api/conversations/{conversation_id}/participants/{participant_id}` | Remove participant |
| POST | `/api/conversations/{conversation_id}/messages` | Save user/agent/RAG message |
| GET | `/api/conversations/{conversation_id}/messages` | List conversation messages |
| GET | `/api/messages/{message_id}` | Get single message |
| PATCH | `/api/messages/{message_id}` | Edit message |
| DELETE | `/api/messages/{message_id}` | Delete message |
| POST | `/api/messages/{message_id}/attachments` | Add attachment |
| GET | `/api/messages/{message_id}/attachments` | List attachments |
| POST | `/api/messages/{message_id}/reactions` | React to message |
| POST | `/api/conversations/{conversation_id}/summaries` | Generate summary |
| GET | `/api/conversations/{conversation_id}/summaries` | List summaries |
| GET | `/api/conversations/{conversation_id}/metrics` | Conversation metrics |
| POST | `/api/conversations/{conversation_id}/intents` | Log intent |
| POST | `/api/conversations/{conversation_id}/sentiments` | Log sentiment |
| POST | `/api/conversations/{conversation_id}/emotions` | Log emotion |
| POST | `/api/conversations/{conversation_id}/objections` | Log objection |
| POST | `/api/conversations/{conversation_id}/buying-signals` | Log buying signal |

## Domain 6: Leads & Revenue

| Method | Endpoint | Purpose |
| --- | --- | --- |
| POST | `/api/leads` | Create lead |
| GET | `/api/leads` | List leads |
| GET | `/api/leads/{lead_id}` | Get lead |
| PATCH | `/api/leads/{lead_id}` | Update lead |
| DELETE | `/api/leads/{lead_id}` | Delete lead |
| POST | `/api/leads/{lead_id}/activities` | Log lead activity |
| GET | `/api/leads/{lead_id}/activities` | List lead activities |
| POST | `/api/leads/{lead_id}/scores` | Compute/update lead score |
| GET | `/api/leads/{lead_id}/scores` | Lead score history |
| POST | `/api/qualification-frameworks` | Create qualification framework |
| GET | `/api/qualification-frameworks` | List qualification frameworks |
| POST | `/api/leads/{lead_id}/qualifications` | Start qualification |
| GET | `/api/leads/{lead_id}/qualifications` | List lead qualifications |
| POST | `/api/opportunities` | Create opportunity |
| GET | `/api/opportunities` | List opportunities |
| GET | `/api/opportunities/{opportunity_id}` | Get opportunity |
| PATCH | `/api/opportunities/{opportunity_id}` | Update opportunity |
| POST | `/api/opportunities/{opportunity_id}/proposals` | Generate proposal |
| POST | `/api/opportunities/{opportunity_id}/quotes` | Create quote |
| POST | `/api/meetings` | Book meeting |
| GET | `/api/meetings` | List meetings |
| PATCH | `/api/meetings/{meeting_id}` | Update meeting |
| DELETE | `/api/meetings/{meeting_id}` | Cancel meeting |

## Domain 7: Customers & Customer Success

| Method | Endpoint | Purpose |
| --- | --- | --- |
| POST | `/api/customers` | Create customer |
| GET | `/api/customers` | List customers |
| GET | `/api/customers/{customer_id}` | Get customer |
| PATCH | `/api/customers/{customer_id}` | Update customer |
| DELETE | `/api/customers/{customer_id}` | Delete customer |
| POST | `/api/customers/{customer_id}/contacts` | Add contact |
| GET | `/api/customers/{customer_id}/contacts` | List contacts |
| POST | `/api/customers/{customer_id}/health-scores` | Compute health score |
| GET | `/api/customers/{customer_id}/health-scores` | Health score history |
| POST | `/api/customers/{customer_id}/events` | Log customer event |
| GET | `/api/customers/{customer_id}/events` | List customer events |
| POST | `/api/customers/{customer_id}/renewals` | Create renewal |
| GET | `/api/customers/{customer_id}/renewals` | List renewals |
| PATCH | `/api/renewals/{renewal_id}` | Update renewal |

## Implementation Notes

- These endpoints are now visible in Swagger at `/docs`.
- Conversation/message, lead, and customer core endpoints use existing SQLAlchemy models.
- Some workflow endpoints use structured in-memory responses until their full database models are added.
- The RAG handoff endpoint is:

```text
POST /api/conversations/{conversation_id}/messages
```

Use this endpoint to save assistant answers with citations, confidence, tool calls, and metadata.
