import os
import logging
from flask import Flask, render_template, send_from_directory, jsonify, request
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from app.config.settings import Config
from app.controllers.audio_controller import audio_bp
from app.controllers.weather_controller import weather_bp
from app.controllers.tts_controller import tts_bp
from app.controllers.diagnosis_controller import diagnosis_bp
from app.controllers.demo_controller import demo_bp
from app.controllers.history_controller import history_bp
from app.controllers.export_controller import export_bp

# Configure detailed logging
handlers = [logging.StreamHandler()]
is_vercel = os.environ.get("VERCEL") is not None or os.environ.get("VERCEL_DEPLOYMENT", "false").lower() == "true"
if not is_vercel:
    try:
        handlers.append(logging.FileHandler("app.log", encoding="utf-8"))
    except Exception:
        pass

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=handlers
)
logger = logging.getLogger(__name__)

def create_app():
    # Set up folders and paths
    Config.init_app()
    
    # Configure custom templates and static paths in MVC view structure
    # Since this app.py is in app/, templates is at app/views/templates
    # and static is at app/views/static. We resolve paths relative to app/
    base_path = os.path.dirname(os.path.abspath(__file__))
    app = Flask(
        __name__,
        template_folder=os.path.join(base_path, "views", "templates"),
        static_folder=os.path.join(base_path, "views", "static")
    )
    
    app.config.from_object(Config)
    
    # Initialize Rate Limiter
    try:
        limiter = Limiter(
            key_func=get_remote_address,
            default_limits=["100 per day", "30 per hour"],
            storage_uri="memory://"
        )
        limiter.init_app(app)
        # Apply limits to blueprints
        limiter.limit("5 per minute")(audio_bp)
        limiter.limit("5 per minute")(diagnosis_bp)
        logger.info("Rate limiter enabled on endpoints.")
    except Exception as e:
        logger.warning(f"Could not initialize Flask-Limiter: {e}. Running without rate limits.")

    # Register Blueprints
    app.register_blueprint(audio_bp)
    app.register_blueprint(weather_bp)
    app.register_blueprint(tts_bp)
    app.register_blueprint(diagnosis_bp)
    app.register_blueprint(demo_bp)
    app.register_blueprint(history_bp)
    app.register_blueprint(export_bp)

    @app.route("/api/knowledge/stats")
    def knowledge_stats():
        try:
            from app.services.rag_service import RAGService
            rag = RAGService()
            count = rag.vector_store.count()
            from app.config.settings import Config
            emb_model = "models/embedding-001 (Google GenAI)" if Config.GEMINI_API_KEY else f"{Config.EMBEDDING_MODEL_NAME} (Default)"
            
            import glob
            doc_files = glob.glob(os.path.join(str(Config.KNOWLEDGE_BASE_DIR), "*"))
            if not doc_files:
                return jsonify({
                    "success": True,
                    "total_documents": 0,
                    "total_chunks": 0,
                    "embedding_model": emb_model,
                    "last_ingestion": None,
                    "last_ingestion_timestamp": None,
                    "message": "Knowledge base is empty. Add documents or run ingestion."
                })
            
            doc_count = len(doc_files)
            
            # Formulate ingestion timestamp from directory metadata or fallback
            import datetime
            last_ingestion = "2026-06-25 10:15:30 UTC"
            mtimes = [os.path.getmtime(f) for f in doc_files]
            if mtimes:
                dt = datetime.datetime.utcfromtimestamp(max(mtimes))
                last_ingestion = dt.strftime("%Y-%m-%d %H:%M:%S UTC")
                
            return jsonify({
                "total_documents": doc_count,
                "total_chunks": count,
                "embedding_model": emb_model,
                "last_ingestion": last_ingestion,
                "last_ingestion_timestamp": last_ingestion
            })
        except Exception as e:
            logger.error(f"Failed to fetch knowledge stats: {e}", exc_info=True)
            return jsonify({"error": str(e)}), 500

    @app.route("/api/knowledge/ingest", methods=["POST"])
    def trigger_ingestion():
        try:
            from app.services.rag_service import RAGService
            rag = RAGService()
            num_chunks = rag.ingest_directory_documents()
            return jsonify({"success": True, "message": f"Successfully ingested {num_chunks} chunks."})
        except Exception as e:
            logger.error(f"Failed to trigger ingestion: {e}", exc_info=True)
            return jsonify({"error": str(e)}), 500

    # Route to serve main UI
    @app.route("/")
    def index():

        return render_template("index.html")

    # Custom route to serve generated TTS audio files from local data directory
    @app.route("/static/audio/<filename>")
    def serve_audio_file(filename):
        return send_from_directory(str(Config.GENERATED_AUDIO_DIR), filename)

    # Error boundaries
    @app.errorhandler(404)
    def page_not_found(e):
        logger.error(f"404 Error: {request.url}")
        return jsonify({"error": "Resource not found"}), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        logger.error("500 Internal Server Error", exc_info=True)
        return jsonify({"error": "An internal server error occurred"}), 500

    @app.errorhandler(413)
    def request_entity_too_large(e):
        return jsonify({"error": "File size exceeds the 16MB limit"}), 413

    return app

app = create_app()
