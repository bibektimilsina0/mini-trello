from typing import Any


class EventType:
    CARD_CREATED = "card_created"
    CARD_UPDATED = "card_updated"
    CARD_MOVED = "card_moved"
    CARD_DELETED = "card_deleted"
    LIST_CREATED = "list_created"
    LIST_UPDATED = "list_updated"
    COMMENT_CREATED = "comment_created"


def build_event(event_type: str, payload: dict[str, Any]) -> dict[str, Any]:
    return {"type": event_type, "payload": payload}