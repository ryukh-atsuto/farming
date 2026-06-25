import os
from pathlib import Path
from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
from app.config.settings import Config

audio_bp = Blueprint("audio", __name__)

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in Config.ALLOWED_EXTENSIONS

@audio_bp.route("/api/audio/upload", methods=["POST"])
def upload_audio():
    """
    Upload a recorded voice file (mp3, wav, m4a, ogg).
    """
    if "audio" not in request.files:
        return jsonify({"error": "No audio file in request"}), 400
        
    file = request.files["audio"]
    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400
        
    if file and allowed_file(file.filename):
        try:
            Config.init_app()
            filename = secure_filename(file.filename)
            # Add unique prefix to avoid collisions
            import time
            unique_filename = f"{int(time.time())}_{filename}"
            save_path = Config.UPLOAD_DIR / unique_filename
            
            file.save(str(save_path))
            
            return jsonify({
                "message": "Audio file uploaded successfully",
                "file_path": str(save_path),
                "filename": unique_filename
            }), 200
        except Exception as e:
            return jsonify({"error": f"Failed to save audio file: {str(e)}"}), 500
            
    return jsonify({"error": f"Invalid file format. Supported: {Config.ALLOWED_EXTENSIONS}"}), 400
