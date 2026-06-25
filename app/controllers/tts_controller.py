from flask import Blueprint, request, jsonify
from app.services.tts_service import TTSService

tts_bp = Blueprint("tts", __name__)
tts_service = TTSService()

@tts_bp.route("/api/tts/synthesize", methods=["POST"])
def synthesize_speech():
    """
    Synthesize Bangla text to speech.
    """
    data = request.get_json() or {}
    text = data.get("text", "")
    gender = data.get("gender", "female")
    
    if not text or not text.strip():
        return jsonify({"error": "No text content provided for synthesis"}), 400
        
    try:
        audio_url = tts_service.synthesize(text, voice_gender=gender)
        if not audio_url:
            return jsonify({"error": "Failed to synthesize speech"}), 500
            
        return jsonify({
            "message": "Speech synthesized successfully",
            "audio_url": audio_url
        }), 200
    except Exception as e:
        return jsonify({"error": f"TTS controller error: {str(e)}"}), 500
