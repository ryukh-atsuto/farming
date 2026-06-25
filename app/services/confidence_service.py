# app/services/confidence_service.py
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class ConfidenceService:
    def calculate_confidence(
        self,
        asr_data: Dict[str, Any],
        intent_data: Dict[str, Any],
        rag_data: Dict[str, Any],
        weather_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Calculates system-wide confidence score based on ASR clarity, intent precision,
        RAG similarity scores, and weather data availability.
        """
        # 1. ASR Component (weight: 0.2)
        asr_notes = asr_data.get("asr_uncertainty_notes", [])
        asr_score = 1.0 - (len(asr_notes) * 0.2)
        asr_score = max(0.2, min(1.0, asr_score))
        
        # 2. Intent Component (weight: 0.3)
        crop = intent_data.get("crop", "unknown").lower()
        symptoms = intent_data.get("symptoms", [])
        
        crop_score = 1.0 if crop != "unknown" and crop != "" else 0.3
        symptoms_score = 1.0 if len(symptoms) > 0 else 0.5
        intent_score = (crop_score * 0.6) + (symptoms_score * 0.4)
        
        # 3. RAG Component (weight: 0.4)
        chunks = rag_data.get("retrieved_chunks", [])
        if chunks:
            # Take max similarity score of retrieved chunks
            rag_score = max([c.get("relevance_score", 0.0) for c in chunks])
        else:
            rag_score = 0.2
            
        # 4. Weather Component (weight: 0.1)
        simulated = weather_data.get("raw_data", {}).get("simulated", False)
        if not weather_data:
            weather_score = 0.2
        elif simulated:
            weather_score = 0.8
        else:
            weather_score = 1.0
            
        # Weighted Average calculation
        total_score = (asr_score * 0.20) + (intent_score * 0.30) + (rag_score * 0.40) + (weather_score * 0.10)
        total_score = round(max(0.0, min(1.0, total_score)), 2)
        
        # Deduct if manual corrections/safety warnings are triggered
        if intent_data.get("human_review_triggered"):
            # Flagged cases have lower confidence automatically
            total_score = max(0.4, round(total_score * 0.85, 2))
            
        rubric = {
            "asr_score": round(asr_score, 2),
            "intent_score": round(intent_score, 2),
            "rag_score": round(rag_score, 2),
            "weather_score": round(weather_score, 2),
            "system_confidence_score": total_score
        }
        
        logger.info(f"System confidence calculated: {rubric}")
        return rubric
