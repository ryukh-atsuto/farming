# app/repositories/demo_scenario_store.py
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from app.config.settings import Config

DEFAULT_SCENARIOS = {
    "rice_brown_leaf_spot": {
        "id": "rice_brown_leaf_spot",
        "title": "Rice Brown Leaf Spot (ধানের বাদামী দাগ রোগ)",
        "farmer_complaint": "আমার ধানের পাতায় বাদামী দাগ পড়েছে",
        "raw_transcript": "আমার ধানের পাতায় বাদামী দাগ পড়েছে",
        "corrected_bangla": "আমার ধানের পাতায় বাদামী দাগ পড়েছে",
        "english_translation": "Brown spots have appeared on my rice leaves.",
        "crop": "rice",
        "symptoms": ["brown spots on leaves", "leaf drying"],
        "severity": "medium",
        "urgency": "normal",
        "weather": {
            "location_name": "Mymensingh Demo Farm",
            "temperature_c": 31.2,
            "humidity_percent": 84.0,
            "rain_probability": 65.0,
            "forecast_summary": "High humidity with scattered thunder showers expected.",
            "weather_risk_factors": ["High humidity creates favorable conditions for fungal spore spread."]
        },
        "diagnosis_title": "ধানের বাদামী দাগ রোগ (Brown Leaf Spot)",
        "likely_problem": "Fungal infection caused by Bipolaris oryzae",
        "confidence_score": 0.85,
        "risk_level": "medium",
        "bangla_recommendation": "কৃষক ভাই, আপনার ধানের জমিতে বাদামী দাগ বা ব্রাউন স্পট রোগ দেখা দিয়েছে। এটি একটি ছত্রাকজনিত রোগ। প্রতিকারের জন্য জমিতে সুষম সার ব্যবহার করুন, বিশেষ করে পটাশ সার সঠিক মাত্রায় দিন। আক্রমণ তীব্র হলে প্রতি লিটার পানিতে ট্রাইসাইক্লাজল ৭২ ডব্লিউপি (যেমন: ট্রুপার) ০.৭৫ গ্রাম অথবা প্রপিকোনাজল (যেমন: টিল্ট ২৫০ ইসি) ১ মিলি মিশিয়ে ১০-১২ দিন পর পর ২ বার স্প্রে করুন। জমিতে পানি ধরে রাখুন এবং আক্রান্ত গাছের অবশিষ্টাংশ পুড়িয়ে ফেলুন।",
        "english_summary": "Diagnosed with Rice Brown Leaf Spot disease. Caused by nutritional deficiency (mainly Potassium) and fungal pathogens. Recommended balance fertilizer and systemic fungicide application.",
        "immediate_actions": [
            "জমিতে পর্যাপ্ত ইউরিয়া ও পটাশ সার সুষম মাত্রায় প্রয়োগ করুন।",
            "জমিতে পানির অভাব হতে দেবেন না, পর্যাপ্ত পানি রাখুন।",
            "ছত্রাকনাশক স্প্রে করার ব্যবস্থা করুন।"
        ],
        "what_to_avoid": [
            "অতিরিক্ত ইউরিয়া সার প্রয়োগ করা থেকে বিরত থাকুন।",
            "আক্রান্ত জমির পানি সুস্থ জমিতে প্রবাহিত করবেন না।"
        ],
        "human_review_required": False,
        "human_review_reasons": [],
        "uncertainty_explanation": "লক্ষণগুলো স্পষ্ট, তবে ছত্রাকনাশক কেনার আগে ডিলার বা উপ-সহকারী কৃষি কর্মকর্তার সাথে পরামর্শ করে ঔষধের মেয়াদ দেখে নিন।",
        "source_documents_used": ["rice_disease_manual.txt", "brri_brown_spot_guide.txt"],
        "weather_factors_used": ["High humidity (84%) increases fungal spore growth rates."]
    },
    "rice_blast": {
        "id": "rice_blast",
        "title": "Rice Blast (ধানের ব্লাস্ট রোগ)",
        "farmer_complaint": "ধান গাছের গিট পচে ভেঙে যাচ্ছে আর পাতা পুড়ে যাচ্ছে",
        "raw_transcript": "ধান গাছের গিট পচে ভেঙে যাচ্ছে আর পাতা পুড়ে যাচ্ছে",
        "corrected_bangla": "ধান গাছের গিট পচে ভেঙে যাচ্ছে এবং পাতা পুড়ে যাচ্ছে",
        "english_translation": "Rice plant nodes are rotting, breaking, and leaves are drying up like fire.",
        "crop": "rice",
        "symptoms": ["node rot", "leaf drying", "neck rot"],
        "severity": "high",
        "urgency": "urgent",
        "weather": {
            "location_name": "Sylhet Demo Farm",
            "temperature_c": 28.5,
            "humidity_percent": 90.0,
            "rain_probability": 80.0,
            "forecast_summary": "Continuous rain and warm conditions forecast.",
            "weather_risk_factors": ["Over 90% humidity is highly critical for neck blast propagation."]
        },
        "diagnosis_title": "ধানের নেক ব্লাস্ট ও গিট ব্লাস্ট (Neck & Node Blast)",
        "likely_problem": "Fungal infection caused by Magnaporthe oryzae",
        "confidence_score": 0.92,
        "risk_level": "high",
        "bangla_recommendation": "কৃষক ভাই, এটি ধানের মারাত্মক নেক বা গিট ব্লাস্ট রোগ। অতি দ্রুত ব্যবস্থা না নিলে ফসল সম্পূর্ণ নষ্ট হতে পারে। প্রতিকারের জন্য জমিতে ট্রাইসাইক্লাজল ৭২ ডব্লিউপি (যেমন: ট্রুপার) প্রতি লিটার পানিতে ০.৭৫ গ্রাম অথবা টেবুকোনাজল+ট্রাইফ্লক্সিস্ট্রবিন (যেমন: নাটিভো ৭৫ ডব্লিউজি) প্রতি লিটার পানিতে ০.৬ গ্রাম মিশিয়ে ১০ দিন পর পর ২ বার স্প্রে করুন। বিকেল বেলা স্প্রে করবেন। জমিতে পর্যাপ্ত পানি ধরে রাখুন এবং এই অবস্থায় জমিতে অতিরিক্ত ইউরিয়া সার দেওয়া বন্ধ রাখুন। সঠিক মাত্রার জন্য কৃষি কর্মকর্তার পরামর্শ নিন।",
        "english_summary": "Diagnosed with severe Neck/Node Blast. Spreads rapidly under wet/warm conditions. Highly urgent action required. Spray systemic fungicides immediately and suspend nitrogen fertilizers.",
        "immediate_actions": [
            "জমিতে নাইট্রোজেন বা ইউরিয়া সার দেওয়া সম্পূর্ণ বন্ধ রাখুন।",
            "জমিতে পানি ধরে রাখুন এবং আর্দ্রতা বজায় রাখুন।",
            "অতি দ্রুত নাটিভো বা ট্রুপার জাতীয় ছত্রাকনাশক স্প্রে করুন।"
        ],
        "what_to_avoid": [
            "আক্রান্ত জমিতে ইউরিয়া সার স্প্রে বা ছিটানো বন্ধ করুন।",
            "দিনের প্রখর রোদে স্প্রে করা এড়িয়ে চলুন, বিকেলে স্প্রে করুন।"
        ],
        "human_review_required": True,
        "human_review_reasons": [
            "chemical_dosage_pesticide_imminent",
            "high_severity_crop_destruction_risk"
        ],
        "uncertainty_explanation": "যেহেতু এটি একটি মারাত্মক রাসায়নিক ছত্রাকনাশক নির্দেশ করে, তাই কৃষি কর্মকর্তার সরাসরি মতামত নেওয়া আবশ্যক।",
        "source_documents_used": ["brri_blast_management_guide.txt"],
        "weather_factors_used": ["High humidity (90%) and rain forecasts accelerate pathogen spreading."]
    },
    "tomato_leaf_curl": {
        "id": "tomato_leaf_curl",
        "title": "Tomato Leaf Curl (টমেটোর পাতা কোঁকড়ানো রোগ)",
        "farmer_complaint": "টমেটো গাছের কচি পাতাগুলো কেমন জানি কুকড়ে কুচকে ছোট হয়ে গেছে",
        "raw_transcript": "টমেটো গাছের কচি পাতাগুলো কেমন জানি কুকড়ে কুচকে ছোট হয়ে গেছে",
        "corrected_bangla": "টমেটো গাছের কচি পাতাগুলো কুকড়ে কুঁচকে ছোট হয়ে গেছে",
        "english_translation": "The young leaves of the tomato plants have curled up and shrunk.",
        "crop": "tomato",
        "symptoms": ["curled leaves", "shrunk leaves", "stunted growth"],
        "severity": "medium",
        "urgency": "normal",
        "weather": {
            "location_name": "Rajshahi Demo Farm",
            "temperature_c": 34.0,
            "humidity_percent": 55.0,
            "rain_probability": 10.0,
            "forecast_summary": "Dry, hot and sunny conditions.",
            "weather_risk_factors": ["Dry, hot weather increases whitefly vector activity."]
        },
        "diagnosis_title": "টমেটোর পাতা কোঁকড়ানো রোগ (Tomato Leaf Curl Virus - TYLCV)",
        "likely_problem": "Viral disease transmitted by Whitefly (Bemisia tabaci)",
        "confidence_score": 0.88,
        "risk_level": "medium",
        "bangla_recommendation": "কৃষক ভাই, এটি টমেটোর পাতা কোঁকড়ানো ভাইরাস রোগ। এটি সাধারণত সাদা মাছি নামক এক ধরণের পোকার মাধ্যমে ছড়ায়। প্রতিকারের জন্য আক্রান্ত গাছ দেখামাত্রই গোড়াসহ তুলে মাটির নিচে পুঁতে ফেলুন। সাদা মাছি দমনের জন্য ইমিডাক্লোপ্রিড গ্রুপের কীটনাশক (যেমন: টিডো বা এডমায়ার) প্রতি লিটার পানিতে ০.৫ মিলি অথবা অ্যাসিটামিপ্রিড (যেমন: টুন্ড্রা) প্রতি লিটার পানিতে ১ গ্রাম মিশিয়ে ৭-১০ দিন পর পর ২ বার স্প্রে করুন। চারা রোপণের সময় নাইলন জাল ব্যবহার করুন।",
        "english_summary": "Diagnosed with Tomato Leaf Curl Virus (TYLCV), spread by whitefly vectors. Advised vector control insecticides and physical removal of infected plants.",
        "immediate_actions": [
            "আক্রান্ত টমেটো গাছ দ্রুত উপরে ফেলে দূরে মাটির নিচে পুঁতে দিন।",
            "জমির আগাছা পরিষ্কার রাখুন যেন সাদা মাছি আশ্রয় না পায়।",
            "সাদা মাছি দমনে হলুদ আঠালো ফাঁদ ব্যবহার করুন বা ইমিডাক্লোপ্রিড স্প্রে করুন।"
        ],
        "what_to_avoid": [
            "আক্রান্ত গাছ জমিতে রেখে দেয়া থেকে বিরত থাকুন।",
            "অতিরিক্ত রাসায়নিক প্রয়োগ করবেন না যদি সাদা মাছির উপস্থিতি না থাকে।"
        ],
        "human_review_required": False,
        "human_review_reasons": [],
        "uncertainty_explanation": "ভাইরাস জনিত রোগ নিরাময় অযোগ্য, তাই নিয়ন্ত্রণ পদ্ধতি শুধুমাত্র ছড়ানোর গতি হ্রাসের উদ্দেশ্যে দেওয়া হয়েছে।",
        "source_documents_used": ["bari_tomato_guide.txt"],
        "weather_factors_used": ["Dry and hot conditions (34°C) favor whitefly population growth."]
    },
    "jute_stem_rot": {
        "id": "jute_stem_rot",
        "title": "Jute Stem Rot (পাটের কাণ্ড পচা রোগ)",
        "farmer_complaint": "পাটের গোড়ার দিকে কালো দাগ হয়ে পচে গাছ শুকিয়ে যাচ্ছে",
        "raw_transcript": "পাটের গোড়ার দিকে কালো দাগ হয়ে পচে গাছ শুকিয়ে যাচ্ছে",
        "corrected_bangla": "পাটের গোড়ার দিকে কালো দাগ হয়ে পচে গাছ শুকিয়ে যাচ্ছে",
        "english_translation": "Black spots have formed near the base of the jute stem, rotting it and drying up the plant.",
        "crop": "jute",
        "symptoms": ["black spot on stem", "stem rot", "plant drying"],
        "severity": "high",
        "urgency": "urgent",
        "weather": {
            "location_name": "Faridpur Demo Farm",
            "temperature_c": 32.5,
            "humidity_percent": 88.0,
            "rain_probability": 70.0,
            "forecast_summary": "Monsoonal rain and humid climate.",
            "weather_risk_factors": ["Waterlogging combined with high humidity causes fungal stem rot outbreaks."]
        },
        "diagnosis_title": "পাটের কাণ্ড পচা রোগ (Jute Stem Rot)",
        "likely_problem": "Fungal infection caused by Macrophomina phaseolina",
        "confidence_score": 0.82,
        "risk_level": "high",
        "bangla_recommendation": "কৃষক ভাই, আপনার পাটের জমিতে কাণ্ড পচা রোগ দেখা দিয়েছে। এটি একটি ক্ষতিকর ছত্রাকজনিত রোগ। প্রতিকারের জন্য জমিতে যেন পানি জমে না থাকে সেদিকে খেয়াল রাখুন, নিষ্কাশন ব্যবস্থা উন্নত করুন। আক্রান্ত গাছ উঠিয়ে পুড়ে ফেলুন। প্রতি লিটার পানিতে কার্বেন্ডাজিম গ্রুপের ছত্রাকনাশক (যেমন: নোইন বা অটোস্টিন) ২ গ্রাম অথবা ম্যানকোজেব+মেটালাক্সিল (যেমন: রিডোমিল গোল্ড) ২ গ্রাম মিশিয়ে ১০ দিন পর পর গাছের গোড়ায় ২ বার স্প্রে করুন। সঠিক মাত্রার জন্য কৃষি কর্মকর্তার পরামর্শ নিন।",
        "english_summary": "Diagnosed with Jute Stem Rot. Fungal disease amplified by high soil moisture and waterlogging. Recommend improving drainage and applying copper/carbendazim fungicides.",
        "immediate_actions": [
            "জমিতে জমে থাকা অতিরিক্ত পানি বের করে দেওয়ার দ্রুত ব্যবস্থা করুন।",
            "আক্রান্ত গাছ তুলে ফেলে পুড়িয়ে দিন যাতে ছত্রাক না ছড়ায়।",
            "গোড়ার মাটিতে অটোস্টিন বা কার্বেন্ডাজিম জাতীয় ছত্রাকনাশক স্প্রে করুন।"
        ],
        "what_to_avoid": [
            "জমিতে পানি জমা থাকা অবস্থায় চাষ করবেন না বা সার দেবেন না।",
            "সংক্রমিত কাণ্ড শুকানোর জন্য সুস্থ গাছের পাশে রাখবেন না।"
        ],
        "human_review_required": True,
        "human_review_reasons": ["chemical_dosage_pesticide_imminent"],
        "uncertainty_explanation": "মাটির আর্দ্রতা অনুযায়ী ছত্রাকনাশকের ডোজ ওঠানামা করতে পারে, উপ-সহকারী কৃষি কর্মকর্তার কাছে নিশ্চিত হয়ে নিন।",
        "source_documents_used": ["bjri_jute_disease_manual.txt"],
        "weather_factors_used": ["Waterlogging and high humidity (88%) amplify stem rot lesions."]
    }
}

class DemoScenarioStore:
    def __init__(self, file_path: Path = None):
        self.file_path = file_path or Config.DEMO_SCENARIOS_FILE

    def get_all_scenarios(self) -> List[Dict[str, Any]]:
        """Loads and returns all demo scenarios from JSON, or uses default fallback."""
        if self.file_path.exists():
            try:
                with open(self.file_path, "r", encoding="utf-8") as f:
                    return list(json.load(f).values())
            except Exception as e:
                print(f"Error loading demo scenarios from {self.file_path}: {e}")
        
        return list(DEFAULT_SCENARIOS.values())

    def get_scenario(self, scenario_id: str) -> Optional[Dict[str, Any]]:
        """Returns a single scenario by ID."""
        if self.file_path.exists():
            try:
                with open(self.file_path, "r", encoding="utf-8") as f:
                    scenarios = json.load(f)
                    return scenarios.get(scenario_id)
            except Exception as e:
                print(f"Error loading scenario {scenario_id} from {self.file_path}: {e}")
        
        return DEFAULT_SCENARIOS.get(scenario_id)

    def get_scenarios(self) -> List[Dict[str, Any]]:
        """Alias for get_all_scenarios."""
        return self.get_all_scenarios()

    def get_scenario_by_id(self, scenario_id: str) -> Optional[Dict[str, Any]]:
        """Alias for get_scenario."""
        return self.get_scenario(scenario_id)

    def save_default_scenarios(self) -> None:
        """Saves the default scenarios to the config file path."""
        try:
            self.file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump(DEFAULT_SCENARIOS, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"Failed to write default scenarios to {self.file_path}: {e}")
            
    def save_sample_agriculture_dataset(self, target_path: Path) -> None:
        """Helper to create a sample agriculture RAG dataset JSON."""
        dataset = [
            {
                "id": "brri_001",
                "title": "Rice Blast Management",
                "crop": "rice",
                "disease": "blast",
                "content": "Bangladesh Rice Research Institute (BRRI) Blast Control Manual: Rice blast is caused by Magnaporthe oryzae. Symptoms include spindle-shaped leaf lesions and neck rot where panicles collapse. High relative humidity above 85% and warm temperatures of 25-30°C are extremely favorable. Treatment: Suspend Nitrogen/Urea applications. Keep fields irrigated. Apply Tricyclazole 72 WP (Trooper) at 0.75g per liter of water, or Nativo 75 WG at 0.6g per liter of water. Spray in the afternoon.",
                "source": "brri_blast_management_guide.txt"
            },
            {
                "id": "brri_002",
                "title": "Rice Brown Leaf Spot Prevention",
                "crop": "rice",
                "disease": "brown_leaf_spot",
                "content": "BRRI Leaf Spot advisory: Brown Leaf Spot (Bipolaris oryzae) manifests as small oval dark brown lesions on rice foliage. Often associated with potassium-deficient, sandy or low-fertility soils. Control: Apply balanced fertilizers (potash and gypsum). Apply Propiconazole (Tilt 250 EC) at 1ml per liter of water, or Tricyclazole at 0.75g per liter. Spray twice with a 10-12 day gap.",
                "source": "brri_brown_spot_guide.txt"
            },
            {
                "id": "bari_001",
                "title": "Tomato Leaf Curl virus controls",
                "crop": "tomato",
                "disease": "leaf_curl",
                "content": "Bangladesh Agricultural Research Institute (BARI) Tomato Management: Leaf curl virus is spread by Whitefly (Bemisia tabaci). Symptoms are downward curling, severe puckering, yellowing and stunted plant height. Viral infections are incurable, so infected plants must be uprooted and buried. Spray systemic vector insecticides: Imidacloprid (Admire or Tido) at 0.5ml per liter, or Acetamiprid (Tundra) at 1g per liter, to eliminate whitefly vectors.",
                "source": "bari_tomato_guide.txt"
            },
            {
                "id": "bjri_001",
                "title": "Jute Stem Rot cure",
                "crop": "jute",
                "disease": "stem_rot",
                "content": "Bangladesh Jute Research Institute (BJRI) Stem Rot prevention: Jute stem rot is caused by Macrophomina phaseolina. Dark brown or black lesions occur near the base of the stems, leading to fiber rotting and dry plants. Favorable under waterlogging conditions. Action: Provide drainage. Apply Carbendazim (Autostin or Noin) at 2g per liter of water, or Mancozeb+Metalaxyl (Ridomil Gold) at 2g per liter at the root base. Repeat after 10 days.",
                "source": "bjri_jute_disease_manual.txt"
            }
        ]
        try:
            target_path.parent.mkdir(parents=True, exist_ok=True)
            with open(target_path, "w", encoding="utf-8") as f:
                json.dump(dataset, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"Failed to write sample dataset to {target_path}: {e}")
