# app/services/export_service.py
import json
import logging
from datetime import datetime
from typing import Dict, Any

logger = logging.getLogger(__name__)

class ExportService:
    def format_to_json(self, data: Dict[str, Any]) -> str:
        """Serializes query history parameters into formatted JSON."""
        try:
            return json.dumps(data, indent=4, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to serialize to JSON: {e}")
            return "{}"

    def format_to_txt_report(self, data: Dict[str, Any]) -> str:
        """
        Synthesizes a structured text report containing diagnosis, advice,
        weather, and judge-level logs.
        """
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        raw_text = data.get("raw_transcript", "")
        asr = data.get("asr_corrected", {})
        intent = data.get("intent", {})
        weather = data.get("weather", {})
        advisor = data.get("advisor", {})
        confidence = data.get("confidence", {})
        badge = data.get("badge", {})
        district = data.get("district", "Unknown")

        report = f"""==================================================
KRISHIKANTHO AI - FIELD DIAGNOSTIC REPORT
==================================================
Report Generated: {now}
Location Context: {district}
--------------------------------------------------
1. VOICE TRANSCRIPT & LINGUISTIC REPAIR
--------------------------------------------------
Raw Audio Text: "{raw_text}"
Corrected Bangla: "{asr.get('corrected_bangla', '')}"
English Translation: "{asr.get('english_translation', '')}"
Linguistic Dialect Style: {asr.get('detected_language_style', 'unknown')}
ASR Uncertainty Notes: {', '.join(asr.get('asr_uncertainty_notes', [])) or 'None'}

--------------------------------------------------
2. INTENT CLASSIFICATION METADATA
--------------------------------------------------
Target Crop: {intent.get('crop', 'unknown').upper()}
Identified Symptoms: {', '.join(intent.get('symptoms', [])) or 'None'}
Affected Plant Parts: {', '.join(intent.get('affected_parts', [])) or 'None'}
Urgency Index: {intent.get('urgency', 'unknown').upper()}
Severity Level: {intent.get('severity', 'unknown').upper()}
Suspected Cause: {intent.get('suspected_problem_type', 'unknown').upper()}

--------------------------------------------------
3. METEOROLOGICAL CONTEXT
--------------------------------------------------
Temperature: {weather.get('temp', 0.0)}°C
Relative Humidity: {weather.get('humidity', 0)}%
Precipitation Rate: {weather.get('rainfall', 0.0)} mm
Wind Velocity: {weather.get('wind_speed', 0.0)} m/s
Atmospheric Conditions: {weather.get('description', '')}

--------------------------------------------------
4. RECOMMENDATIONS FOR THE FARMER (BANGLA)
--------------------------------------------------
সমস্যার শিরোনাম: {advisor.get('diagnosis_title', '')}
পরামর্শ:
{advisor.get('bangla_recommendation', '')}

জরুরি করণীয় পদক্ষেপসমূহ:
{chr(10).join(['- ' + action for action in advisor.get('immediate_actions', [])]) or '- কোনো করণীয় পদক্ষেপ নেই।'}

যা করা থেকে বিরত থাকবেন:
{chr(10).join(['- ' + avoid for avoid in advisor.get('what_to_avoid', [])]) or '- কোনো সতর্কবাণী নেই।'}

অনিশ্চয়তার ব্যাখ্যা:
{advisor.get('uncertainty_explanation', 'কোনো উল্লেখযোগ্য অনিশ্চয়তা নেই।')}

--------------------------------------------------
5. COMPETITION JUDGE SYSTEM LOGS
--------------------------------------------------
Global Confidence Score: {confidence.get('system_confidence_score', 0.0)} / 1.00
  - ASR Clarity Score: {confidence.get('asr_score', 0.0)}
  - Intent Extract Score: {confidence.get('intent_score', 0.0)}
  - Vector Store RAG Score: {confidence.get('rag_score', 0.0)}
  - Meteorological Score: {confidence.get('weather_score', 0.0)}

System Status Badge: {badge.get('label', 'Normal')}
Agronomist Action Triggered: {str(advisor.get('human_review_required', False)).upper()}
Audit Triggers: {', '.join(advisor.get('human_review_reasons', [])) or 'None'}

Retrieved Reference Chunks:
{self._format_chunks_for_report(data.get('rag', {}).get('retrieved_chunks', []))}

==================================================
KrishiKantho AI - Empowering Voice-First AgriTech
==================================================
"""
        return report

    def _format_chunks_for_report(self, chunks: list) -> str:
        if not chunks:
            return "No RAG documents retrieved."
        formatted = []
        for idx, chunk in enumerate(chunks):
            formatted.append(
                f"  Chunk #{idx+1} [Relevance: {chunk.get('relevance_score', 0.0)}]\n"
                f"    Source: {chunk.get('source_name', 'Unknown')}\n"
                f"    Excerpt: {chunk.get('text', '')[:180]}..."
            )
        return "\n".join(formatted)
