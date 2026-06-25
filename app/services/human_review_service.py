# app/services/human_review_service.py
import logging
from typing import Dict, Any, List, Optional
from app.models.review_case import ReviewCase

logger = logging.getLogger(__name__)

class HumanReviewService:
    def evaluate(
        self,
        conversation_id: str,
        confidence_score: float,
        intent_data: Dict[str, Any],
        advisor_data: Dict[str, Any]
    ) -> Optional[ReviewCase]:
        """
        Analyzes advisor findings, intent logs, and confidence metrics.
        Returns a ReviewCase if a human agronomist audit is triggered, otherwise None.
        """
        reasons = []

        # Check low confidence threshold
        if confidence_score < 0.70:
            reasons.append(f"low_confidence_score: {confidence_score}")

        # Check intent triggers
        if intent_data.get("human_review_triggered"):
            reasons.extend(intent_data.get("human_review_reasons", []))

        # Check advisor safety trigger
        if advisor_data.get("human_review_required"):
            for reason in advisor_data.get("human_review_reasons", []):
                if reason not in reasons:
                    reasons.append(reason)

        if reasons:
            logger.info(f"Human review required for conversation {conversation_id}. Reasons: {reasons}")
            return ReviewCase(
                conversation_id=conversation_id,
                reasons=reasons,
                status="pending_agronomist_review"
            )
        return None

    def get_badge_metadata(self, case: Optional[ReviewCase], confidence_score: float) -> Dict[str, Any]:
        """
        Returns visual badge properties (label, type/severity, class) for rendering
        the "Telecom Judge" / "Agronomist Audit" dashboards.
        """
        if case:
            reasons = case.reasons
            is_critical = any("dose" in r or "critical" in r or "severe" in r for r in reasons)
            if is_critical:
                return {
                    "badge_type": "critical",
                    "label": "Human Agronomist Review Recommended",
                    "css_class": "badge-danger",
                    "description": "Farming parameters hit safety thresholds (unsupported dosage query or high severity crop rot)."
                }
            else:
                return {
                    "badge_type": "warning",
                    "label": "Human Agronomist Review Recommended",
                    "css_class": "badge-warning",
                    "description": "Linguistic patterns or RAG index bounds returned high uncertainty scores. Review recommended."
                }
        
        # Standard verified pass
        return {
            "badge_type": "success",
            "label": "AI Verified Advice",
            "css_class": "badge-success",
            "description": "System confidence and vector matches are fully optimal."
        }

