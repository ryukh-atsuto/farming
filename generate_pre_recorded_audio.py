import asyncio
import os
import math
import struct
import wave
import edge_tts

def synthesize_vocal_fallback(text: str, output_path: str, gender: str = "female"):
    # Syllables estimation
    num_syllables = max(4, len(text) // 3)
    num_syllables = min(35, num_syllables)
    
    sample_rate = 8000
    dir_name = os.path.dirname(output_path)
    if dir_name:
        os.makedirs(dir_name, exist_ok=True)
        
    # Pitch configuration: Male ~110Hz base, Female ~200Hz base
    pitch_base = 110.0 if gender == "male" else 200.0
    
    with wave.open(output_path, "wb") as wav_file:
        wav_file.setparams((1, 2, sample_rate, 0, "NONE", "not compressed"))
        
        frames = []
        for s in range(num_syllables):
            # Syllable duration
            duration = 0.14
            num_samples = int(sample_rate * duration)
            # Add some pitch inflection / intonation
            base_freq = pitch_base + 25.0 * math.sin(s * 0.7)
            
            for i in range(num_samples):
                t = i / sample_rate
                # Envelope
                envelope = 1.0
                fade_samples = int(sample_rate * 0.02)
                if i < fade_samples:
                    envelope = i / fade_samples
                elif i > num_samples - fade_samples:
                    envelope = (num_samples - i) / fade_samples
                    
                # Formant synthesis
                val = math.sin(2 * math.pi * base_freq * t)
                val += 0.5 * math.sin(2 * math.pi * (2 * base_freq) * t)
                val += 0.25 * math.sin(2 * math.pi * (3 * base_freq) * t)
                
                # Soft saturation
                val = math.tanh(val)
                
                sample_val = int(32767 * 0.25 * envelope * val)
                frames.append(struct.pack("<h", sample_val))
                
            # Syllable gap
            gap_samples = int(sample_rate * 0.02)
            for _ in range(gap_samples):
                frames.append(struct.pack("<h", 0))
                
        wav_file.writeframes(b"".join(frames))
    print(f"Synthesized fallback beep sample to: {output_path} ({len(text)} chars)")

async def synthesize_neural(text: str, output_path: str, gender: str = "female"):
    # Voice selection
    # Male: bn-BD-PradeepNeural
    # Female: bn-BD-NabanitaNeural
    voice = "bn-BD-NabanitaNeural" if gender == "female" else "bn-BD-PradeepNeural"
    
    dir_name = os.path.dirname(output_path)
    if dir_name:
        os.makedirs(dir_name, exist_ok=True)
        
    try:
        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(output_path)
        print(f"Synthesized neural {gender} sample to: {output_path} ({len(text)} chars)")
    except Exception as e:
        print(f"Error generating neural voice: {e}. Falling back to beep tones...")
        synthesize_vocal_fallback(text, output_path, gender)

async def main():
    scenarios = {
        "rice_brown_spot": {
            "input": "আমার ধানের পাতায় বাদামী দাগ পড়েছে।",
            "response": "আপনার ধানের পাতার বাদামী দাগ দেখে বাদামী দাগ রোগের ঝুঁকি মনে হচ্ছে। জমিতে অতিরিক্ত পানি জমতে দেবেন না, আক্রান্ত পাতা পর্যবেক্ষণ করুন, এবং সঠিক মাত্রার জন্য কৃষি কর্মকর্তার পরামর্শ নিন।"
        },
        "rice_blast": {
            "input": "ধানের পাতায় চোখের মতো দাগ দেখা যাচ্ছে আর কিছু পাতা শুকিয়ে যাচ্ছে।",
            "response": "আপনার ধানের পাতায় চোখের মতো দাগ ব্লাস্ট রোগের লক্ষণ নির্দেশ করে। আক্রান্ত জমিতে নাইট্রোজেন সার দেওয়া বন্ধ রাখুন, আর্দ্রতা বজায় রাখুন এবং বিকেল বেলা ট্রাইসাইক্লাজল জাতীয় ছত্রাকনাশক স্প্রে করুন।"
        },
        "tomato_leaf_curl": {
            "input": "আমার টমেটো গাছের পাতা কুঁকড়ে যাচ্ছে আর গাছের বৃদ্ধি কমে গেছে।",
            "response": "টমেটো গাছের পাতা কোঁকড়ানো ও বৃদ্ধি কমে যাওয়া পাতা কোঁকড়ানো ভাইরাসের লক্ষণ। আক্রান্ত গাছ দ্রুত তুলে ফেলুন এবং সাদা মাছি দমনের জন্য ইমিডাক্লোপ্রিড কীটনাশক ব্যবহার করুন।"
        },
        "jute_stem_rot": {
            "input": "পাট গাছের গোড়া কালো হয়ে যাচ্ছে আর গাছ ঢলে পড়ছে।",
            "response": "পাটের গোড়া কালো হওয়া ও গাছ ঢলে পড়া কাণ্ড পচা রোগের লক্ষণ। জমি থেকে অতিরিক্ত পানি নিষ্কাশনের ব্যবস্থা করুন এবং কার্বেন্ডাজিম বা অটোস্টিন গ্রুপের ছত্রাকনাশক গাছের গোড়ায় প্রয়োগ করুন।"
        }
    }
    
    # Paths
    base_dir = os.path.dirname(os.path.abspath(__file__))
    samples_dir = os.path.join(base_dir, "app", "views", "static", "audio", "demo_samples")
    responses_dir = os.path.join(base_dir, "app", "views", "static", "audio", "demo_responses")
    
    for key, data in scenarios.items():
        # Input samples (Male voice)
        input_filename = f"{key}_input.wav"
        input_path = os.path.join(samples_dir, input_filename)
        await synthesize_neural(data["input"], input_path, gender="male")
        
        # Response samples (Female voice)
        response_filename = f"{key}_response.mp3"
        response_path = os.path.join(responses_dir, response_filename)
        await synthesize_neural(data["response"], response_path, gender="female")
        
    print("All pre-recorded demo audio files generated successfully!")

if __name__ == "__main__":
    asyncio.run(main())
