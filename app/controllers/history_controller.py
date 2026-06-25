# app/controllers/history_controller.py
import logging
from flask import Blueprint, request, jsonify
from app.repositories.conversation_store import ConversationStoreRepository

logger = logging.getLogger(__name__)

history_bp = Blueprint("history", __name__)
conversation_store = ConversationStoreRepository()

@history_bp.route("/api/history", methods=["GET"])
def get_history_list():
    """Gets the list of recent query sessions containing status badges and timestamps."""
    try:
        limit = request.args.get("limit", default=20, type=int)
        raw_history = conversation_store.get_all_history()
        
        # Sort by timestamp descending
        sorted_history = sorted(
            raw_history,
            key=lambda x: x.get("timestamp", ""),
            reverse=True
        )
        return jsonify(sorted_history[:limit]), 200
    except Exception as e:
        logger.error(f"Failed to fetch history list: {e}")
        return jsonify({"error": f"Failed to load history list: {str(e)}"}), 500

@history_bp.route("/api/history/<conversation_id>", methods=["GET"])
def get_history_detail(conversation_id):
    """Gets the full JSON details for a specific conversation ID."""
    try:
        detail = conversation_store.get_history_by_id(conversation_id)
        if not detail:
            return jsonify({"error": "Conversation not found."}), 404
        return jsonify(detail), 200
    except Exception as e:
        logger.error(f"Failed to fetch history details: {e}")
        return jsonify({"error": f"Failed to retrieve conversation details: {str(e)}"}), 500

@history_bp.route("/api/history/delete/<conversation_id>", methods=["DELETE"])
def delete_history_item(conversation_id):
    """Deletes a specific conversation history item from storage."""
    try:
        success = conversation_store.delete_conversation(conversation_id)
        if success:
            return jsonify({"message": "Conversation history deleted successfully."}), 200
        return jsonify({"error": "Conversation not found."}), 404
    except Exception as e:
        logger.error(f"Failed to delete history item: {e}")
        return jsonify({"error": f"Failed to delete conversation: {str(e)}"}), 500

@history_bp.route("/api/history/clear", methods=["POST"])
def clear_all_history():
    """Clears all conversation records for demo reset."""
    try:
        conversation_store.clear_all()
        return jsonify({"message": "All diagnostic history cleared successfully."}), 200
    except Exception as e:
        logger.error(f"Failed to clear history: {e}")
        return jsonify({"error": f"Failed to clear history data: {str(e)}"}), 500
