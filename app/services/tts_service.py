import os
import asyncio
import logging
import subprocess
from pathlib import Path
from app.config.settings import Config

logger = logging.getLogger(__name__)

class TTSService:
    def __init__(self):
        Config.init_app()
        self.output_dir = Path(Config.GENERATED_AUDIO_DIR)
        
        # Piper local binary configuration paths (in case the user installs it later)
        # Default checks for a 'piper' directory in the root
        self.piper_path = Config.BASE_DIR / "piper" / "piper.exe"
        self.piper_model = Config.BASE_DIR / "piper" / "bn_BD-fahim-medium.onnx"
        
        # Check if local Piper is ready
        self.piper_ready = self.piper_path.exists() and self.piper_model.exists()
        if self.piper_ready:
            logger.info("Piper TTS binary and model detected. Local offline synthesis enabled.")
        else:
            logger.info("Piper TTS not fully configured. Using Microsoft Edge-TTS neural fallback for premium natural Bangla speech.")

    def synthesize(self, text: str, voice_gender: str = "female") -> str:
        """
        Synthesize text to audio.
        Returns the relative file path to the output audio file (wav or mp3).
        """
        self.last_synthesis_method = "unknown"
        if not text or not text.strip():
            return ""
            
        # Clean text
        text = text.replace("*", "").replace("#", "").strip()
        
        # Generate unique filename based on hash of text
        text_hash = hash(text) & 0xffffffff
        file_extension = "wav" if (self.piper_ready or Config.USE_MOCK_TTS) else "mp3"
        filename = f"tts_{text_hash}.{file_extension}"
        output_filepath = self.output_dir / filename
        
        # If file already exists, return its relative path directly (caching!)
        if output_filepath.exists():
            logger.info(f"Using cached TTS file: {filename}")
            if Config.USE_MOCK_TTS:
                self.last_synthesis_method = "mock_fallback"
            elif self.piper_ready:
                self.last_synthesis_method = "piper"
            else:
                # If cached, it might be from edge-tts
                self.last_synthesis_method = "edge-tts"
            return f"/static/audio/{filename}"

        # If mock TTS is requested, handle it immediately
        if Config.USE_MOCK_TTS:
            success = self._run_mock_tts(text, str(output_filepath))
            if success:
                self.last_synthesis_method = "mock_fallback"
                return f"/static/audio/{filename}"

        if self.piper_ready:
            success = self._run_piper(text, str(output_filepath))
            if success:
                self.last_synthesis_method = "piper"
                # Flask view static mapping: we will expose the tts folder under /static/audio
                return f"/static/audio/{filename}"
                
        # Fallback to Edge-TTS
        success = self._run_edge_tts(text, str(output_filepath), voice_gender)
        if success:
            self.last_synthesis_method = "edge-tts"
            return f"/static/audio/{filename}"
            
        # Last resort: gTTS or dummy audio file
        success = self._run_gtts_fallback(text, str(output_filepath))
        if success:
            self.last_synthesis_method = "gtts"
            return f"/static/audio/{filename}"
            
        logger.error("All TTS synthesis pipelines failed.")
        self.last_synthesis_method = "failed"
        return ""

    def _run_mock_tts(self, text: str, output_path: str) -> bool:
        """
        Generates a dummy silent WAV file using the standard wave module.
        """
        try:
            logger.info(f"Generating mock silent TTS audio: '{text[:30]}...'")
            import wave
            import struct
            
            # Ensure parent directories exist
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Create a 1-second silent WAV file at 8000Hz mono
            with wave.open(output_path, "wb") as wav_file:
                # nchannels, sampwidth, framerate, nframes, comptype, compname
                wav_file.setparams((1, 2, 8000, 8000, "NONE", "not compressed"))
                # Write 8000 frames of silence (0)
                silence_frames = struct.pack("<8000h", *[0]*8000)
                wav_file.writeframes(silence_frames)
                
            if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                logger.info("Mock TTS generation completed successfully.")
                return True
            return False
        except Exception as e:
            logger.error(f"Mock TTS generation failed: {e}")
            return False

    def _run_piper(self, text: str, output_path: str) -> bool:
        """
        Run local Piper TTS binary via subprocess.
        """
        try:
            logger.info(f"Synthesizing with Piper: '{text[:30]}...'")
            # Piper reads from stdin and writes to the file
            # Example command: echo "text" | piper.exe --model model.onnx --output_file file.wav
            process = subprocess.Popen(
                [
                    str(self.piper_path),
                    "--model", str(self.piper_model),
                    "--output_file", output_path
                ],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8"
            )
            stdout, stderr = process.communicate(input=text)
            
            if process.returncode == 0 and os.path.exists(output_path):
                logger.info("Piper synthesis completed successfully.")
                return True
            else:
                logger.error(f"Piper error (Code {process.returncode}): {stderr}")
                return False
        except Exception as e:
            logger.error(f"Error running Piper: {e}")
            return False

    def _run_edge_tts(self, text: str, output_path: str, voice_gender: str) -> bool:
        """
        Run edge-tts neural voice generator.
        """
        try:
            logger.info(f"Synthesizing with Edge-TTS: '{text[:30]}...'")
            # Select Bangla voice
            # Female: bn-BD-NabanitaNeural
            # Male: bn-BD-PradeepNeural
            voice = "bn-BD-NabanitaNeural" if voice_gender.lower() == "female" else "bn-BD-PradeepNeural"
            
            import edge_tts
            
            communicate = edge_tts.Communicate(text, voice)
            
            # Since edge-tts is async, we execute it synchronously
            asyncio.run(communicate.save(output_path))
            
            if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                logger.info("Edge-TTS synthesis completed successfully.")
                return True
            return False
        except Exception as e:
            logger.error(f"Edge-TTS synthesis failed: {e}")
            return False

    def _run_gtts_fallback(self, text: str, output_path: str) -> bool:
        """
        Fallback using Google Translate TTS (gTTS).
        """
        try:
            logger.info("Running gTTS fallback...")
            from gtts import gTTS
            tts = gTTS(text=text, lang="bn")
            tts.save(output_path)
            if os.path.exists(output_path):
                logger.info("gTTS synthesis completed successfully.")
                return True
            return False
        except Exception as e:
            logger.error(f"gTTS fallback failed: {e}")
            # Write a dummy silent audio block to avoid crashes
            # Try to write pure WAV silence first to avoid ffmpeg dependency
            if output_path.endswith(".wav"):
                return self._run_mock_tts(text, output_path)
            
            try:
                # Try pydub if it is a different format like mp3
                from pydub import AudioSegment
                silence = AudioSegment.silent(duration=1000)
                silence.export(output_path, format="mp3")
                logger.info("Created silent audio fallback via pydub.")
                return True
            except Exception as ex:
                logger.error(f"Failed to create silent fallback via pydub: {ex}")
                # As a final resort, even if it's named .mp3, write a WAV structure (most players will try to decode it, or at least it won't crash the server file writing)
                return self._run_mock_tts(text, output_path)
