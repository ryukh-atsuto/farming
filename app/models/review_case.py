# app/models/review_case.py
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, List, Optional

@dataclass
class ReviewCase:
    conversation_id: str
    reasons: List[str] = field(default_factory=list)
    status: str = "pending_agronomist_review"  # pending_agronomist_review, reviewed, dismissed
    agronomist_notes: Optional[str] = None
    triggered_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "conversation_id": self.conversation_id,
            "reasons": self.reasons,
            "status": self.status,
            "agronomist_notes": self.agronomist_notes,
            "triggered_at": self.triggered_at
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ReviewCase":
        return cls(
            conversation_id=data["conversation_id"],
            reasons=data.get("reasons", []),
            status=data.get("status", "pending_agronomist_review"),
            agronomist_notes=data.get("agronomist_notes"),
            triggered_at=data.get("triggered_at", datetime.utcnow().isoformat())
        )
