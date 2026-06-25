# app/controllers/diagnosis_controller.py
import logging
import time
from flask import Blueprint, request, jsonify
from app.models.diagnosis import Diagnosis
from app.models.conversation import Conversation
from app.repositories.conversation_store import ConversationStoreRepository

from app.services.audio_preprocessing_service import AudioPreprocessingService
from app.services.stt_service import STTService
from app.services.correction_service import CorrectionService
from app.services.intent_extraction_service import IntentExtractionService
from app.services.rag_service import RAGService
from app.services.weather_service import WeatherService
from app.services.location_service import LocationService
from app.services.tts_service import TTSService
from app.services.advisor_service import AdvisorService
from app.services.confidence_service import ConfidenceService
from app.services.human_review_service import HumanReviewService

logger = logging.getLogger(__name__)

diagnosis_bp = Blueprint("diagnosis", __name__)

# Initialize decoupled services
audio_preprocess_service = AudioPreprocessingService()
stt_service = STTService()
correction_service = CorrectionService()
intent_service = IntentExtractionService()
rag_service = RAGService()
weather_service = WeatherService()
location_service = LocationService()
tts_service = TTSService()
advisor_service = AdvisorService()
confidence_service = ConfidenceService()
human_review_service = HumanReviewService()

conversation_store = ConversationStoreRepository()

@diagnosis_bp.route("/api/diagnose", methods=["POST"])
def diagnose_crop():
    """
    Main diagnostic entry point.
    Coordinates audio preprocessing, speech transcription, correction, intent analysis,
    weather parameters retrieval, RAG documents query, AI advisor advice, confidence assessment,
    human review triggers, and TTS audio synthesis.
    """
    t_start = time.perf_counter()
    data = request.get_json() or {}
    audio_path = data.get("audio_path")
    text_query = data.get("text_query")
    lat = data.get("lat")
    lon = data.get("lon")
    district = data.get("district")

    if not audio_path and not text_query:
        return jsonify({"error": "No voice recording or text query provided."}), 400

    try:
        # Step 1: Preprocessing & Transcription (ASR) if audio is supplied
        original_transcript = ""
        audio_metadata = {}
        stt_latency = 0
        
        if audio_path:
            t_stt_start = time.perf_counter()
            logger.info(f"Pipeline: Preprocessing audio: {audio_path}")
            audio_job = audio_preprocess_service.preprocess(audio_path)
            if audio_job.status == "failed":
                return jsonify({"error": f"Audio processing failed: {audio_job.error_message}"}), 400
                
            audio_metadata = {
                "duration": audio_job.duration,
                "sample_rate": audio_job.sample_rate,
                "channels": audio_job.channels
            }
            
            logger.info("Pipeline: Transcribing audio...")
            original_transcript = stt_service.transcribe(audio_job.filepath)
            stt_latency = int((time.perf_counter() - t_stt_start) * 1000)
            if not original_transcript:
                # If local transcription returns empty, fallback/trigger match
                original_transcript = text_query or ""
                
            if not original_transcript:
                return jsonify({"error": "Failed to transcribe audio. Please record/speak clearly."}), 400
        else:
            original_transcript = text_query

        # Step 2: ASR dialect/error correction
        t_corr_start = time.perf_counter()
        asr_result = correction_service.correct(original_transcript)
        corrected_bangla = asr_result.get("corrected_bangla", original_transcript)
        english_translation = asr_result.get("english_translation", "")
        correction_latency = int((time.perf_counter() - t_corr_start) * 1000)

        # Step 3: Localized weather parameters
        t_weather_start = time.perf_counter()
        resolved_district = "Dhaka"
        weather_model = None

        if lat is not None and lon is not None:
            resolved_district = location_service.resolve_district(float(lat), float(lon))
            weather_model = weather_service.get_weather_by_coords(float(lat), float(lon))
        elif district:
            resolved_district = district.capitalize()
            weather_model = weather_service.get_weather_by_district(district)
        else:
            resolved_district = "Dhaka"
            coords = location_service.get_coords_for_district("Dhaka")
            weather_model = weather_service.get_weather_by_coords(coords["lat"], coords["lon"])

        weather_context = weather_model.to_dict()
        weather_context["resolved_district"] = resolved_district
        weather_latency = int((time.perf_counter() - t_weather_start) * 1000)

        # Step 4: Intent and parameters extraction
        t_intent_start = time.perf_counter()
        intent_result = intent_service.extract(corrected_bangla)
        crop = intent_result.get("crop", "unknown")
        symptoms = intent_result.get("symptoms", [])
        severity = intent_result.get("severity", "unknown")
        urgency = intent_result.get("urgency", "unknown")
        intent_latency = int((time.perf_counter() - t_intent_start) * 1000)

        # Step 5: Document Knowledge RAG retrieval
        t_rag_start = time.perf_counter()
        rag_result = rag_service.query_knowledge(
            query_text=corrected_bangla,
            crop=crop,
            symptoms=symptoms,
            english_translation=english_translation
        )
        rag_docs = rag_result.get("retrieved_chunks", [])
        rag_latency = int((time.perf_counter() - t_rag_start) * 1000)

        # Retrieve previous history if conversation_id is provided
        conversation_id = data.get("conversation_id")
        history_context = ""
        history_payload = None
        if conversation_id:
            history_payload = conversation_store.get_history_by_id(conversation_id)
            if history_payload:
                turns = history_payload.get("turns", [])
                if not turns and "raw_transcript" in history_payload:
                    # Upgrade legacy single-turn format
                    legacy_turn = {k: v for k, v in history_payload.items() if k != "turns"}
                    turns = [legacy_turn]
                
                history_parts = []
                for idx, t in enumerate(turns[-3:]):  # Use last 3 turns
                    history_parts.append(
                        f"Turn {idx+1}:\n"
                        f"Farmer: {t.get('raw_transcript', '')}\n"
                        f"AI Diagnosis: {t.get('advisor', {}).get('diagnosis_title', '')}\n"
                        f"AI Recommendation: {t.get('advisor', {}).get('bangla_recommendation', '')}"
                    )
                history_context = "\n\n".join(history_parts)

        # Step 6: AI Advisor response synthesis
        t_adv_start = time.perf_counter()
        advisor_result = advisor_service.generate_advice(
            farmer_query=corrected_bangla,
            intent_data=intent_result,
            weather_data=weather_context,
            rag_data=rag_result,
            history_context=history_context
        )
        recommendation_text = advisor_result.get("bangla_recommendation", "")
        advisor_latency = int((time.perf_counter() - t_adv_start) * 1000)

        # Step 7: System Confidence score mapping
        confidence_result = confidence_service.calculate_confidence(
            asr_data=asr_result,
            intent_data=intent_result,
            rag_data=rag_result,
            weather_data=weather_context
        )
        
        # Override output confidence
        advisor_result["confidence_score"] = confidence_result["system_confidence_score"]

        # Step 8: Evaluates human agronomist attention requirements
        review_case = human_review_service.evaluate(
            conversation_id="",  # Will populate below
            confidence_score=confidence_result["system_confidence_score"],
            intent_data=intent_result,
            advisor_data=advisor_result
        )
        badge = human_review_service.get_badge_metadata(
            case=review_case,
            confidence_score=confidence_result["system_confidence_score"]
        )

        # Step 9: Speech synthesis (TTS)
        t_tts_start = time.perf_counter()
        logger.info("Pipeline: Synthesizing Bangla advice to voice...")
        recommendation_audio_url = tts_service.synthesize(recommendation_text, voice_gender="female")
        tts_latency = int((time.perf_counter() - t_tts_start) * 1000)

        import datetime
        timestamp_str = datetime.datetime.utcnow().isoformat()
        total_latency = int((time.perf_counter() - t_start) * 1000)
        
        # Estimate tokens
        rag_context_len = sum(len(c.get("text", "")) for c in rag_docs)
        input_token_count = (len(corrected_bangla) + rag_context_len + len(history_context)) // 4
        output_token_count = len(recommendation_text) // 4
        
        from app.config.settings import Config
        is_corr_fallback = Config.USE_MOCK_LLM or asr_result.get("_is_mock_fallback", False)
        is_intent_fallback = Config.USE_MOCK_LLM or intent_result.get("_is_mock_fallback", False)
        is_advisor_fallback = Config.USE_MOCK_LLM or advisor_result.get("_is_mock_fallback", False)
        
        stage_status = {
            "stt": "executed" if audio_path else "skipped",
            "correction": "mock_fallback" if is_corr_fallback else "executed",
            "weather": "executed",
            "intent": "mock_fallback" if is_intent_fallback else "executed",
            "rag": "executed",
            "advisor": "mock_fallback" if is_advisor_fallback else "executed",
            "tts": getattr(tts_service, "last_synthesis_method", "mock_fallback")
        }

        metrics = {
            "stt_latency_ms": stt_latency if audio_path else 0,
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

        # Step 10: Model instantiation & validation
        diagnosis = Diagnosis(
            original_transcript=original_transcript,
            corrected_query=corrected_bangla,
            crop=crop,
            symptoms=", ".join(symptoms) if isinstance(symptoms, list) else str(symptoms),
            disease=advisor_result.get("diagnosis_title", "Undetermined Disease"),
            confidence=confidence_result["system_confidence_score"],
            severity=severity,
            urgency=urgency,
            recommendation_text=recommendation_text,
            recommendation_audio_url=recommendation_audio_url,
            rag_context=[{"text": c["text"], "metadata": {"source": c["source_name"]}} for c in rag_docs],
            weather_context=weather_context
        )

        # Save to database
        conversation = Conversation(
            conversation_id=conversation_id,  # Preserve ID if passed
            user_audio_path=audio_path or "",
            transcript=original_transcript,
            corrected_transcript=corrected_bangla,
            advisor_response=recommendation_text,
            response_audio_path=recommendation_audio_url,
            diagnosis_summary={
                "crop": crop,
                "symptoms": symptoms,
                "severity": severity,
                "urgency": urgency,
                "confidence": confidence_result["system_confidence_score"],
                "badge": badge
            },
            timestamp=timestamp_str
        )

        # Update case conversation ID
        if review_case:
            review_case.conversation_id = conversation.conversation_id

        # Compile turns list
        if history_payload:
            turns = history_payload.get("turns", [])
            if not turns and "raw_transcript" in history_payload:
                legacy_turn = {k: v for k, v in history_payload.items() if k != "turns"}
                turns = [legacy_turn]
        else:
            turns = []

        new_turn_payload = {
            "raw_transcript": original_transcript,
            "asr_corrected": asr_result,
            "intent": intent_result,
            "weather": weather_context,
            "rag": rag_result,
            "advisor": advisor_result,
            "confidence": confidence_result,
            "badge": badge,
            "district": resolved_district,
            "audio_metadata": audio_metadata,
            "timestamp": timestamp_str,
            "metrics": metrics
        }
        turns.append(new_turn_payload)

        # Save historical payload
        payload = {
            "conversation_id": conversation.conversation_id,
            "turns": turns,
            # Top-level attributes for the latest turn for backward-compatibility with UI
            "raw_transcript": original_transcript,
            "asr_corrected": asr_result,
            "intent": intent_result,
            "weather": weather_context,
            "rag": rag_result,
            "advisor": advisor_result,
            "confidence": confidence_result,
            "badge": badge,
            "district": resolved_district,
            "audio_metadata": audio_metadata,
            "timestamp": timestamp_str,
            "metrics": metrics
        }
        
        conversation_store.save_history(conversation.conversation_id, payload)
        
        # Save simple MVC conversation representation
        conversation_store.save_conversation(conversation)

        logger.info(f"Pipeline: Diagnostic completed for {conversation.conversation_id}")
        return jsonify(payload), 200

    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        return jsonify({"error": f"Failed to complete diagnosis: {str(e)}"}), 500
