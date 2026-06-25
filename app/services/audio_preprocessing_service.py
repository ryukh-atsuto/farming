# app/services/audio_preprocessing_service.py
import logging
import uuid
from pathlib import Path
from pydub import AudioSegment, effects
from app.config.settings import Config
from app.models.audio_job import AudioJob

logger = logging.getLogger(__name__)

class AudioPreprocessingService:
    def __init__(self):
        Config.init_app()
        self.upload_dir = Config.UPLOAD_DIR
        self.allowed_extensions = Config.ALLOWED_EXTENSIONS

    def preprocess(self, input_path: str) -> AudioJob:
        """
        Validate, normalize, noise filter, and convert audio to WAV 16kHz mono.
        Returns populated AudioJob object.
        """
        input_path = Path(input_path)
        job_id = str(uuid.uuid4())
        output_filename = f"cleaned_{job_id}.wav"
        output_path = self.upload_dir / output_filename
        
        job = AudioJob(
            id=job_id,
            filename=input_path.name,
            filepath=str(input_path),
            status="preprocessing"
        )
        
        try:
            # Validate extension
            suffix = input_path.suffix.lower().replace(".", "")
            if suffix not in self.allowed_extensions:
                raise ValueError(f"Unsupported format: {suffix}. Allowed: {self.allowed_extensions}")

            # Load audio segment
            sound = AudioSegment.from_file(input_path, format=suffix)
            
            # Check length limit
            duration_sec = len(sound) / 1000.0
            if duration_sec > Config.MAX_AUDIO_SECONDS:
                logger.warning(f"Audio exceeds duration limit: {duration_sec}s > {Config.MAX_AUDIO_SECONDS}s. Truncating.")
                sound = sound[:Config.MAX_AUDIO_SECONDS * 1000]
                duration_sec = Config.MAX_AUDIO_SECONDS

            # Set channels to 1 (Mono) and sample rate to 16000Hz
            sound = sound.set_frame_rate(16000).set_channels(1)
            
            # Volume Normalization
            try:
                sound = effects.normalize(sound)
            except Exception as e:
                logger.warning(f"Failed volume normalization: {e}")

            # Simple Band-Pass Filter (high-pass 80Hz, low-pass 6000Hz)
            try:
                sound = sound.high_pass_filter(80)
                sound = sound.low_pass_filter(6000)
            except Exception as e:
                logger.warning(f"Failed noise filtering: {e}")

            # Silence trimming
            try:
                def get_silence_trim(s, thresh=-45.0, chunk=10):
                    trim_ms = 0
                    while trim_ms < len(s):
                        if s[trim_ms:trim_ms+chunk].dBFS < thresh:
                            trim_ms += chunk
                        else:
                            break
                        return trim_ms  # Return on first break
                    return trim_ms

                start_trim = get_silence_trim(sound)
                end_trim = get_silence_trim(sound.reverse())
                
                total_len = len(sound)
                if start_trim + end_trim < total_len:
                    sound = sound[start_trim:total_len - end_trim]
            except Exception as e:
                logger.warning(f"Failed silence trimming: {e}")

            # Save clean file
            self.upload_dir.mkdir(parents=True, exist_ok=True)
            sound.export(output_path, format="wav")
            
            # Update job info
            job.filepath = str(output_path)
            job.filename = output_filename
            job.duration = round(len(sound) / 1000.0, 2)
            job.sample_rate = 16000
            job.channels = 1
            job.status = "completed"
            logger.info(f"Audio preprocessed successfully. Output: {output_path}")

        except Exception as e:
            logger.error(f"Failed audio preprocessing: {e}")
            job.status = "failed"
            job.error_message = str(e)
            
        return job
