import math
import struct
import wave
import os

def synthesize_retro_voice(text: str, output_path: str):
    num_syllables = max(3, len(text) // 3)
    num_syllables = min(30, num_syllables)
    
    sample_rate = 8000
    dir_name = os.path.dirname(output_path)
    if dir_name:
        os.makedirs(dir_name, exist_ok=True)
    
    with wave.open(output_path, "wb") as wav_file:
        wav_file.setparams((1, 2, sample_rate, 0, "NONE", "not compressed"))
        
        frames = []
        for s in range(num_syllables):
            duration = 0.15
            num_samples = int(sample_rate * duration)
            base_freq = 150.0 + 30.0 * math.sin(s * 0.8)
            
            for i in range(num_samples):
                t = i / sample_rate
                envelope = 1.0
                fade_samples = int(sample_rate * 0.02)
                if i < fade_samples:
                    envelope = i / fade_samples
                elif i > num_samples - fade_samples:
                    envelope = (num_samples - i) / fade_samples
                
                val = math.sin(2 * math.pi * base_freq * t)
                val += 0.5 * math.sin(2 * math.pi * (2 * base_freq) * t)
                val += 0.25 * math.sin(2 * math.pi * (3 * base_freq) * t)
                val = math.tanh(val)
                
                sample_val = int(32767 * 0.25 * envelope * val)
                frames.append(struct.pack("<h", sample_val))
                
            gap_samples = int(sample_rate * 0.03)
            for _ in range(gap_samples):
                frames.append(struct.pack("<h", 0))
                
        wav_file.writeframes(b"".join(frames))
    print("Voice synthesized successfully at:", output_path)

if __name__ == "__main__":
    synthesize_retro_voice("আমার ধানের পাতায় বাদামী দাগ পড়েছে", "test_output.wav")
