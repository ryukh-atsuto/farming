# app/services/stt_service.py
import logging
from pathlib import Path
import google.generativeai as genai
from app.config.settings import Config

logger = logging.getLogger(__name__)

try:
    from faster_whisper import WhisperModel
    FASTER_WHISPER_AVAILABLE = True
except ImportError:
    FASTER_WHISPER_AVAILABLE = False
    logger.warning("faster-whisper not available. Will use Gemini ASR fallback.")

class STTService:
    def __init__(self):
        self.model = None
        self.model_name = Config.WHISPER_MODEL_NAME
        self.device = Config.WHISPER_DEVICE
        self.compute_type = Config.WHISPER_COMPUTE_TYPE

        # Auto-configure device/compute if set to 'auto'
        if self.device == "auto":
            try:
                import torch
                self.device = "cuda" if torch.cuda.is_available() else "cpu"
            except ImportError:
                self.device = "cpu"

        if self.compute_type == "auto" or not self.compute_type:
            self.compute_type = "float16" if self.device == "cuda" else "int8"

    def _load_model(self):
        if self.model is None and FASTER_WHISPER_AVAILABLE:
            # Fallback sequence: Preferred (self.model_name) -> large-v3 -> medium -> small
            models_to_try = []
            if self.model_name:
                models_to_try.append(self.model_name)
            models_to_try.extend(["large-v3", "medium", "small"])
            
            unique_models = []
            for m in models_to_try:
                if m not in unique_models:
                    unique_models.append(m)
                    
            for mname in unique_models:
                try:
                    logger.info(f"Loading Whisper model '{mname}' on '{self.device}' ({self.compute_type})")
                    self.model = WhisperModel(
                        mname,
                        device=self.device,
                        compute_type=self.compute_type
                    )
                    logger.info(f"Successfully loaded Whisper model '{mname}'")
                    self.model_name = mname
                    return
                except Exception as e:
                    logger.error(f"Failed to load Whisper model '{mname}': {e}. Trying fallback.")
            
            logger.warning("All faster-whisper models failed to load.")
            self.model = None


    def transcribe(self, audio_path: str) -> str:
        """Transcribes the given WAV file to text with local and API fallbacks."""
        if not audio_path or not Path(audio_path).exists():
            logger.error(f"Audio file not found: {audio_path}")
            return ""

        # 1. Try local Whisper model
        self._load_model()
        if self.model:
            try:
                logger.info(f"Transcribing {audio_path} locally...")
                segments, info = self.model.transcribe(
                    str(audio_path),
                    beam_size=5,
                    language="bn"  # Force Bengali
                )
                text = " ".join([seg.text for seg in segments]).strip()
                logger.info(f"Transcription complete: '{text}' (lang: {info.language})")
                return text
            except Exception as e:
                logger.error(f"Local Whisper transcription failed: {e}. Trying Gemini API.")

        # 2. Try Gemini API File upload
        if Config.GEMINI_API_KEY and not Config.USE_MOCK_LLM:
            try:
                logger.info("Uploading audio to Gemini File API...")
                genai.configure(api_key=Config.GEMINI_API_KEY)
                audio_file = genai.upload_file(path=str(audio_path))
                
                model = genai.GenerativeModel("gemini-1.5-flash")
                prompt = (
                    "Please listen to this audio clip and transcribe the spoken words "
                    "exactly in standard Bengali characters. Only output the transcription, "
                    "do not add explanations or markdown."
                )
                response = model.generate_content([audio_file, prompt])
                
                # Cleanup API file
                try:
                    audio_file.delete()
                except Exception:
                    pass
                
                text = response.text.strip()
                logger.info(f"Gemini API transcription complete: '{text}'")
                return text
            except Exception as e:
                logger.error(f"Gemini API transcription failed: {e}")

        # 3. If no transcription succeeded, return empty string (caller will trigger mock scenario matching)
        logger.warning("All Speech-to-Text paths failed. Will rely on fallback text matcher.")
        return ""
