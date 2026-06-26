import json
import logging
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    genai = None

from app.config.settings import Config

logger = logging.getLogger(__name__)

class GeminiService:
    def __init__(self):
        self.api_key = Config.GEMINI_API_KEY
        if self.api_key and GEMINI_AVAILABLE:
            genai.configure(api_key=self.api_key)
            self.model_flash = genai.GenerativeModel("gemini-2.0-flash")
            logger.info("Gemini Service initialized successfully.")
        else:
            logger.warning("GEMINI_API_KEY not found or google-generativeai module unavailable. Gemini Service will operate in offline/mock mode.")
            self.model_flash = None

    def correct_asr(self, raw_transcript: str) -> dict:
        """
        Repair ASR mistakes, Banglish, and regional dialects to clean Bangla, 
        and translate to English.
        """
        if not raw_transcript:
            return {"corrected_bangla": "", "english_translation": ""}

        if not self.model_flash:
            # Mock fallback if key is missing
            return {
                "corrected_bangla": raw_transcript,
                "english_translation": "Mock translation: " + raw_transcript
            }

        prompt = f"""
        You are a linguistics expert specializing in Bengali dialects, Banglish (Bengali written in English letters), and Automatic Speech Recognition (ASR) error correction.
        
        Task: Analyze the following raw voice transcript from a Bangladeshi farmer. Repair any typos, slang, ASR artifacts, regional dialects, or Banglish spelling to standard, polite agricultural Bengali. Also provide a direct English translation of their query.
        
        Raw Transcript: "{raw_transcript}"
        
        Output format must be JSON matching this exact structure:
        {{
            "corrected_bangla": "Standard clean Bengali text here",
            "english_translation": "Direct English translation of the farmer's problem"
        }}
        """
        try:
            response = self.model_flash.generate_content(
                prompt,
                generation_config={"response_mime_type": "application/json"}
            )
            data = json.loads(response.text)
            logger.info(f"ASR correction completed. Corrected: {data.get('corrected_bangla')}")
            return data
        except Exception as e:
            logger.error(f"Error in correct_asr: {e}")
            return {
                "corrected_bangla": raw_transcript,
                "english_translation": f"Failed to translate: {raw_transcript}"
            }

    def extract_intent(self, corrected_bangla: str) -> dict:
        """
        Extract agricultural metadata from the query: crop, symptoms, severity, urgency.
        """
        if not corrected_bangla:
            return {"crop": "Unknown", "symptoms": "None", "severity": "Medium", "urgency": "Medium"}

        if not self.model_flash:
            # Mock fallback
            return {"crop": "Rice", "symptoms": "Yellowing leaves", "severity": "Medium", "urgency": "Medium"}

        prompt = f"""
        You are an AI agricultural classifier. Extract key metadata from this farmer query:
        
        Farmer Query: "{corrected_bangla}"
        
        Identify:
        1. Crop: Rice (ধান), Wheat (গম), Tomato (টমেটো), Jute (পাট), Vegetables (সবজি), Poultry (মুরগি), Fisheries (মাছ), or Other.
        2. Symptoms: What physical damage, discoloration, or issues are observed.
        3. Severity: Estimate based on symptoms (Low, Medium, High, Critical).
        4. Urgency: Estimate speed of intervention required (Low, Medium, High, Critical).
        
        Output format must be JSON matching this exact structure:
        {{
            "crop": "English Crop Name",
            "symptoms": "Brief description of symptoms in English",
            "severity": "Low/Medium/High/Critical",
            "urgency": "Low/Medium/High/Critical"
        }}
        """
        try:
            response = self.model_flash.generate_content(
                prompt,
                generation_config={"response_mime_type": "application/json"}
            )
            data = json.loads(response.text)
            logger.info(f"Intent extraction completed: {data}")
            return data
        except Exception as e:
            logger.error(f"Error in extract_intent: {e}")
            return {"crop": "Unknown", "symptoms": "None", "severity": "Medium", "urgency": "Medium"}

    def generate_advice(self, farmer_query: str, crop_context: dict, weather_data: dict, RAG_docs: list) -> dict:
        """
        Generate localized Bangla recommendations using RAG and weather context.
        """
        if not self.model_flash:
            # Mock advice for offline testing
            return {
                "recommendation_bangla": "দুঃখিত, বর্তমানে এআই পরামর্শক অফলাইন আছে। অনুগ্রহ করে আপনার ধানের ক্ষেত নিয়মিত পর্যবেক্ষণ করুন এবং কোনো রাসায়নিক ছিটানোর আগে কৃষি কর্মকর্তার পরামর্শ নিন।",
                "judge_mode": {
                    "weather_factors_used": "Weather data is unavailable in offline mock mode.",
                    "retrieved_documents_used": ["Offline fallback documentation"],
                    "ai_confidence_score": 0.5,
                    "reasoning_summary": "Offline system fallback used."
                }
            }

        # Build context strings
        docs_context = "\n---\n".join([f"Source: {doc['metadata'].get('source', 'Unknown')}\nContent: {doc['text']}" for doc in RAG_docs])
        if not docs_context:
            docs_context = "No specific reference documents found. Rely on standard guidelines for Bangladesh agriculture."

        weather_str = f"Temperature: {weather_data.get('temp', 25)}C, Humidity: {weather_data.get('humidity', 80)}%, Rainfall: {weather_data.get('rainfall', 0)}mm. Forecast: {', '.join(weather_data.get('forecast', []))}"
        
        # System guidelines
        system_role = """
        You are KrishiKantho AI. You are a professional agricultural advisor specializing in Bangladeshi agriculture (Rice, Wheat, Tomato, Jute, Vegetables, Poultry, Fisheries).
        
        Your response rules:
        1. Use simple, polite, encouraging Bangla language.
        2. Give practical, localized recommendations suitable for smallholder farmers.
        3. Avoid overly complex scientific/technical jargon. Use terms farmers understand.
        4. Never invent specific chemical pesticide dosages. Recommend consulting local dealers or agricultural officers for dosage if necessary.
        5. Explain any uncertainty in your diagnosis.
        6. Always mention when a physical inspection by a human sub-district agricultural officer (Sub-Assistant Agriculture Officer / SAAO) is recommended.
        """
        
        prompt = f"""
        {system_role}
        
        Inputs for diagnosis:
        - Farmer's Query: "{farmer_query}"
        - Extracted Crop Context: {json.dumps(crop_context)}
        - Weather Context: "{weather_str}"
        - Scientific Knowledge Context (RAG):
        {docs_context}
        
        Task: 
        1. Formulate a direct, compassionate, actionable advice in Bangla for the farmer.
        2. Create a "Why This Recommendation?" explanation for the competition judges. Evaluate how weather conditions (like humidity causing fungal growth) and retrieved guidelines influence the advice. Assess your confidence score (0.0 to 1.0) and write a reasoning summary in English.
        
        Output format must be JSON matching this exact structure:
        {{
            "recommendation_bangla": "Detailed and simple response for the farmer in Bangla. Include weather-related crop protection tips.",
            "judge_mode": {{
                "weather_factors_used": "Detailed description in English of which weather parameters were analyzed and why they matter for this crop issue.",
                "retrieved_documents_used": ["List of sources/documents/guidelines used from the vector store"],
                "ai_confidence_score": 0.85,
                "reasoning_summary": "Concise summary in English outlining the diagnosis logic, document correlation, and uncertainty bounds."
            }}
        }}
        """
        try:
            response = self.model_flash.generate_content(
                prompt,
                generation_config={"response_mime_type": "application/json"}
            )
            data = json.loads(response.text)
            logger.info("Advice generation complete.")
            return data
        except Exception as e:
            logger.error(f"Error in generate_advice: {e}")
            return {
                "recommendation_bangla": "দুঃখিত, পরামর্শ তৈরির সময় ত্রুটি ঘটেছে। অনুগ্রহ করে আবার চেষ্টা করুন।",
                "judge_mode": {
                    "weather_factors_used": "Error processing weather factors",
                    "retrieved_documents_used": [],
                    "ai_confidence_score": 0.0,
                    "reasoning_summary": f"Exception occurred: {str(e)}"
                }
            }
