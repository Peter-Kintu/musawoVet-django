# byabulimi/ai_config.py

# --- GEMINI API Configuration ---
# 'gemini-1.5-flash' is the best for the FREE TIER.
# It allows for higher rate limits and is optimized for speed/latency.
GEMINI_MODEL = "gemini-1.5-flash"

# The standard JSON output format expected by the Django backend.
# Changed 'localized_advice_luganda' to 'localized_advice' to match 
# byabulimi/models.py and support multiple languages (Luganda, Swahili, etc.)
DIAGNOSIS_OUTPUT_SCHEMA = {
    "diagnosis_code": "STRING (e.g., MAI-FALL-ARMY-A)",
    "confidence_score": "FLOAT (0.0 to 1.0)",
    "localized_advice": "STRING (Full actionable advice in the farmer's requested language)",
    "is_expert_referral_needed": "BOOLEAN (True if the case looks severe or ambiguous)",
    "english_summary": "STRING (Brief English summary for the agronomist/audit log)"
}

# The System Instruction sets the core persona and rules
SYSTEM_INSTRUCTION = (
    "You are an expert Agricultural Extension Officer operating in rural Uganda. "
    "Your primary goal is to provide **accurate, safe, and practical** advice to smallholder farmers. "
    "Analyze the image and the farmer's query carefully. "
    "Check for signs of pests, diseases, or nutrient deficiencies specific to East African agriculture. "
    "Follow a Chain-of-Thought process to reach your diagnosis, but ONLY output the final result "
    "as a strict JSON object matching the provided schema."
)