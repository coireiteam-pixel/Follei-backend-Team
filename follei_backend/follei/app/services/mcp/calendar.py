from uuid import uuid4


def create_event(title: str, start: str, end: str, attendees: list | None = None) -> dict:
    event_id = str(uuid4())
    return {"event_id": event_id, "title": title, "start": start, "end": end, "attendees": attendees or [], "calendar_link": f"https://calendar.example.com/{event_id}", "created": True}


def check_availability(email: str, date: str, duration_minutes: int = 60) -> dict:
    return {
        "email": email,
        "date": date,
        "duration_minutes": duration_minutes,
        "available_slots": [{"start": "14:00", "end": "15:00"}, {"start": "16:00", "end": "17:00"}],
    }
