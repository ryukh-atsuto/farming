# app/services/demo_service.py
import logging
import time
from typing import Dict, Any, List
from app.repositories.demo_scenario_store import DemoScenarioStore
from app.repositories.conversation_store import ConversationStoreRepository
from app.services.correction_service import CorrectionService
from app.services.intent_extraction_service import IntentExtractionService
from app.services.rag_service import RAGService
from app.services.weather_service import WeatherService
from app.services.advisor_service import AdvisorService
from app.services.confidence_service import ConfidenceService
from app.services.human_review_service import HumanReviewService
from app.services.tts_service import TTSService

logger = logging.getLogger(__name__)

class DemoService:
    def __init__(
        self,
        scenario_store: DemoScenarioStore = None,
        conversation_store: ConversationStoreRepository = None,
        correction_service: CorrectionService = None,
        intent_service: IntentExtractionService = None,
        rag_service: RAGService = None,
        weather_service: WeatherService = None,
        advisor_service: AdvisorService = None,
        confidence_service: ConfidenceService = None,
        human_review_service: HumanReviewService = None,
        tts_service: TTSService = None
    ):
        self.scenario_store = scenario_store or DemoScenarioStore()
        self.conversation_store = conversation_store or ConversationStoreRepository()
        self.correction_service = correction_service or CorrectionService()
        self.intent_service = intent_service or IntentExtractionService()
        self.rag_service = rag_service or RAGService()
        self.weather_service = weather_service or WeatherService()
        self.advisor_service = advisor_service or AdvisorService()
        self.confidence_service = confidence_service or ConfidenceService()
        self.human_review_service = human_review_service or HumanReviewService()
        self.tts_service = tts_service or TTSService()

    def get_available_scenarios(self) -> List[Dict[str, Any]]:
        """Returns all configured scenarios with titles and icons."""
        return self.scenario_store.get_scenarios()

    def execute_scenario(self, scenario_id: str, district: str = None) -> Dict[str, Any]:
        """
        Executes a pre-defined scenario, running each step of the pipeline.
        Saves resulting context in the conversation history vector/DB.
        """
        t_start = time.perf_counter()
        logger.info(f"Executing demo scenario '{scenario_id}'...")
        scenario = self.scenario_store.get_scenario_by_id(scenario_id)
        if not scenario:
            raise ValueError(f"Scenario ID '{scenario_id}' not found.")

        # Extract basic parameters
        raw_transcript = scenario["raw_transcript"]
        
        # Simulate STT latency (voice interface) since we read from text
        stt_latency = 1150
        
        # Step 1: ASR correction and English translation
        t_corr_start = time.perf_counter()
        asr_result = self.correction_service.correct(raw_transcript)
        correction_latency = int((time.perf_counter() - t_corr_start) * 1000)
        
        # Step 2: Intent extraction
        t_intent_start = time.perf_counter()
        intent_result = self.intent_service.extract(asr_result["corrected_bangla"])
        intent_latency = int((time.perf_counter() - t_intent_start) * 1000)
        
        # Step 3: Localized weather lookup (using custom coordinates or scenario coordinates)
        # Coordinate selection: Prioritize district coordinates if user selected a custom district
        t_weather_start = time.perf_counter()
        lat = scenario.get("lat", 23.8103)
        lon = scenario.get("lon", 90.4125)
        
        if district:
            # Dynamically fetch coordinates for selected district
            from app.services.weather_service import WeatherService
            ws = WeatherService()
            weather = ws.get_weather_by_district(district)
        else:
            weather = self.weather_service.get_weather_by_coords(lat, lon)
            
        weather_dict = weather.to_dict()
        weather_latency = int((time.perf_counter() - t_weather_start) * 1000)

        # Step 4: RAG search using crop metadata + symptoms
        t_rag_start = time.perf_counter()
        rag_result = self.rag_service.query_knowledge(
            query_text=asr_result["corrected_bangla"],
            crop=intent_result.get("crop"),
            symptoms=intent_result.get("symptoms"),
            english_translation=asr_result.get("english_translation")
        )
        rag_docs = rag_result.get("retrieved_chunks", [])
        rag_latency = int((time.perf_counter() - t_rag_start) * 1000)

        # Step 5: AI Advisor Recommendation
        t_adv_start = time.perf_counter()
        advisor_result = self.advisor_service.generate_advice(
            farmer_query=asr_result["corrected_bangla"],
            intent_data=intent_result,
            weather_data=weather_dict,
            rag_data=rag_result
        )
        advisor_latency = int((time.perf_counter() - t_adv_start) * 1000)

        # Step 6: Confidence Calculations
        confidence_result = self.confidence_service.calculate_confidence(
            asr_data=asr_result,
            intent_data=intent_result,
            rag_data=rag_result,
            weather_data=weather_dict
        )
        
        # Ensure calculated confidence is reflected in advisor result
        advisor_result["confidence_score"] = confidence_result["system_confidence_score"]

        # Step 7: Human Review Audit Check
        review_case = self.human_review_service.evaluate(
            conversation_id=scenario_id,
            confidence_score=confidence_result["system_confidence_score"],
            intent_data=intent_result,
            advisor_data=advisor_result
        )
        badge = self.human_review_service.get_badge_metadata(
            case=review_case,
            confidence_score=confidence_result["system_confidence_score"]
        )

        # Step 8: TTS Audio Synthesis
        t_tts_start = time.perf_counter()
        recommendation_audio_url = ""
        tts_failed = False
        
        from app.config.settings import Config
        if not Config.USE_MOCK_TTS:
            try:
                recommendation_audio_url = self.tts_service.synthesize(
                    advisor_result.get("bangla_recommendation", ""), 
                    voice_gender="female"
                )
                if not recommendation_audio_url or getattr(self.tts_service, "last_synthesis_method", "") in ["failed", "mock_fallback", "gtts"]:
                    tts_failed = True
            except Exception as e:
                logger.error(f"Live TTS synthesis failed: {e}")
                tts_failed = True
        else:
            tts_failed = True
            
        if tts_failed:
            logger.info("Live TTS is disabled or failed; falling back to scenario-specific pre-recorded response audio.")
            recommendation_audio_url = scenario.get("response_audio_url", "")
            
        tts_latency = int((time.perf_counter() - t_tts_start) * 1000)
        
        total_latency = int((time.perf_counter() - t_start) * 1000) + stt_latency

        # Estimate tokens
        rag_context_len = sum(len(c.get("text", "")) for c in rag_docs)
        input_token_count = (len(asr_result["corrected_bangla"]) + rag_context_len) // 4
        output_token_count = len(advisor_result.get("bangla_recommendation", "")) // 4

        stage_status = {
            "stt": "executed",
            "correction": "mock_fallback" if Config.USE_MOCK_LLM else "executed",
            "weather": "executed",
            "intent": "mock_fallback" if Config.USE_MOCK_LLM else "executed",
            "rag": "executed",
            "advisor": "mock_fallback" if Config.USE_MOCK_LLM else "executed",
            "tts": "mock_fallback" if (Config.USE_MOCK_TTS or tts_failed) else "executed"
        }

        metrics = {
            "stt_latency_ms": stt_latency,
            "correction_latency_ms": correction_latency,
            "intent_latency_ms": intent_latency,
            "weather_latency_ms": weather_latency,
            "rag_latency_ms": rag_latency,
            "advisor_latency_ms": advisor_latency,
            "tts_latency_ms": tts_latency,
            "total_latency_ms": total_latency,
            "input_token_count": input_token_count,
            "output_token_count": output_token_count,
            "retrieved_doc_count": len(rag_docs),
            "stage_status": stage_status
        }

        # Save result into conversation history database
        payload = {
            "conversation_id": scenario_id,
            "raw_transcript": raw_transcript,
            "asr_corrected": asr_result,
            "intent": intent_result,
            "weather": weather_dict,
            "rag": rag_result,
            "advisor": advisor_result,
            "confidence": confidence_result,
            "badge": badge,
            "district": district or "Dhaka",
            "audio_metadata": {
                "duration": 5.0,
                "sample_rate": 16000,
                "channels": 1
            },
            "recommendation_audio_url": recommendation_audio_url,
            "metrics": metrics,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        }
        
        try:
            self.conversation_store.save_history(scenario_id, payload)
            logger.info(f"Demo scenario '{scenario_id}' results persisted to database.")
        except Exception as e:
            logger.error(f"Failed to persist history: {e}")

        return payload
