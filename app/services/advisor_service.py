# app/services/advisor_service.py
import json
import logging
from typing import Dict, Any, List
from app.config.prompts import AGRICULTURAL_ADVISOR_PROMPT
from app.services.llm_provider_service import LLMProviderService

logger = logging.getLogger(__name__)

class AdvisorService:
    def __init__(self, llm_provider: LLMProviderService = None):
        self.llm_provider = llm_provider or LLMProviderService()

    def get_seasonal_context(self, district: str, temp: float, humidity: float, rainfall: float) -> Dict[str, Any]:
        import datetime
        month = datetime.datetime.now().month
        
        # Determine season based on standard Bangladesh crop seasons
        if month in [11, 12, 1, 2]:
            season = "Rabi (Winter / রবি)"
        elif month in [3, 4, 5, 6]:
            season = "Kharif-I (Summer / খরিপ-১)"
        else:
            season = "Kharif-II (Monsoon / খরিপ-২)"
            
        regional_risks = []
        threats = []
        pests = []
        
        if month in [11, 12, 1, 2]:
            regional_risks.append("Late Blight of Tomato (টমেটোর লেট ব্লাইট)")
            regional_risks.append("Powdery Mildew (পাউডারি মিলডিউ)")
            pests.append("Aphids (জাব পোকা)")
            pests.append("Cutworms (কাটুই পোকা)")
            if temp < 18 and humidity > 85:
                threats.append("Dense fog causing fungal outbreaks (ঘন কুয়াশার কারণে ছত্রাকের আক্রমণ)")
        elif month in [3, 4, 5, 6]:
            regional_risks.append("Stem Rot of Jute (পাটের কাণ্ড পচা)")
            pests.append("Jute Hairy Caterpillar (পাটের বিছা পোকা)")
            pests.append("Yellow Mite (হলুদ মাকড়)")
            if temp > 32:
                threats.append("Heat stress and drought (তীব্র গরম ও অনাবৃষ্টির ঝুঁকি)")
        else:
            regional_risks.append("Rice Blast (ধানের ব্লাস্ট রোগ)")
            regional_risks.append("Bacterial Leaf Blight (ব্যাকটেরিয়াল লিফ ব্লাইট)")
            pests.append("Brown Planthopper (বাদামী গাছ ফড়িং / কারেন্ট পোকা)")
            pests.append("Rice Stem Borer (ধানের মাজরা পোকা)")
            if rainfall > 5.0 or humidity > 85:
                threats.append("Waterlogging and flooding risks (জলাবদ্ধতা ও আকস্মিক বন্যার ঝুঁকি)")
                
        district_clean = district.lower() if district else "dhaka"
        if "sylhet" in district_clean or "sunamganj" in district_clean:
            threats.append("Flash floods in Haor region (হাওর অঞ্চলে আকস্মিক বন্যা)")
        elif "rajshahi" in district_clean or "barind" in district_clean:
            threats.append("Drought and water scarcity (খরা ও ভূগর্ভস্থ পানির সংকট)")
        elif "barisal" in district_clean or "bagerhat" in district_clean:
            threats.append("Salinity intrusion and cyclone storm surges (লবণাক্ততা বৃদ্ধি ও জোয়ারের পানি বৃদ্ধি)")
            
        return {
            "crop_season": season,
            "regional_disease_risks": regional_risks,
            "rainfall_threats": threats,
            "seasonal_pests": pests
        }

    def generate_advice(
        self,
        farmer_query: str,
        intent_data: Dict[str, Any],
        weather_data: Dict[str, Any],
        rag_data: Dict[str, Any],
        history_context: str = ""
    ) -> Dict[str, Any]:
        """
        Coordinates full context and queries the LLM to generate localized Bangla agricultural advice
        along with details for competition judges.
        """
        logger.info("Generating agricultural advice using context...")
        
        # Calculate seasonal/regional context
        temp = weather_data.get("temp", 28.0)
        humidity = weather_data.get("humidity", 70.0)
        rainfall = weather_data.get("rainfall", 0.0)
        district = weather_data.get("resolved_district", "Dhaka")
        seasonal_ctx = self.get_seasonal_context(district, temp, humidity, rainfall)
        
        # Format RAG chunks
        chunks = rag_data.get("retrieved_chunks", [])
        if chunks:
            rag_context = "\n---\n".join([
                f"Source: {c.get('source_name', 'Unknown')}\n"
                f"Crop: {c.get('crop', 'general')}\n"
                f"Content: {c.get('text', '')}"
                for c in chunks
            ])
        else:
            rag_context = "No direct matching segments found in vector store. Rely on standard agronomy principles for Bangladesh."

        # Format system instruction and parameters
        try:
            formatted_instruction = AGRICULTURAL_ADVISOR_PROMPT.format(
                farmer_query=farmer_query,
                intent_json=json.dumps(intent_data, ensure_ascii=False),
                weather_json=json.dumps(weather_data, ensure_ascii=False),
                seasonal_context=json.dumps(seasonal_ctx, ensure_ascii=False),
                history_context=history_context or "No previous turns.",
                rag_context=rag_context
            )
        except Exception as e:
            logger.error(f"Failed to format advisor prompt template: {e}")
            formatted_instruction = AGRICULTURAL_ADVISOR_PROMPT
            
        try:
            result = self.llm_provider.generate_json(
                system_instruction=formatted_instruction,
                user_prompt=f"Please provide standard diagnosis and recommendation."
            )
            
            # Post-processing checks and defaults validation
            keys = [
                "diagnosis_title", "likely_problem", "confidence_score", "risk_level",
                "bangla_recommendation", "english_summary", "immediate_actions",
                "what_to_avoid", "human_review_required", "human_review_reasons",
                "uncertainty_explanation", "source_documents_used", "weather_factors_used",
                "reasoning_summary_for_judges"
            ]
            for key in keys:
                if key not in result:
                    if key == "immediate_actions" or key == "what_to_avoid" or key == "human_review_reasons" or key == "source_documents_used" or key == "weather_factors_used":
                        result[key] = []
                    elif key == "human_review_required":
                        result[key] = False
                    elif key == "confidence_score":
                        result[key] = 0.5
                    else:
                        result[key] = "unknown"
                        
            # Force safety: if crop intent triggered human review, enforce in final output
            if intent_data.get("human_review_triggered"):
                result["human_review_required"] = True
                for r in intent_data.get("human_review_reasons", []):
                    if r not in result["human_review_reasons"]:
                        result["human_review_reasons"].append(r)
                        
            # Force safety: if confidence is extremely low (< 0.6), trigger human review
            try:
                score = float(result["confidence_score"])
                if score < 0.6:
                    result["human_review_required"] = True
                    reason = "low_confidence_score"
                    if reason not in result["human_review_reasons"]:
                        result["human_review_reasons"].append(reason)
            except Exception:
                pass
                
            # Attach seasonal context
            result["seasonal_context"] = seasonal_ctx
            return result
            
        except Exception as e:
            logger.error(f"Failed in generate_advice service: {e}")
            return {
                "diagnosis_title": "ত্রুটি ঘটেছে",
                "likely_problem": "system_error",
                "confidence_score": 0.0,
                "risk_level": "high",
                "bangla_recommendation": "দুঃখিত, অভ্যন্তরীণ ত্রুটির কারণে পরামর্শ তৈরি করা সম্ভব হয়নি। জমিতে নতুন কোনো কীটনাশক ছিটানো বন্ধ রাখুন এবং স্থানীয় কৃষি কর্মকর্তার সাথে যোগাযোগ করুন।",
                "english_summary": "System error prevented advice formulation.",
                "immediate_actions": ["স্থানীয় কৃষি উপ-সহকারী কর্মকর্তার সাহায্য নিন।"],
                "what_to_avoid": ["পরামর্শ ছাড়া রাসায়নিক প্রয়োগ করবেন না।"],
                "human_review_required": True,
                "human_review_reasons": ["system_error_occurred"],
                "uncertainty_explanation": str(e),
                "source_documents_used": [],
                "weather_factors_used": [],
                "reasoning_summary_for_judges": f"Advisory generation caught exception: {str(e)}",
                "seasonal_context": seasonal_ctx
            }
