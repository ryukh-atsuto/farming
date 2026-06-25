# app/services/llm_provider_service.py
import json
import logging
import requests
import google.generativeai as genai
from typing import Dict, Any, Optional
from app.config.settings import Config

logger = logging.getLogger(__name__)

class LLMProviderService:
    def __init__(self):
        self.gemini_key = Config.GEMINI_API_KEY
        self.hf_token = Config.HF_TOKEN
        self.use_mock = Config.USE_MOCK_LLM

        # Init Gemini
        self.gemini_model = None
        if self.gemini_key and not self.use_mock:
            try:
                genai.configure(api_key=self.gemini_key)
                self.gemini_model = genai.GenerativeModel("gemini-1.5-flash")
                logger.info("LLM Provider: Gemini initialized successfully.")
            except Exception as e:
                logger.error(f"LLM Provider: Failed to init Gemini: {e}")

    def generate_json(self, system_instruction: str, user_prompt: str) -> Dict[str, Any]:
        """Generates content via Gemini, HF, or offline mock, strictly returning JSON."""
        # 1. Try Gemini
        if self.gemini_model:
            try:
                full_prompt = f"{system_instruction}\n\nUser Input:\n{user_prompt}"
                response = self.gemini_model.generate_content(
                    full_prompt,
                    generation_config={"response_mime_type": "application/json"}
                )
                if response.text:
                    return json.loads(response.text.strip())
            except Exception as e:
                logger.error(f"LLM Provider: Gemini inference failed: {e}. Trying fallback.")

        # 2. Try Hugging Face Inference API
        if self.hf_token and not self.use_mock:
            try:
                url = "https://api-inference.huggingface.co/models/Qwen/Qwen2.5-72B-Instruct"
                headers = {"Authorization": f"Bearer {self.hf_token}"}
                payload = {
                    "inputs": f"<|im_start|>system\n{system_instruction}<|im_end|>\n<|im_start|>user\n{user_prompt}<|im_end|>\n<|im_start|>assistant\n",
                    "parameters": {"max_new_tokens": 1000, "return_full_text": False}
                }
                res = requests.post(url, json=payload, headers=headers, timeout=10)
                if res.status_code == 200:
                    resp_data = res.json()
                    text = ""
                    if isinstance(resp_data, list) and len(resp_data) > 0:
                        text = resp_data[0].get("generated_text", "")
                    elif isinstance(resp_data, dict):
                        text = resp_data.get("generated_text", "")

                    # Extract JSON from generated text
                    json_match = self._extract_json(text)
                    if json_match:
                        return json_match
            except Exception as e:
                logger.error(f"LLM Provider: HF inference failed: {e}. Trying local rule-based mock.")

        # 3. Offline Rule-based Mock / Demo Fallback
        logger.info("LLM Provider: Utilizing offline rule-based mock.")
        return self._mock_reasoning_fallback(user_prompt)

    def _extract_json(self, text: str) -> Optional[Dict[str, Any]]:
        """Safely extracts JSON from markdown or raw strings."""
        text = text.strip()
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # Try regex or block parsing
        try:
            start = text.find("{")
            end = text.rfind("}")
            if start != -1 and end != -1:
                return json.loads(text[start:end+1])
        except Exception:
            pass
        return None

    def _mock_reasoning_fallback(self, user_prompt: str) -> Dict[str, Any]:
        """Provides a simple rule-based mock analyzer matching terms in user_prompt."""
        prompt_lower = user_prompt.lower()
        
        # Determine scenario
        if "বাদামী" in prompt_lower or "brown" in prompt_lower or "leaf spot" in prompt_lower:
            from app.repositories.demo_scenario_store import DEFAULT_SCENARIOS
            scenario = DEFAULT_SCENARIOS["rice_brown_leaf_spot"]
        elif "গিট" in prompt_lower or "blast" in prompt_lower or "ব্লাস্ট" in prompt_lower:
            from app.repositories.demo_scenario_store import DEFAULT_SCENARIOS
            scenario = DEFAULT_SCENARIOS["rice_blast"]
        elif "কোকড়ানো" in prompt_lower or "curl" in prompt_lower or "কুচকে" in prompt_lower:
            from app.repositories.demo_scenario_store import DEFAULT_SCENARIOS
            scenario = DEFAULT_SCENARIOS["tomato_leaf_curl"]
        elif "কাণ্ড" in prompt_lower or "পচা" in prompt_lower or "rot" in prompt_lower:
            from app.repositories.demo_scenario_store import DEFAULT_SCENARIOS
            scenario = DEFAULT_SCENARIOS["jute_stem_rot"]
        else:
            # General generic fallback
            scenario = {
                "raw_transcript": user_prompt,
                "corrected_bangla": user_prompt,
                "english_translation": "General crop leaf issue query.",
                "crop": "unknown",
                "symptoms": ["unknown spot"],
                "severity": "medium",
                "urgency": "normal",
                "weather_factors_used": ["Default weather values used."],
                "diagnosis_title": "অনির্ণীত শস্য সমস্যা",
                "likely_problem": "General agricultural stress",
                "confidence_score": 0.5,
                "risk_level": "medium",
                "bangla_recommendation": "কৃষক ভাই, আপনার শস্যের সমস্যাটি সুনির্দিষ্টভাবে নির্ণয় করা সম্ভব হয়নি। অনুগ্রহ করে জমিতে অতিরিক্ত ইউরিয়া ছিটানো বন্ধ রাখুন, নিষ্কাশন ব্যবস্থা পরীক্ষা করুন এবং নিকটস্থ কৃষি কর্মকর্তার সাথে যোগাযোগ করুন। সঠিক কীটনাশকের মাত্রার জন্য পরামর্শ নিন।",
                "english_summary": "Unresolved crop problem. Recommended balanced water management and consultation with local block supervisors.",
                "immediate_actions": ["জমির পানি নিষ্কাশন ব্যবস্থা উন্নত করুন।", "কৃষি কর্মকর্তার পরামর্শ নিন।"],
                "what_to_avoid": ["অতিরিক্ত রাসায়নিক স্প্রে করা থেকে বিরত থাকুন।"],
                "human_review_required": True,
                "human_review_reasons": ["unsupported_crop_or_symptom_complexity"],
                "uncertainty_explanation": "লক্ষণগুলো অস্পষ্ট হওয়ায় এআই সুনির্দিষ্ট পরামর্শ দিতে পারেনি।",
                "source_documents_used": [],
                "reasoning_summary_for_judges": "Default fallback triggered due to missing keyword match."
            }
        
        return scenario
