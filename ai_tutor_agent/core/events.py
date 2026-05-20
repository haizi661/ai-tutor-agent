from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional


@dataclass
class AgentEvent:
    type: str
    source: str
    message: Optional[str] = None
    data: dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "type": self.type,
            "source": self.source,
            "timestamp": self.timestamp,
            "data": self.data,
        }
        if self.message:
            payload["message"] = self.message
        return payload


def make_event(
    event_type: str,
    source: str,
    *,
    message: Optional[str] = None,
    data: Optional[dict[str, Any]] = None,
) -> AgentEvent:
    return AgentEvent(
        type=event_type,
        source=source,
        message=message,
        data=data or {},
    )
