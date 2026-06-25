import uuid
from datetime import datetime

class Conversation:
    def __init__(self, conversation_id=None, farmer_id=None, user_audio_path=None, 
                 transcript=None, corrected_transcript=None, advisor_response=None, 
                 response_audio_path=None, diagnosis_summary=None, timestamp=None):
        self.conversation_id = conversation_id or str(uuid.uuid4())
        self.farmer_id = farmer_id
        self.user_audio_path = user_audio_path or ""
        self.transcript = transcript or ""
        self.corrected_transcript = corrected_transcript or ""
        self.advisor_response = advisor_response or ""
        self.response_audio_path = response_audio_path or ""
        self.diagnosis_summary = diagnosis_summary or {}
        self.timestamp = timestamp or datetime.utcnow().isoformat()

    def to_dict(self):
        return {
            "conversation_id": self.conversation_id,
            "farmer_id": self.farmer_id,
            "user_audio_path": self.user_audio_path,
            "transcript": self.transcript,
            "corrected_transcript": self.corrected_transcript,
            "advisor_response": self.advisor_response,
            "response_audio_path": self.response_audio_path,
            "diagnosis_summary": self.diagnosis_summary,
            "timestamp": self.timestamp
        }

    @classmethod
    def from_dict(cls, data):
        if not data:
            return cls()
        return cls(
            conversation_id=data.get("conversation_id"),
            farmer_id=data.get("farmer_id"),
            user_audio_path=data.get("user_audio_path"),
            transcript=data.get("transcript"),
            corrected_transcript=data.get("corrected_transcript"),
            advisor_response=data.get("advisor_response"),
            response_audio_path=data.get("response_audio_path"),
            diagnosis_summary=data.get("diagnosis_summary"),
            timestamp=data.get("timestamp")
        )

    def validate(self):
        errors = {}
        if not self.conversation_id:
            errors["conversation_id"] = "Conversation ID must not be empty."
        if not self.transcript and not self.user_audio_path:
            errors["input"] = "Conversation must have either audio input or text transcript."
        return len(errors) == 0, errors
