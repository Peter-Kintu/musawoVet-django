# byabulimi/ai_config.py

# --- GEMINI API Configuration ---
GEMINI_MODEL = "gemini-2.5-flash"

# The standard JSON output format expected by the Django backend
DIAGNOSIS_OUTPUT_SCHEMA = {
    "diagnosis_code": "STRING (e.g., MAI-FALL-ARMY-A)",
    "confidence_score": "FLOAT (0.0 to 1.0)",
    "localized_advice_luganda": "STRING (Full actionable advice in Luganda)",
    "is_expert_referral_needed": "BOOLEAN (True if the case looks severe or ambiguous)",
    "english_summary": "STRING (Brief English summary for the agronomist/audit log)"
}

# The System Instruction sets the core persona and rules
SYSTEM_INSTRUCTION = (
    "You are an expert Agricultural Extension Officer operating in rural Uganda. "
    "Your primary goal is to provide **accurate, safe, and practical** advice to smallholder farmers. "
    "Analyze the image and the farmer's query. Follow the Chain-of-Thought process and ONLY output the result as a strict JSON object."
)