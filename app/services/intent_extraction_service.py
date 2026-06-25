# app/services/intent_extraction_service.py
import logging
from typing import Dict, Any
from app.config.prompts import INTENT_EXTRACTION_PROMPT
from app.services.llm_provider_service import LLMProviderService

logger = logging.getLogger(__name__)

class IntentExtractionService:
    def __init__(self, llm_provider: LLMProviderService = None):
        self.llm_provider = llm_provider or LLMProviderService()

    def extract(self, corrected_bangla: str) -> Dict[str, Any]:
        """
        Parses crop type, symptoms, plant parts, severity, and urgency.
        Triggers human review flag if severe issues are identified.
        """
        if not corrected_bangla or not corrected_bangla.strip():
            return {
                "crop": "unknown",
                "symptoms": [],
                "affected_parts": [],
                "severity": "unknown",
                "urgency": "unknown",
                "location_text": "",
                "farmer_intent": "",
                "suspected_problem_type": "unknown",
                "human_review_triggered": False,
                "human_review_reasons": []
            }

        logger.info(f"Extracting intent from query: '{corrected_bangla}'")
        try:
            result = self.llm_provider.generate_json(
                system_instruction=INTENT_EXTRACTION_PROMPT,
                user_prompt=f"Farmer Query: \"{corrected_bangla}\""
            )
            
            # Clean structure and normalize keys
            keys = [
                "crop", "symptoms", "affected_parts", "severity", "urgency",
                "location_text", "farmer_intent", "suspected_problem_type",
                "human_review_triggered", "human_review_reasons"
            ]
            for key in keys:
                if key not in result:
                    if key == "symptoms" or key == "affected_parts" or key == "human_review_reasons":
                        result[key] = []
                    elif key == "human_review_triggered":
                        result[key] = False
                    else:
                        result[key] = "unknown"
                        
            # Normalize crop name string
            result["crop"] = str(result["crop"]).lower().strip()
            
            return result
        except Exception as e:
            logger.error(f"Error in IntentExtractionService: {e}")
            return {
                "crop": "unknown",
                "symptoms": [],
                "affected_parts": [],
                "severity": "unknown",
                "urgency": "unknown",
                "location_text": "",
                "farmer_intent": "General agricultural advisory requested",
                "suspected_problem_type": "unknown",
                "human_review_triggered": True,
                "human_review_reasons": [f"Failed to analyze query: {str(e)}"]
            }
