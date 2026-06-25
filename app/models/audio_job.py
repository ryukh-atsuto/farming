# app/models/audio_job.py
from dataclasses import dataclass, asdict
from typing import Dict, Any, Optional

@dataclass
class AudioJob:
    id: str
    filename: str
    filepath: str
    status: str = "pending"  # pending, preprocessing, stt, completed, failed
    duration: float = 0.0
    sample_rate: int = 16000
    channels: int = 1
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AudioJob":
        return cls(
            id=data["id"],
            filename=data["filename"],
            filepath=data["filepath"],
            status=data.get("status", "pending"),
            duration=data.get("duration", 0.0),
            sample_rate=data.get("sample_rate", 16000),
            channels=data.get("channels", 1),
            error_message=data.get("error_message")
        )
