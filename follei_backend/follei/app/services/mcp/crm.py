from app.core.ids import short_id


def search(query: str, object: str = "Contact", limit: int = 10) -> dict:
    return {
        "contacts": [
            {"id": str(short_id()), "name": "Jane Lead", "email": "jane@acme.com", "object": object, "query": query}
            for _ in range(min(limit, 3))
        ]
    }


def create_contact(name: str, email: str, company: str | None = None) -> dict:
    return {"contact_id": str(short_id()), "name": name, "email": email, "company": company, "success": True}


def update_deal(deal_id: str, stage: str, amount: float | None = None) -> dict:
    return {"deal_id": deal_id, "stage": stage, "amount": amount, "updated": True}
