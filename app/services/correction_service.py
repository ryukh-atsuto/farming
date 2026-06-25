# app/services/correction_service.py
import logging
from typing import Dict, Any
from app.config.prompts import ASR_CORRECTION_PROMPT
from app.services.llm_provider_service import LLMProviderService

logger = logging.getLogger(__name__)

class CorrectionService:
    def __init__(self, llm_provider: LLMProviderService = None):
        self.llm_provider = llm_provider or LLMProviderService()

    def correct(self, raw_transcript: str) -> Dict[str, Any]:
        """
        Repairs grammar, dialect, spelling, and ASR errors.
        Translates text to English for cross-reference.
        """
        if not raw_transcript or not raw_transcript.strip():
            return {
                "raw_transcript": "",
                "corrected_bangla": "",
                "english_translation": "",
                "detected_language_style": "standard_bangla",
                "asr_uncertainty_notes": []
            }

        logger.info(f"Correcting ASR transcription: '{raw_transcript}'")
        try:
            result = self.llm_provider.generate_json(
                system_instruction=ASR_CORRECTION_PROMPT,
                user_prompt=f"Raw Transcript: \"{raw_transcript}\""
            )
            # Validate output keys
            if "corrected_bangla" not in result:
                # If mock returns advisor payload, extract it
                if "corrected_bangla" in result:
                    pass
                else:
                    result["corrected_bangla"] = raw_transcript
            if "english_translation" not in result:
                result["english_translation"] = f"Translation fallback: {raw_transcript}"
            if "detected_language_style" not in result:
                result["detected_language_style"] = "unknown"
            if "asr_uncertainty_notes" not in result:
                result["asr_uncertainty_notes"] = []
                
            return result
        except Exception as e:
            logger.error(f"Error in CorrectionService: {e}")
            return {
                "raw_transcript": raw_transcript,
                "corrected_bangla": raw_transcript,
                "english_translation": f"Fallback: {raw_transcript}",
                "detected_language_style": "mixed",
                "asr_uncertainty_notes": [f"Error occurred during correction: {str(e)}"]
            }
        
    def get_simple_rule_based_correction(self, raw_text: str) -> str:
        """Helper for extremely fast local rule-based translation checks."""
        # Simple dictionary for common Banglish agricultural terms
        mappings = {
            "dhan": "ধান",
            "dhaner": "ধানের",
            "pata": "পাতা",
            "patay": "পাতায়",
            "pacha": "পচা",
            "rok": "রোগ",
            "poka": "পোকা",
            "holud": "হলুদ",
            "badami": "বাদামী",
            "daag": "দাগ",
            "tomato": "টমেটো",
            "jute": "পাট"
        }
        words = raw_text.lower().split()
        converted = [mappings.get(w, w) for w in words]
        return " ".join(converted)
