# app/controllers/demo_controller.py
import logging
from flask import Blueprint, request, jsonify
from app.services.demo_service import DemoService

logger = logging.getLogger(__name__)

demo_bp = Blueprint("demo", __name__)
demo_service = DemoService()

@demo_bp.route("/api/demo/scenarios", methods=["GET"])
def list_scenarios():
    """Returns available validation/demo scenarios."""
    try:
        scenarios = demo_service.get_available_scenarios()
        return jsonify(scenarios), 200
    except Exception as e:
        logger.error(f"Failed to fetch scenarios: {e}")
        return jsonify({"error": f"Failed to load scenarios: {str(e)}"}), 500

@demo_bp.route("/api/demo/run", methods=["POST"])
def run_scenario():
    """Runs a complete diagnostics pipeline for a specific scenario ID."""
    data = request.get_json() or {}
    scenario_id = data.get("scenario_id")
    district = data.get("district")

    if not scenario_id:
        return jsonify({"error": "Missing scenario_id in request"}), 400

    try:
        result = demo_service.execute_scenario(scenario_id, district=district)
        return jsonify(result), 200
    except ValueError as ve:
        logger.warning(f"Scenario not found: {ve}")
        return jsonify({"error": str(ve)}), 404
    except Exception as e:
        logger.error(f"Failed running scenario: {e}", exc_info=True)
        return jsonify({"error": f"Internal error during execution: {str(e)}"}), 500
