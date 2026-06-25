from datetime import datetime

class Diagnosis:
    def __init__(self, original_transcript=None, corrected_query=None, crop=None, 
                 symptoms=None, disease=None, confidence=0.0, severity="Medium", 
                 urgency="Medium", recommendation_text=None, recommendation_audio_url=None, 
                 rag_context=None, weather_context=None, timestamp=None):
        self.original_transcript = original_transcript or ""
        self.corrected_query = corrected_query or ""
        self.crop = crop or "Unknown"
        self.symptoms = symptoms or ""
        self.disease = disease or "Undetermined"
        self.confidence = float(confidence)
        self.severity = severity or "Medium"
        self.urgency = urgency or "Medium"
        self.recommendation_text = recommendation_text or ""
        self.recommendation_audio_url = recommendation_audio_url or ""
        self.rag_context = rag_context or []
        self.weather_context = weather_context or {}
        self.timestamp = timestamp or datetime.utcnow().isoformat()

    def to_dict(self):
        return {
            "original_transcript": self.original_transcript,
            "corrected_query": self.corrected_query,
            "crop": self.crop,
            "symptoms": self.symptoms,
            "disease": self.disease,
            "confidence": self.confidence,
            "severity": self.severity,
            "urgency": self.urgency,
            "recommendation_text": self.recommendation_text,
            "recommendation_audio_url": self.recommendation_audio_url,
            "rag_context": self.rag_context,
            "weather_context": self.weather_context,
            "timestamp": self.timestamp
        }

    @classmethod
    def from_dict(cls, data):
        if not data:
            return cls()
        return cls(
            original_transcript=data.get("original_transcript"),
            corrected_query=data.get("corrected_query"),
            crop=data.get("crop"),
            symptoms=data.get("symptoms"),
            disease=data.get("disease"),
            confidence=data.get("confidence", 0.0),
            severity=data.get("severity", "Medium"),
            urgency=data.get("urgency", "Medium"),
            recommendation_text=data.get("recommendation_text"),
            recommendation_audio_url=data.get("recommendation_audio_url"),
            rag_context=data.get("rag_context"),
            weather_context=data.get("weather_context"),
            timestamp=data.get("timestamp")
        )

    def validate(self):
        errors = {}
        if not self.crop or self.crop.strip() == "":
            errors["crop"] = "Crop must not be empty."
            
        if self.confidence < 0.0 or self.confidence > 1.0:
            errors["confidence"] = "Confidence score must be between 0.0 and 1.0."
            
        valid_levels = ["Low", "Medium", "High", "Critical"]
        if self.severity not in valid_levels:
            errors["severity"] = f"Severity must be one of {valid_levels}."
        if self.urgency not in valid_levels:
            errors["urgency"] = f"Urgency must be one of {valid_levels}."
            
        if not self.recommendation_text or self.recommendation_text.strip() == "":
            errors["recommendation_text"] = "Recommendation text must be provided."
            
        return len(errors) == 0, errors
