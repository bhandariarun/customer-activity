from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class NormalizedCustomer:
    id: int
    name: str
    email: str


@dataclass(frozen=True)
class NormalizedActivity:
    external_id: int
    customer_id: Optional[int]
    type: str
    title: str
    content: str
    source: str


def normalize_customer_from_crm(raw: Dict[str, Any]) -> Optional[NormalizedCustomer]:
    """
    Expected example:
      {"id": 1, "name": "...", "email": "..."}
    Returns None if missing critical fields.
    """
    try:
        customer_id = int(raw.get("id"))
    except (TypeError, ValueError):
        return None

    name = raw.get("name") or ""
    email = raw.get("email") or ""
    return NormalizedCustomer(id=customer_id, name=name, email=email)


def normalize_activity_from_support_post(
    raw: Dict[str, Any],
) -> Optional[NormalizedActivity]:
    """
    Expected example:
      {"userId": 1, "id": 1, "title": "...", "body": "..."}
    Returns None if missing critical fields (id).
    """
    try:
        external_id = int(raw.get("id"))
    except (TypeError, ValueError):
        return None

    # userId can be missing/invalid; we treat as orphan activity
    customer_id = None
    try:
        if raw.get("userId") is not None:
            customer_id = int(raw.get("userId"))
    except (TypeError, ValueError):
        customer_id = None

    title = raw.get("title") or ""
    body = raw.get("body") or ""

    return NormalizedActivity(
        external_id=external_id,
        customer_id=customer_id,
        type="ticket",
        title=title,
        content=body,
        source="support",
    )
