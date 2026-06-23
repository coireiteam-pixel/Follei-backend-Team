"""
Realistic sample data seeder for Follei API.
Populates all domains with production-like data.
"""
from app.core.ids import short_id
from datetime import datetime, timedelta
from random import choice, randint, uniform
from typing import List

from sqlalchemy.orm import Session

from app.database.session import SessionLocal
from app.models.tenancy import Tenant, User
from app.models.agents.agent import Agent, AgentVersion, AgentSession, AgentTask
from app.models.conversations.conversation import (
    Conversation,
    Message,
    ConversationParticipant,
)
from app.models.customers.customer import Customer
from app.models.leads.lead import Lead
from app.models.knowledge.document import Document, DocumentChunk
from app.models.integrations.integration import Integration, IntegrationConnection
from app.models.domain import Plan, Subscription, Event


# Realistic sample data constants
TENANTS = [
    {
        "name": "TechCorp Solutions",
        "domain": "techcorp.com",
        "plan": "enterprise",
    },
    {
        "name": "GreenLeaf Retail",
        "domain": "greenleaf.co",
        "plan": "professional",
    },
    {
        "name": "FinEdge Banking",
        "domain": "finedge.io",
        "plan": "enterprise",
    },
]

USERS_PER_TENANT = [
    {"email": "admin@techcorp.com", "first_name": "Raj", "last_name": "Kumar", "role": "admin"},
    {"email": "support@techcorp.com", "first_name": "Priya", "last_name": "Sharma", "role": "agent"},
    {"email": "sales@techcorp.com", "first_name": "Arun", "last_name": "Verma", "role": "sales"},
]

AGENTS = [
    {"name": "Support Bot", "role": "support", "tools": ["knowledge_search", "ticket_create"]},
    {"name": "SDR Bot", "role": "sdr", "tools": ["lead_score", "crm_update"]},
    {"name": "CS Bot", "role": "customer_success", "tools": ["health_check", "renewal_alert"]},
]

LEAD_FIRST_NAMES = ["Vikram", "Anita", "Rahul", "Sneha", "Karthik", "Meera", "Aditya", "Pooja"]
LEAD_LAST_NAMES = ["Patel", "Singh", "Reddy", "Nair", "Gupta", "Joshi", "Rao", "Iyer"]
LEAD_COMPANIES = ["Infosys", "TCS", "Wipro", "HCL", "Tech Mahindra", "LTI", "Mphasis", "Cognizant"]
LEAD_SOURCES = ["website", "referral", "linkedin", "google_ads", "webinar", "cold_outreach"]
LEAD_STATUSES = ["new", "contacted", "qualified", "proposal", "negotiation", "won", "lost"]

CUSTOMER_NAMES = ["TechCorp Solutions", "GreenLeaf Retail", "FinEdge Banking", "HealthFirst Inc", "EduSmart Labs"]

CONVERSATION_CHANNELS = ["web", "whatsapp", "email", "sms", "voice"]
CONVERSATION_STATUSES = ["open", "active", "resolved", "closed"]

MESSAGE_ROLES = ["user", "assistant", "system"]
MESSAGE_CONTENTS = [
    "Hi, I need help with my subscription.",
    "Can you tell me about your pricing plans?",
    "I'm interested in the enterprise features.",
    "How do I integrate with my CRM?",
    "What's the uptime SLA?",
    "Can I schedule a demo?",
    "I have a question about billing.",
    "Thanks for the quick response!",
    "Let me check with my team and get back to you.",
    "That sounds good, let's proceed.",
]

DOCUMENT_TITLES = [
    "Q4 2024 Product Roadmap",
    "Enterprise Security Whitepaper",
    "API Integration Guide",
    "Customer Success Playbook",
    "Sales Training Manual",
    "Onboarding Checklist",
    "Compliance Policy v2.1",
    "Feature Release Notes",
]

INTEGRATION_NAMES = ["salesforce", "hubspot", "zendesk", "slack", "gmail", "google_calendar"]


def seed_tenants(db: Session) -> List[Tenant]:
    tenants = []
    for data in TENANTS:
        tenant = Tenant(
            id=short_id(),
            name=data["name"],
            domain=data["domain"],
            is_active=True,
            created_at=datetime.utcnow() - timedelta(days=randint(30, 365)),
            updated_at=datetime.utcnow() - timedelta(days=randint(1, 30)),
        )
        db.add(tenant)
        tenants.append(tenant)
    db.flush()
    return tenants


def seed_users(db: Session, tenants: List[Tenant]) -> List[User]:
    users = []
    for tenant in tenants:
        for user_data in USERS_PER_TENANT:
            user = User(
                id=short_id(),
                tenant_id=tenant.id,
                email=user_data["email"],
                hashed_password="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj8J5z4rG7qG",  # 'password123'
                first_name=user_data["first_name"],
                last_name=user_data["last_name"],
                role=user_data["role"],
                is_active=True,
                created_at=datetime.utcnow() - timedelta(days=randint(30, 365)),
                updated_at=datetime.utcnow() - timedelta(days=randint(1, 30)),
            )
            db.add(user)
            users.append(user)
    db.flush()
    return users


def seed_agents(db: Session, tenants: List[Tenant]) -> List[Agent]:
    agents = []
    for tenant in tenants:
        for agent_data in AGENTS:
            agent = Agent(
                id=short_id(),
                tenant_id=tenant.id,
                name=agent_data["name"],
                role=agent_data["role"],
                system_prompt=f"You are a helpful {agent_data['role']} assistant for {tenant.name}.",
                tools=agent_data["tools"],
                is_active=True,
                created_at=datetime.utcnow() - timedelta(days=randint(30, 180)),
                updated_at=datetime.utcnow() - timedelta(days=randint(1, 30)),
            )
            db.add(agent)
            agents.append(agent)
    db.flush()
    return agents


def seed_leads(db: Session, tenants: List[Tenant]) -> List[Lead]:
    leads = []
    for tenant in tenants:
        for _ in range(15):
            lead = Lead(
                id=short_id(),
                tenant_id=tenant.id,
                email=f"{choice(LEAD_FIRST_NAMES).lower()}.{choice(LEAD_LAST_NAMES).lower()}@{choice(LEAD_COMPANIES).lower()}.com",
                first_name=choice(LEAD_FIRST_NAMES),
                last_name=choice(LEAD_LAST_NAMES),
                company=choice(LEAD_COMPANIES),
                status=choice(LEAD_STATUSES),
                revenue_score=randint(0, 100),
                source=choice(LEAD_SOURCES),
                metadata={"campaign": f"campaign_{randint(1, 10)}", "utm_source": choice(LEAD_SOURCES)},
                created_at=datetime.utcnow() - timedelta(days=randint(1, 90)),
                updated_at=datetime.utcnow() - timedelta(days=randint(1, 30)),
            )
            db.add(lead)
            leads.append(lead)
    db.flush()
    return leads


def seed_customers(db: Session, tenants: List[Tenant], leads: List[Lead]) -> List[Customer]:
    customers = []
    for tenant in tenants:
        tenant_leads = [l for l in leads if l.tenant_id == tenant.id][:5]
        for lead in tenant_leads:
            customer = Customer(
                id=short_id(),
                tenant_id=tenant.id,
                lead_id=lead.id,
                name=lead.company,
                health_score=randint(60, 100),
                churn_risk=choice(["low", "medium", "high"]),
                metadata={"industry": "technology", "employees": randint(50, 5000)},
                created_at=datetime.utcnow() - timedelta(days=randint(30, 180)),
                updated_at=datetime.utcnow() - timedelta(days=randint(1, 30)),
            )
            db.add(customer)
            customers.append(customer)
    db.flush()
    return customers


def seed_conversations(db: Session, tenants: List[Tenant], agents: List[Agent], leads: List[Lead], customers: List[Customer]) -> List[Conversation]:
    conversations = []
    for tenant in tenants:
        tenant_agents = [a for a in agents if a.tenant_id == tenant.id]
        tenant_leads = [l for l in leads if l.tenant_id == tenant.id]
        tenant_customers = [c for c in customers if c.tenant_id == tenant.id]

        for _ in range(20):
            agent = choice(tenant_agents) if len(tenant_agents) > 0 else None
            lead = choice(tenant_leads) if len(tenant_leads) > 0 else None
            customer = choice(tenant_customers) if len(tenant_customers) > 0 else None

            conversation = Conversation(
                id=short_id(),
                tenant_id=tenant.id,
                agent_id=agent.id if agent else None,
                lead_id=lead.id if lead else None,
                customer_id=customer.id if customer else None,
                title=f"Conversation with {lead.first_name if lead else 'Customer'}",
                channel=choice(CONVERSATION_CHANNELS),
                status=choice(CONVERSATION_STATUSES),
                created_at=datetime.utcnow() - timedelta(days=randint(1, 60)),
                updated_at=datetime.utcnow() - timedelta(days=randint(0, 30)),
            )
            db.add(conversation)
            conversations.append(conversation)
    db.flush()
    return conversations


def seed_messages(db: Session, conversations: List[Conversation]) -> List[Message]:
    messages = []
    for conversation in conversations:
        num_messages = randint(3, 15)
        for i in range(num_messages):
            message = Message(
                id=short_id(),
                tenant_id=conversation.tenant_id,
                conversation_id=conversation.id,
                role=choice(MESSAGE_ROLES),
                content=choice(MESSAGE_CONTENTS),
                metadata={"message_index": i},
                created_at=conversation.created_at + timedelta(minutes=i * randint(1, 5)),
            )
            db.add(message)
            messages.append(message)
    db.flush()
    return messages


def seed_documents(db: Session, tenants: List[Tenant]) -> List[Document]:
    documents = []
    for tenant in tenants:
        for title in DOCUMENT_TITLES:
            doc = Document(
                id=short_id(),
                tenant_id=tenant.id,
                title=title,
                source_type="upload",
                mime_type="application/pdf",
                status="indexed",
                tags=["knowledge_base", "documentation"],
                summary=f"This document contains information about {title.lower()}.",
                keywords=["product", "policy", "guide"],
                metadata={"author": "System", "version": "1.0"},
                created_at=datetime.utcnow() - timedelta(days=randint(30, 180)),
                updated_at=datetime.utcnow() - timedelta(days=randint(1, 30)),
                indexed_at=datetime.utcnow() - timedelta(days=randint(1, 30)),
            )
            db.add(doc)
            documents.append(doc)
    db.flush()
    return documents


def seed_document_chunks(db: Session, documents: List[Document]) -> List[DocumentChunk]:
    chunks = []
    for doc in documents:
        num_chunks = randint(5, 20)
        for i in range(num_chunks):
            chunk = DocumentChunk(
                id=short_id(),
                tenant_id=doc.tenant_id,
                document_id=doc.id,
                chunk_index=i,
                content=f"This is chunk {i} of document '{doc.title}'. It contains relevant information for RAG retrieval.",
                token_count=randint(50, 200),
                metadata={"page": i + 1},
                created_at=doc.created_at,
            )
            db.add(chunk)
            chunks.append(chunk)
    db.flush()
    return chunks


def seed_integrations(db: Session, tenants: List[Tenant]) -> List[IntegrationConnection]:
    connections = []
    for tenant in tenants:
        for integration_name in INTEGRATION_NAMES[:3]:  # First 3 integrations per tenant
            integration = Integration(
                id=short_id(),
                name=integration_name,
                description=f"{integration_name.title()} integration for {tenant.name}",
                is_active=True,
                created_at=datetime.utcnow() - timedelta(days=randint(30, 180)),
            )
            db.add(integration)
            db.flush()

            connection = IntegrationConnection(
                id=short_id(),
                tenant_id=tenant.id,
                integration_id=integration.id,
                status="active",
                config={"api_key": f"key_{short_id()}", "sync_enabled": True},
                created_at=datetime.utcnow() - timedelta(days=randint(30, 180)),
                updated_at=datetime.utcnow() - timedelta(days=randint(1, 30)),
            )
            db.add(connection)
            connections.append(connection)
    db.flush()
    return connections


def seed_plans_and_subscriptions(db: Session, tenants: List[Tenant]) -> List[Subscription]:
    plans = [
        {"name": "starter", "price": 29, "features": ["basic_support", "1000_messages"]},
        {"name": "professional", "price": 99, "features": ["priority_support", "10000_messages", "analytics"]},
        {"name": "enterprise", "price": 299, "features": ["dedicated_support", "unlimited", "custom_integrations"]},
    ]

    subscriptions = []
    for tenant in tenants:
        plan_data = next(p for p in plans if p["name"] == tenant.plan)
        plan = Plan(
            id=short_id(),
            name=plan_data["name"],
            price=plan_data["price"],
            features=plan_data["features"],
            is_active=True,
            created_at=datetime.utcnow() - timedelta(days=randint(30, 180)),
        )
        db.add(plan)
        db.flush()

        subscription = Subscription(
            id=short_id(),
            tenant_id=tenant.id,
            plan_name=plan.name,
            status="active",
            current_period_start=datetime.utcnow() - timedelta(days=30),
            current_period_end=datetime.utcnow() + timedelta(days=30),
            metadata={"price": plan.price, "features": plan.features},
            created_at=datetime.utcnow() - timedelta(days=randint(30, 180)),
            updated_at=datetime.utcnow() - timedelta(days=randint(1, 30)),
        )
        db.add(subscription)
        subscriptions.append(subscription)
    db.flush()
    return subscriptions


def seed_events(db: Session, tenants: List[Tenant]) -> List[Event]:
    events = []
    event_types = ["message.received", "response.generated", "document.ingested", "lead.created", "ticket.created"]

    for tenant in tenants:
        for _ in range(50):
            event = Event(
                id=short_id(),
                tenant_id=tenant.id,
                event_type=choice(event_types),
                payload={"source": "api", "user_agent": "Mozilla/5.0"},
                created_at=datetime.utcnow() - timedelta(days=randint(1, 30), hours=randint(0, 23)),
            )
            db.add(event)
            events.append(event)
    db.flush()
    return events


def seed_usage_events(db: Session, tenants: List[Tenant], agents: List[Agent]) -> List[Event]:
    usage_events = []
    event_names = ["message_sent", "api_call", "document_processed", "tool_executed"]

    for tenant in tenants:
        tenant_agents = [a for a in agents if a.tenant_id == tenant.id]
        for _ in range(100):
            usage_event = Event(
                id=short_id(),
                tenant_id=tenant.id,
                event_type=choice(event_names),
                payload={
                    "user_id": None,
                    "agent_id": choice(tenant_agents).id if len(tenant_agents) > 0 else None,
                    "quantity": randint(1, 10),
                    "endpoint": "/api/v1/chat",
                    "latency_ms": randint(50, 500),
                },
                created_at=datetime.utcnow() - timedelta(days=randint(1, 30), hours=randint(0, 23)),
            )
            db.add(usage_event)
            usage_events.append(usage_event)
    db.flush()
    return usage_events


def run_seed():
    """Main seed function to populate database with realistic data."""
    db: Session = SessionLocal()
    try:
        print("Starting database seeding...")

        print("Seeding tenants...")
        tenants = seed_tenants(db)

        print("Seeding users...")
        users = seed_users(db, tenants)

        print("Seeding agents...")
        agents = seed_agents(db, tenants)

        print("Seeding leads...")
        leads = seed_leads(db, tenants)

        print("Seeding customers...")
        customers = seed_customers(db, tenants, leads)

        print("Seeding conversations...")
        conversations = seed_conversations(db, tenants, agents, leads, customers)

        print("Seeding messages...")
        messages = seed_messages(db, conversations)

        print("Seeding documents...")
        documents = seed_documents(db, tenants)

        print("Seeding document chunks...")
        chunks = seed_document_chunks(db, documents)

        print("Seeding integrations...")
        connections = seed_integrations(db, tenants)

        print("Seeding plans and subscriptions...")
        subscriptions = seed_plans_and_subscriptions(db, tenants)

        print("Seeding events...")
        events = seed_events(db, tenants)

        print("Seeding usage events...")
        usage_events = seed_usage_events(db, tenants, agents)

        db.commit()
        print(f"\n✅ Seeding completed successfully!")
        print(f"   Tenants: {len(tenants)}")
        print(f"   Users: {len(users)}")
        print(f"   Agents: {len(agents)}")
        print(f"   Leads: {len(leads)}")
        print(f"   Customers: {len(customers)}")
        print(f"   Conversations: {len(conversations)}")
        print(f"   Messages: {len(messages)}")
        print(f"   Documents: {len(documents)}")
        print(f"   Document Chunks: {len(chunks)}")
        print(f"   Integration Connections: {len(connections)}")
        print(f"   Subscriptions: {len(subscriptions)}")
        print(f"   Events: {len(events)}")
        print(f"   Usage Events: {len(usage_events)}")

    except Exception as e:
        db.rollback()
        print(f"\n❌ Seeding failed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    run_seed()