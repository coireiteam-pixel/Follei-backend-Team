# Follei P2/P3 API Examples

Run from `follei_backend/follei`:

```powershell
uvicorn app.main:app --reload
```

Swagger: `http://127.0.0.1:8000/docs`

Create P1 parent records first, then copy returned IDs into P2/P3 routes.

## Conversations & Messages

`PATCH /api/messages/{message_id}`

```json
{ "content": "Updated answer text", "status": "edited", "metadata": { "edited_by": "agent" } }
```

`POST /api/messages/{message_id}/attachments`

```json
{ "filename": "pricing.pdf", "url": "https://example.com/files/pricing.pdf", "mime_type": "application/pdf", "size_bytes": 204800, "caption": "Pricing document", "metadata": { "source": "upload" } }
```

`POST /api/messages/{message_id}/reactions`

```json
{ "emoji": "like", "user_id": "55555555-5555-4555-8555-555555555555", "metadata": { "source": "swagger" } }
```

`POST /api/conversations/{conversation_id}/summaries`

```json
{ "max_length": 200, "focus": "sales next steps", "metadata": { "generated_by": "ai" } }
```

`POST /api/conversations/{conversation_id}/intents`

```json
{ "message_id": "88888888-8888-4888-8888-888888888888", "intent": "pricing_question", "confidence": 0.87, "entities": [{ "type": "plan", "value": "pro" }], "metadata": {} }
```

`POST /api/conversations/{conversation_id}/sentiments`

```json
{ "message_id": "88888888-8888-4888-8888-888888888888", "sentiment": "positive", "score": 0.76, "aspects": [{ "topic": "pricing", "sentiment": "neutral" }], "metadata": {} }
```

`POST /api/conversations/{conversation_id}/emotions`

```json
{ "message_id": "88888888-8888-4888-8888-888888888888", "emotion": "curious", "intensity": 0.64, "metadata": {} }
```

`POST /api/conversations/{conversation_id}/objections`

```json
{ "message_id": "88888888-8888-4888-8888-888888888888", "objection_type": "price", "description": "Customer thinks the plan is expensive", "severity": "medium", "metadata": {} }
```

`POST /api/conversations/{conversation_id}/buying-signals`

```json
{ "message_id": "88888888-8888-4888-8888-888888888888", "signal_type": "demo_requested", "description": "Customer asked for a product demo", "strength": 0.9, "metadata": {} }
```

## Leads & Revenue

`POST /api/leads/{lead_id}/activities`

```json
{ "type": "call", "description": "Discovery call completed", "outcome": "interested", "metadata": { "duration_minutes": 30 } }
```

`POST /api/leads/{lead_id}/scores`

```json
{ "model": "default", "force_recalculate": true, "metadata": { "reason": "new activity" } }
```

`POST /api/qualification-frameworks`

```json
{ "name": "BANT", "description": "Budget, Authority, Need, Timeline framework", "criteria": [{ "name": "budget", "weight": 25 }], "metadata": {} }
```

`POST /api/leads/{lead_id}/qualifications`

```json
{ "framework_id": "99999999-9999-4999-8999-999999999999", "answers": [{ "question": "Budget?", "answer": "Yes" }], "status": "completed", "metadata": {} }
```

`POST /api/opportunities`

```json
{ "lead_id": "22222222-2222-4222-8222-222222222222", "name": "Acme annual subscription", "value": 25000, "currency": "USD", "stage": "discovery", "probability": 0.65, "expected_close_date": "2026-07-30", "tenant_id": "11111111-1111-4111-8111-111111111111", "metadata": {} }
```

`PATCH /api/opportunities/{opportunity_id}`

```json
{ "name": "Acme annual expansion", "value": 30000, "stage": "negotiation", "probability": 0.75, "expected_close_date": "2026-08-15", "metadata": { "next_step": "legal review" } }
```

`POST /api/opportunities/{opportunity_id}/proposals`

```json
{ "template_id": "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa", "title": "Acme proposal", "customizations": { "discount": "10%" } }
```

`POST /api/opportunities/{opportunity_id}/quotes`

```json
{ "items": [{ "name": "Pro plan", "quantity": 10, "price": 99 }], "valid_until": "2026-07-31", "terms": "Net 30", "metadata": {} }
```

`POST /api/meetings`

```json
{ "lead_id": "22222222-2222-4222-8222-222222222222", "opportunity_id": "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb", "title": "Product demo", "start_time": "2026-07-01T10:00:00+00:00", "end_time": "2026-07-01T10:30:00+00:00", "timezone": "Asia/Kolkata", "attendees": [{ "email": "lead@example.com" }], "location": "Google Meet", "calendar_event_id": "cccccccc-cccc-4ccc-8ccc-cccccccccccc", "metadata": {} }
```

`PATCH /api/meetings/{meeting_id}`

```json
{ "title": "Updated product demo", "start_time": "2026-07-01T11:00:00+00:00", "end_time": "2026-07-01T11:30:00+00:00", "status": "completed", "notes": "Customer wants pricing", "metadata": { "recording_url": "https://example.com/recording" } }
```

## Customers & Customer Success

`POST /api/customers/{customer_id}/contacts`

```json
{ "name": "Priya Menon", "email": "priya@acme.com", "phone": "9876543210", "role": "Admin", "is_primary": true, "metadata": { "department": "operations" } }
```

`POST /api/customers/{customer_id}/health-scores`

```json
{ "force_recalculate": true, "model": "default", "metadata": { "reason": "weekly check" } }
```

`POST /api/customers/{customer_id}/events`

```json
{ "type": "feature_used", "feature": "dashboard", "timestamp": "2026-07-01T10:00:00+00:00", "metadata": { "count": 5 } }
```

`POST /api/customers/{customer_id}/renewals`

```json
{ "subscription_id": "dddddddd-dddd-4ddd-8ddd-dddddddddddd", "renewal_date": "2026-12-31", "expected_value": 25000, "probability": 0.8, "notes": "High renewal confidence", "metadata": {} }
```

`PATCH /api/renewals/{renewal_id}`

```json
{ "renewal_date": "2027-01-15", "expected_value": 28000, "probability": 0.9, "status": "closed_won", "actual_value": 27500, "closed_date": "2026-12-20", "notes": "Renewed with expansion", "metadata": { "owner": "csm" } }
```
