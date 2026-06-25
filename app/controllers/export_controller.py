# app/controllers/export_controller.py
import logging
from flask import Blueprint, jsonify, Response
from app.repositories.conversation_store import ConversationStoreRepository
from app.services.export_service import ExportService

logger = logging.getLogger(__name__)

export_bp = Blueprint("export", __name__)
conversation_store = ConversationStoreRepository()
export_service = ExportService()

@export_bp.route("/api/export/<conversation_id>/<file_format>", methods=["GET"])
def export_diagnostic(conversation_id, file_format):
    """
    Exports a diagnostic report for a specific conversation session.
    Supported formats: 'txt' (human-readable report), 'json' (raw parameters).
    """
    logger.info(f"Exporting conversation {conversation_id} in format: {file_format}")
    try:
        data = conversation_store.get_history_by_id(conversation_id)
        if not data:
            return jsonify({"error": "Diagnostic record not found."}), 404

        file_format = file_format.lower().strip()
        if file_format == "json":
            json_str = export_service.format_to_json(data)
            return Response(
                json_str,
                mimetype="application/json",
                headers={"Content-disposition": f"attachment; filename=krishikantho_report_{conversation_id}.json"}
            )
        elif file_format == "txt":
            report_str = export_service.format_to_txt_report(data)
            return Response(
                report_str,
                mimetype="text/plain; charset=utf-8",
                headers={"Content-disposition": f"attachment; filename=krishikantho_report_{conversation_id}.txt"}
            )
        else:
            return jsonify({"error": f"Unsupported export format '{file_format}'. Use 'txt' or 'json'."}), 400

    except Exception as e:
        logger.error(f"Failed to export diagnostic: {e}", exc_info=True)
        return jsonify({"error": f"Failed to export report: {str(e)}"}), 500
