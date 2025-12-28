# byabulimi/ai_service.py

import json
import logging
from google import genai
from django.conf import settings
from .ai_config import SYSTEM_INSTRUCTION, DIAGNOSIS_OUTPUT_SCHEMA, GEMINI_MODEL

# Setup logging for production traceability
logger = logging.getLogger(__name__)

# Initialize the Gemini Client using the key from Django settings
client = genai.Client(api_key=settings.GEMINI_API_KEY)

# --- HELPER FUNCTION ---
def file_to_part(file_content, mime_type="image/jpeg"):
    """
    Converts raw file content (bytes) into a genai.types.Part object for the multimodal prompt.
    """
    return genai.types.Part.from_bytes(
        data=file_content,
        mime_type=mime_type,
    )

def generate_diagnosis(image_part, query_text: str, detected_crop: str, language_code: str):
    """
    Constructs the multimodal prompt and calls the Gemini API to generate a diagnosis.
    Returns a dictionary matching the application's Advice schema.
    """
    
    # --- PROMPT CONSTRUCTION ---
    # We explicitly tell the AI which language to use for the localized_advice field.
    prompt_parts = [
        image_part,
        (
            f"Context: The farmer is reporting an issue with their '{detected_crop}'. "
            f"Farmer's Observation: '{query_text if query_text else 'No specific observation provided.'}'. "
            f"Task: Analyze the image and the observation to provide a diagnosis and culturally relevant advice."
        ),
        f"Language Requirement: The 'localized_advice' field MUST be written in the language associated with code: {language_code}.",
        "Strictly output the result as a single JSON object matching the required schema. Do not include markdown code blocks."
    ]

    try:
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt_parts,
            config=genai.types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                response_mime_type="application/json",
                response_schema=DIAGNOSIS_OUTPUT_SCHEMA,
                temperature=0.2 
            )
        )
        
        # Parse the JSON response from the Gemini API
        return json.loads(response.text)

    except Exception as e:
        # Use logging instead of print for production-grade error tracking
        logger.error(f"Gemini API Error: {e}", exc_info=True)
        
        # Return a safe error structure that prevents the mobile app from crashing.
        # Note: We use 'localized_advice' to match the Django model and Flutter API model.
        return {
            "diagnosis_code": "ERROR-API",
            "confidence_score": 0.0,
            "localized_advice": "Waliwo kiremya mu mbeera y'obudde. Gezaako nate emabale. (A processing error occurred.)",
            "is_expert_referral_needed": True,
            "english_summary": f"Gemini API or processing error: {str(e)}"
        }