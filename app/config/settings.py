import os
from pathlib import Path
from dotenv import load_dotenv

# Load env variables from .env
load_dotenv()

class Config:
    BASE_DIR = Path(__file__).resolve().parent.parent.parent
    SECRET_KEY = os.environ.get("SECRET_KEY", "krishikantho_secret_key_123987")
    FLASK_ENV = os.environ.get("FLASK_ENV", "development")
    
    # API Keys
    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
    HF_TOKEN = os.environ.get("HF_TOKEN", "")
    OPENWEATHER_API_KEY = os.environ.get("OPENWEATHER_API_KEY", "")
    
    # System toggles
    USE_OPEN_METEO = os.environ.get("USE_OPEN_METEO", "true").lower() == "true"
    USE_MOCK_LLM = os.environ.get("USE_MOCK_LLM", "true").lower() == "true"
    USE_MOCK_TTS = os.environ.get("USE_MOCK_TTS", "false").lower() == "true"
    
    # Paths (Internal to Workspace)
    DATA_DIR = BASE_DIR / "data"
    KNOWLEDGE_BASE_DIR = DATA_DIR / "knowledge_base"
    CHROMA_DB_DIR = DATA_DIR / "chroma_db"
    DEMO_SCENARIOS_FILE = DATA_DIR / "demo_scenarios.json"
    CONVERSATION_HISTORY_FILE = DATA_DIR / "conversation_history.json"
    UPLOAD_DIR = DATA_DIR / "uploads"
    GENERATED_AUDIO_DIR = DATA_DIR / "generated_audio"
    
    EMBEDDING_MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    SAMPLE_DATASET_FILE = BASE_DIR / "data" / "sample_agriculture_dataset.json"
    
    # Audio Settings
    ALLOWED_EXTENSIONS = {"mp3", "wav", "m4a", "ogg"}
    MAX_UPLOAD_MB = int(os.environ.get("MAX_UPLOAD_MB", "25"))
    MAX_CONTENT_LENGTH = MAX_UPLOAD_MB * 1024 * 1024  # Flask file limit
    MAX_AUDIO_SECONDS = int(os.environ.get("MAX_AUDIO_SECONDS", "90"))
    
    # Model configuration
    WHISPER_MODEL_NAME = os.environ.get("WHISPER_MODEL", "small")
    WHISPER_COMPUTE_TYPE = os.environ.get("WHISPER_COMPUTE_TYPE", "int8")
    WHISPER_DEVICE = os.environ.get("WHISPER_DEVICE", "auto")
    
    # Default Location (Dhaka)
    DEFAULT_LATITUDE = float(os.environ.get("DEFAULT_LATITUDE", "23.8103"))
    DEFAULT_LONGITUDE = float(os.environ.get("DEFAULT_LONGITUDE", "90.4125"))
    DEFAULT_LOCATION_NAME = os.environ.get("DEFAULT_LOCATION_NAME", "Dhaka Demo Location")
    
    @classmethod
    def init_app(cls):
        # Ensure directories exist
        cls.DATA_DIR.mkdir(parents=True, exist_ok=True)
        cls.KNOWLEDGE_BASE_DIR.mkdir(parents=True, exist_ok=True)
        cls.CHROMA_DB_DIR.mkdir(parents=True, exist_ok=True)
        cls.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        cls.GENERATED_AUDIO_DIR.mkdir(parents=True, exist_ok=True)

