import os
import logging
from pathlib import Path
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    genai = None

from app.config.settings import Config
from app.utils.audio_processor import process_audio

logger = logging.getLogger(__name__)

# Try to import faster-whisper. If it fails, we will fall back to Gemini Audio transcription
try:
    from faster_whisper import WhisperModel
    FASTER_WHISPER_AVAILABLE = True
except ImportError:
    FASTER_WHISPER_AVAILABLE = False
    logger.warning("faster-whisper package not available. Using Gemini-based audio transcription.")

class WhisperService:
    def __init__(self):
        self.model = None
        self.model_name = Config.WHISPER_MODEL_NAME  # large-v3
        
        if FASTER_WHISPER_AVAILABLE:
            try:
                # Detect device (cuda or cpu)
                import torch
                device = "cuda" if torch.cuda.is_available() else "cpu"
                
                # int8 quantization is much faster and uses less RAM on CPU
                compute_type = "float16" if device == "cuda" else "int8"
                
                logger.info(f"Initializing faster-whisper model '{self.model_name}' on '{device}' with '{compute_type}'")
                
                # We defer actual loading to the first transcription call to speed up server boot,
                # or initialize now. Let's do lazy loading.
                self.device = device
                self.compute_type = compute_type
            except Exception as e:
                logger.error(f"Error checking CUDA for Whisper: {e}")
                self.device = "cpu"
                self.compute_type = "int8"

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
            
            logger.warning("All faster-whisper models failed to load in WhisperService.")
            self.model = None

    def transcribe(self, input_audio_path: str) -> str:
        """
        Transcribe audio at input_audio_path.
        Converts the audio to 16kHz WAV mono first, then transcribes it.
        """
        # Define processed file path
        input_path = Path(input_audio_path)
        processed_path = input_path.parent / f"processed_{input_path.stem}.wav"
        
        # Preprocess audio (Noise reduction, volume normalization, silence trim, resample)
        success = process_audio(str(input_path), str(processed_path))
        if not success:
            logger.warning("Audio processing failed. Attempting transcription on original file.")
            processed_path = input_path

        # Try local faster-whisper first
        self._load_model()
        if self.model:
            try:
                logger.info(f"Running faster-whisper transcription on: {processed_path}")
                segments, info = self.model.transcribe(
                    str(processed_path),
                    beam_size=5,
                    language="bn"  # Force Bengali for better accuracy
                )
                
                # segments is a generator, we must join it
                text = " ".join([segment.text for segment in segments])
                logger.info(f"ASR complete. Language detected: {info.language} (confidence: {info.language_probability:.2f})")
                return text.strip()
            except Exception as e:
                logger.error(f"Local Whisper transcription failed: {e}. Falling back to Gemini API.")

        # Fallback: Transcribe using Gemini API
        if Config.GEMINI_API_KEY and GEMINI_AVAILABLE:
            try:
                logger.info("Transcribing using Gemini API audio upload...")
                genai.configure(api_key=Config.GEMINI_API_KEY)
                
                # Upload the audio file to the Gemini File API
                audio_file = genai.upload_file(path=str(processed_path))
                
                # Ask Gemini to transcribe the audio
                model = genai.GenerativeModel("gemini-2.0-flash")
                prompt = (
                    "Please listen to this Bengali audio recording. "
                    "Transcribe exactly what is being said in Bengali. "
                    "Only output the Bengali transcript text, nothing else."
                )
                response = model.generate_content([audio_file, prompt])
                
                # Cleanup the uploaded file
                try:
                    audio_file.delete()
                except Exception:
                    pass
                    
                text = response.text.strip()
                logger.info("Gemini API transcription complete.")
                return text
            except Exception as e:
                logger.error(f"Gemini API transcription failed: {e}")
                
        # If all else fails, return a friendly error message or mock fallback
        logger.warning("All transcription methods failed.")
        return ""
