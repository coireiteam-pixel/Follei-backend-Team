#!/usr/bin/env python3
"""Generate live demo data for the Follei backend.

Run from ``follei_backend/follei``:

    python generate_realtime_data.py
    python generate_realtime_data.py --once
    python generate_realtime_data.py --iterations 25 --interval 1
"""

from __future__ import annotations

import argparse
import random
import time
from dataclasses import dataclass
from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy import func, text
from sqlalchemy.orm import Session

from app.core.ids import short_id
from app.database.init_db import init_db
from app.database.session import SQLALCHEMY_DATABASE_URL, SessionLocal, engine
from app.models.agents.agent import Agent, AgentAction, AgentTask, AgentToolCall
from app.models.conversations.conversation import (
    Conversation,
    ConversationBuyingSignal,
    ConversationIntent,
    ConversationMetric,
    ConversationSentiment,
    Message,
    ResponseMetric,
)
from app.models.customers.customer import Customer
from app.models.domain import AnalyticsDaily, Event, ModelUsage
from app.models.leads.lead import Lead
from app.models.tenancy import Tenant, User


RNG = random.Random()

TENANT_NAMES = [
    "Follei Demo Labs",
    "Coirei Growth Systems",
    "Northstar SaaS Ops",
]

AGENT_PROFILES = [
    ("Asha Support", "support", "Resolve support conversations with accurate knowledge citations."),
    ("Vikram SDR", "sdr", "Qualify inbound leads and book demos."),
    ("Meera Success", "customer_success", "Monitor account health and expansion signals."),
]

LEAD_NAMES = [
    ("Arjun", "Raman", "arjun.raman@example.com", "Acme Cloud"),
    ("Priya", "Nair", "priya.nair@example.com", "Nova Retail"),
    ("Kavin", "Shah", "kavin.shah@example.com", "Helio Finance"),
    ("Divya", "Menon", "divya.menon@example.com", "BluePeak Logistics"),
]

CUSTOMER_NAMES = [
    "Acme Cloud",
    "Nova Retail",
    "Helio Finance",
    "BluePeak Logistics",
]

CUSTOMER_MESSAGES = [
    "Can you explain pricing for the pro plan?",
    "We want to schedule a product demo this week.",
    "The dashboard is slow for our support team.",
    "Do you integrate with Salesforce and Slack?",
    "Can you summarize our onboarding status?",
    "We are comparing Follei with another vendor.",
]

AGENT_MESSAGES = [
    "I can help with that. The pro plan is best for teams that need automation and analytics.",
    "I found available demo slots and can prepare the handoff notes for sales.",
    "I checked the account context and will open a support action for the dashboard latency.",
    "Follei supports CRM and messaging integrations through the integration layer.",
    "Your onboarding is mostly complete, with one pending data sync step.",
    "Here is a concise comparison based on your requirements.",
]

INTENTS = ["pricing_question", "demo_request", "support_issue", "integration_question", "onboarding_check"]
SENTIMENTS = ["positive", "neutral", "curious", "concerned"]
BUYING_SIGNALS = ["demo_requested", "budget_confirmed", "integration_fit", "timeline_shared"]
TOOL_NAMES = ["crm.lookup_account", "calendar.find_slots", "knowledge.search", "ticket.create"]


def utc_now_naive() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


@dataclass
class SeedState:
    tenants: list[Tenant]
    users: list[User]
    agents: list[Agent]
    leads: list[Lead]
    customers: list[Customer]


class RealtimeDatasetGenerator:
    def __init__(self, interval: float = 2.0, batch_size: int = 1) -> None:
        self.interval = interval
        self.batch_size = batch_size
        self.running = False

    def run(self, iterations: int | None = None) -> None:
        init_db()
        self.running = True
        generated = 0
        print(f"Realtime generator connected to: {SQLALCHEMY_DATABASE_URL}")

        try:
            while self.running and (iterations is None or generated < iterations):
                with SessionLocal() as db:
                    state = self.ensure_seed_data(db)
                    for _ in range(self.batch_size):
                        self.generate_activity(db, state)
                        generated += 1
                    db.commit()
                    print(f"Generated realtime batch. Total generated: {generated}")
                if iterations is None or generated < iterations:
                    time.sleep(self.interval)
        except KeyboardInterrupt:
            print("Realtime generator stopped.")

    def ensure_seed_data(self, db: Session) -> SeedState:
        tenants = db.query(Tenant).limit(10).all()
        if not tenants:
            tenants = self._create_tenants(db)
            db.flush()

        users = db.query(User).filter(User.tenant_id.in_([tenant.id for tenant in tenants])).all()
        if not users:
            users = self._create_users(db, tenants)
            db.flush()

        agents = db.query(Agent).filter(Agent.tenant_id.in_([tenant.id for tenant in tenants])).all()
        tenants_without_agents = [
            tenant for tenant in tenants if not any(agent.tenant_id == tenant.id for agent in agents)
        ]
        if tenants_without_agents:
            agents.extend(self._create_agents(db, tenants_without_agents))
            db.flush()

        leads = db.query(Lead).filter(Lead.tenant_id.in_([tenant.id for tenant in tenants])).all()
        tenants_without_leads = [
            tenant for tenant in tenants if not any(lead.tenant_id == tenant.id for lead in leads)
        ]
        if tenants_without_leads:
            leads.extend(self._create_leads(db, tenants_without_leads))
            db.flush()

        customers = db.query(Customer).filter(Customer.tenant_id.in_([tenant.id for tenant in tenants])).all()
        tenants_without_customers = [
            tenant for tenant in tenants if not any(customer.tenant_id == tenant.id for customer in customers)
        ]
        if tenants_without_customers:
            customers.extend(self._create_customers(db, tenants_without_customers, leads))
            db.flush()

        return SeedState(tenants=tenants, users=users, agents=agents, leads=leads, customers=customers)

    def generate_activity(self, db: Session, state: SeedState) -> None:
        tenant = RNG.choice(state.tenants)
        tenant_agents = [agent for agent in state.agents if agent.tenant_id == tenant.id]
        tenant_leads = [lead for lead in state.leads if lead.tenant_id == tenant.id]
        tenant_customers = [customer for customer in state.customers if customer.tenant_id == tenant.id]

        agent = RNG.choice(tenant_agents)
        lead = RNG.choice(tenant_leads) if RNG.random() < 0.55 and tenant_leads else None
        customer = RNG.choice(tenant_customers) if tenant_customers else None
        now = utc_now_naive()

        conversation = Conversation(
            tenant_id=tenant.id,
            agent_id=agent.id,
            lead_id=lead.id if lead else None,
            customer_id=None if lead else customer.id,
            title=RNG.choice([
                "Realtime pricing conversation",
                "Realtime support conversation",
                "Realtime demo request",
                "Realtime onboarding check",
            ]),
            channel=RNG.choice(["web", "whatsapp", "email", "slack"]),
            status=RNG.choice(["open", "active", "resolved"]),
            started_at=now,
        )
        db.add(conversation)
        db.flush()

        customer_text = RNG.choice(CUSTOMER_MESSAGES)
        agent_text = RNG.choice(AGENT_MESSAGES)
        user_message = Message(
            tenant_id=tenant.id,
            conversation_id=conversation.id,
            role="user",
            content=customer_text,
            sender_type="lead" if lead else "customer",
            sender_id=lead.id if lead else customer.id,
            message=customer_text,
            message_type="text",
            metadata_={"source": "realtime_generator"},
            created_at=now,
        )
        agent_message = Message(
            tenant_id=tenant.id,
            conversation_id=conversation.id,
            role="agent",
            content=agent_text,
            sender_type="agent",
            sender_id=agent.id,
            message=agent_text,
            message_type="text",
            metadata_={"source": "realtime_generator", "model": "demo-agent"},
            created_at=now,
        )
        db.add_all([user_message, agent_message])
        db.flush()

        response_time = Decimal(str(round(RNG.uniform(0.4, 5.5), 2)))
        db.add_all(
            [
                ConversationIntent(
                    tenant_id=tenant.id,
                    conversation_id=conversation.id,
                    intent=RNG.choice(INTENTS),
                    confidence=Decimal(str(round(RNG.uniform(0.65, 0.98), 2))),
                    evidence=customer_text,
                    detected_at=now,
                    created_at=now,
                ),
                ConversationSentiment(
                    tenant_id=tenant.id,
                    conversation_id=conversation.id,
                    message_id=user_message.id,
                    sentiment=RNG.choice(SENTIMENTS),
                    score=Decimal(str(round(RNG.uniform(0.45, 0.95), 2))),
                    detected_at=now,
                    created_at=now,
                ),
                ConversationMetric(
                    tenant_id=tenant.id,
                    conversation_id=conversation.id,
                    response_time_seconds=response_time,
                    resolution_time_seconds=Decimal(str(round(RNG.uniform(60, 900), 2))),
                    message_count=2,
                    metadata_={"channel": conversation.channel, "source": "realtime_generator"},
                    created_at=now,
                ),
                ResponseMetric(
                    tenant_id=tenant.id,
                    message_id=agent_message.id,
                    quality_score=Decimal(str(round(RNG.uniform(0.7, 0.99), 2))),
                    metrics={
                        "latency_ms": int(response_time * 1000),
                        "grounded": RNG.random() > 0.12,
                        "source": "realtime_generator",
                    },
                    created_at=now,
                ),
            ]
        )

        if RNG.random() < 0.45:
            db.add(
                ConversationBuyingSignal(
                    tenant_id=tenant.id,
                    conversation_id=conversation.id,
                    signal_type=RNG.choice(BUYING_SIGNALS),
                    evidence=customer_text,
                    confidence=Decimal(str(round(RNG.uniform(0.55, 0.95), 2))),
                    detected_at=now,
                    created_at=now,
                )
            )

        self._create_agent_work(db, tenant, agent, conversation, now)
        self._create_events_and_analytics(db, tenant, conversation, agent_message, now)

        if lead:
            lead.revenue_score = min(100, (lead.revenue_score or 0) + RNG.randint(1, 8))
            lead.status = RNG.choice(["new", "qualified", "contacted"])
        if customer:
            customer.health_score = max(1, min(100, (customer.health_score or 80) + RNG.randint(-3, 3)))
            customer.churn_risk = "high" if customer.health_score < 45 else "medium" if customer.health_score < 70 else "low"

    def _create_agent_work(
        self,
        db: Session,
        tenant: Tenant,
        agent: Agent,
        conversation: Conversation,
        now: datetime,
    ) -> None:
        task = AgentTask(
            tenant_id=tenant.id,
            agent_id=agent.id,
            task_type=RNG.choice(["reply", "qualify_lead", "summarize", "create_ticket"]),
            title=f"Realtime task for {conversation.title}",
            payload={"conversation_id": str(conversation.id), "source": "realtime_generator"},
            status=RNG.choice(["queued", "in_progress", "completed"]),
            created_at=now,
            updated_at=now,
        )
        db.add(task)
        db.flush()

        tool_name = RNG.choice(TOOL_NAMES)
        db.add_all(
            [
                AgentAction(
                    tenant_id=tenant.id,
                    agent_id=agent.id,
                    task_id=task.id,
                    action_type=RNG.choice(["search_knowledge", "update_crm", "schedule_follow_up"]),
                    payload={"conversation_id": str(conversation.id), "source": "realtime_generator"},
                    result={"ok": True},
                    status="completed",
                    created_at=now,
                ),
                AgentToolCall(
                    tenant_id=tenant.id,
                    agent_id=agent.id,
                    tool_name=tool_name,
                    request={"conversation_id": str(conversation.id)},
                    response={"status": "ok", "tool": tool_name},
                    status="completed",
                    started_at=now,
                    finished_at=now,
                    created_at=now,
                ),
            ]
        )

    def _create_events_and_analytics(
        self,
        db: Session,
        tenant: Tenant,
        conversation: Conversation,
        message: Message,
        now: datetime,
    ) -> None:
        prompt_tokens = RNG.randint(200, 900)
        completion_tokens = RNG.randint(80, 350)
        latency_ms = RNG.randint(400, 5500)
        db.add_all(
            [
                Event(
                    tenant_id=tenant.id,
                    event_type="message.generated",
                    payload={
                        "conversation_id": str(conversation.id),
                        "message_id": str(message.id),
                        "channel": conversation.channel,
                        "source": "realtime_generator",
                    },
                    created_at=now,
                ),
                AnalyticsDaily(
                    tenant_id=tenant.id,
                    metric_date=date.today(),
                    metric_name=RNG.choice(["messages", "conversations", "agent_actions", "tool_calls"]),
                    metric_value=Decimal(str(RNG.randint(1, 5))),
                    dimensions={"channel": conversation.channel, "source": "realtime_generator"},
                    created_at=now,
                ),
                ModelUsage(
                    tenant_id=tenant.id,
                    model="demo-agent",
                    provider="follei-local",
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    total_tokens=prompt_tokens + completion_tokens,
                    cost=Decimal(str(round((prompt_tokens + completion_tokens) * 0.000002, 6))),
                    latency_ms=latency_ms,
                    metadata_={"source": "realtime_generator"},
                    created_at=now,
                ),
            ]
        )

    def _create_tenants(self, db: Session) -> list[Tenant]:
        tenants = [
            Tenant(
                name=name,
                domain=f"{self._slug(name)}.example.com",
                created_at=utc_now_naive(),
            )
            for name in TENANT_NAMES
        ]
        db.add_all(tenants)
        return tenants

    def _create_users(self, db: Session, tenants: list[Tenant]) -> list[User]:
        users = [
            User(
                tenant_id=tenant.id,
                email=f"admin+{self._slug(tenant.name)}@follei.local",
                hashed_password="demo-only-not-a-real-password-hash",
                first_name="Demo",
                last_name="Admin",
                role="admin",
                is_active=True,
            )
            for tenant in tenants
        ]
        db.add_all(users)
        return users

    def _create_agents(self, db: Session, tenants: list[Tenant]) -> list[Agent]:
        if engine.url.get_backend_name() == "sqlite":
            return self._create_agents_for_sqlite(db, tenants)

        agents: list[Agent] = []
        for tenant in tenants:
            for name, role, prompt in AGENT_PROFILES:
                agents.append(
                    Agent(
                        tenant_id=tenant.id,
                        name=name,
                        role=role,
                        system_prompt=prompt,
                        tools=self._empty_tools_value(),
                    )
                )
        db.add_all(agents)
        return agents

    def _create_agents_for_sqlite(self, db: Session, tenants: list[Tenant]) -> list[Agent]:
        agent_ids: list[str] = []
        now = utc_now_naive()
        for tenant in tenants:
            for name, role, prompt in AGENT_PROFILES:
                agent_id = short_id()
                agent_ids.append(agent_id)
                db.execute(
                    text(
                        """
                        INSERT INTO agents (id, tenant_id, name, role, system_prompt, tools, created_at)
                        VALUES (:id, :tenant_id, :name, :role, :system_prompt, :tools, :created_at)
                        """
                    ),
                    {
                        "id": agent_id,
                        "tenant_id": tenant.id,
                        "name": name,
                        "role": role,
                        "system_prompt": prompt,
                        "tools": "[]",
                        "created_at": now,
                    },
                )
        return db.query(Agent).filter(Agent.id.in_(agent_ids)).all()

    def _create_leads(self, db: Session, tenants: list[Tenant]) -> list[Lead]:
        leads: list[Lead] = []
        for tenant in tenants:
            for first_name, last_name, email, company in LEAD_NAMES:
                leads.append(
                    Lead(
                        tenant_id=tenant.id,
                        email=f"{self._slug(tenant.name)}.{email}",
                        first_name=first_name,
                        last_name=last_name,
                        company=company,
                        status=RNG.choice(["new", "contacted", "qualified"]),
                        revenue_score=RNG.randint(10, 80),
                    )
                )
        db.add_all(leads)
        return leads

    def _create_customers(self, db: Session, tenants: list[Tenant], leads: list[Lead]) -> list[Customer]:
        customers: list[Customer] = []
        for tenant in tenants:
            tenant_leads = [lead for lead in leads if lead.tenant_id == tenant.id]
            for index, name in enumerate(CUSTOMER_NAMES):
                lead = tenant_leads[index % len(tenant_leads)] if tenant_leads else None
                customers.append(
                    Customer(
                        tenant_id=tenant.id,
                        lead_id=lead.id if lead else None,
                        name=name,
                        health_score=RNG.randint(55, 98),
                        churn_risk=RNG.choice(["low", "medium"]),
                        metadata_={"source": "realtime_generator"},
                    )
                )
        db.add_all(customers)
        return customers

    @staticmethod
    def _slug(value: str) -> str:
        return "".join(char.lower() if char.isalnum() else "-" for char in value).strip("-")

    @staticmethod
    def _empty_tools_value() -> list[str] | str:
        if engine.url.get_backend_name() == "postgresql":
            return []
        return "[]"


def print_counts() -> None:
    with SessionLocal() as db:
        counts = {
            "tenants": db.query(func.count(Tenant.id)).scalar(),
            "agents": db.query(func.count(Agent.id)).scalar(),
            "leads": db.query(func.count(Lead.id)).scalar(),
            "customers": db.query(func.count(Customer.id)).scalar(),
            "conversations": db.query(func.count(Conversation.id)).scalar(),
            "messages": db.query(func.count(Message.id)).scalar(),
            "events": db.query(func.count(Event.id)).scalar(),
            "analytics_daily": db.query(func.count(AnalyticsDaily.id)).scalar(),
            "model_usage": db.query(func.count(ModelUsage.id)).scalar(),
        }
    print("Current realtime dataset counts:")
    for table, count in counts.items():
        print(f"  {table}: {count}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate live Follei demo data.")
    parser.add_argument("--interval", type=float, default=2.0, help="Seconds between generation batches.")
    parser.add_argument("--batch-size", type=int, default=1, help="Rows of realtime activity per batch.")
    parser.add_argument("--iterations", type=int, default=None, help="Stop after this many activities.")
    parser.add_argument("--once", action="store_true", help="Generate one activity and exit.")
    parser.add_argument("--seed", type=int, default=None, help="Optional random seed for repeatable output.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.seed is not None:
        RNG.seed(args.seed)

    iterations = 1 if args.once else args.iterations
    generator = RealtimeDatasetGenerator(interval=args.interval, batch_size=args.batch_size)
    generator.run(iterations=iterations)
    print_counts()


if __name__ == "__main__":
    main()
