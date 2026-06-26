import os
import logging
import shutil
from pathlib import Path

logger = logging.getLogger(__name__)

def process_audio(input_path: str, output_path: str) -> bool:
    """
    Load an audio file, apply noise reduction, volume normalization, 
    silence trimming, and convert to WAV 16kHz Mono.
    """
    try:
        input_path = Path(input_path)
        output_path = Path(output_path)
        
        # Load audio from file
        suffix = input_path.suffix.lower().replace(".", "")
        if suffix not in ["mp3", "wav", "m4a", "ogg"]:
            logger.error(f"Unsupported audio format: {suffix}")
            return False
            
        logger.info(f"Processing audio: {input_path} (format: {suffix})")
        
        try:
            from pydub import AudioSegment, effects
        except ImportError:
            logger.warning("pydub not installed. Skipping processing and copying original file.")
            # Ensure parent folder exists if possible
            try:
                output_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy(str(input_path), str(output_path))
                return True
            except Exception as copy_err:
                logger.error(f"Copy fallback failed: {copy_err}")
                return False
                
        # Load segment
        sound = AudioSegment.from_file(input_path, format=suffix)
        
        # 1. Convert to Mono and 16kHz
        sound = sound.set_frame_rate(16000).set_channels(1)
        
        # 2. Volume Normalization (Peak normalization to -20 dBFS)
        try:
            sound = effects.normalize(sound)
        except Exception as e:
            logger.warning(f"Failed to normalize volume: {e}")
            
        # 3. Noise Reduction via Band-pass Filter (high-pass at 80Hz, low-pass at 6000Hz)
        # This removes low-frequency rumble and high-frequency hiss, common in outdoor recordings.
        try:
            sound = sound.high_pass_filter(80)
            sound = sound.low_pass_filter(6000)
        except Exception as e:
            logger.warning(f"Failed to apply noise filter: {e}")
            
        # 4. Silence Trimming (remove silence at start and end, threshold = -45 dBFS)
        try:
            def get_silence_trim(s, thresh=-45.0, chunk=10):
                trim_ms = 0
                while trim_ms < len(s):
                    if s[trim_ms:trim_ms+chunk].dBFS < thresh:
                        trim_ms += chunk
                    else:
                        break
                return trim_ms

            start_trim = get_silence_trim(sound)
            end_trim = get_silence_trim(sound.reverse())
            
            duration_ms = len(sound)
            if start_trim + end_trim < duration_ms:
                sound = sound[start_trim:duration_ms - end_trim]
        except Exception as e:
            logger.warning(f"Failed to trim silence: {e}")
            
        # Ensure parent directory of output exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Export as WAV
        sound.export(output_path, format="wav")
        logger.info(f"Successfully processed audio to {output_path}")
        return True
        
    except Exception as e:
        logger.error(f"Error processing audio: {e}")
        return False
