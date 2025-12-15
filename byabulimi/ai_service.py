# byabulimi/ai_service.py

import json
from google import genai
from django.conf import settings
from .ai_config import SYSTEM_INSTRUCTION, DIAGNOSIS_OUTPUT_SCHEMA, GEMINI_MODEL

# Initialize the Gemini Client using the key from Django settings
client = genai.Client(api_key=settings.GEMINI_API_KEY)

# --- NEW HELPER FUNCTION ---
def file_to_part(file_content, mime_type="image/jpeg"):
    """
    Converts raw file content (bytes) into a genai.types.Part object.
    """
    return genai.types.Part.from_bytes(
        data=file_content,
        mime_type=mime_type,
    )

def generate_diagnosis(image_part, query_text: str, detected_crop: str, language_code: str):
    """
    Constructs the multimodal prompt and calls the Gemini API.
    """
    
    # --- COMPLETED PROMPT CONSTRUCTION ---
    prompt_parts = [
        image_part,
        (
            f"Diagnose the issue for the '{detected_crop}' based on the image and the farmer's observation. "
            f"Observation: '{query_text if query_text else 'No specific observation provided.'}'. "
            f"Provide actionable, culturally appropriate advice."
        ),
        f"The required output language for localized_advice is: **{language_code}**.",
        f"Strictly output the result as a single JSON object matching the required schema."
    ]
    # -----------------------------------

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
        # The API returns a string containing the JSON.
        return json.loads(response.text)

    except Exception as e:
        print(f"Gemini API Error: {e}")
        # Return the safe error structure
        # NOTE: We use the key 'localized_advice_luganda' as defined in ai_config.py
        return {
            "diagnosis_code": "ERROR-API",
            "confidence_score": 0.0,
            "localized_advice_luganda": f"Kyetaagisa okwongera okukola okunoonyereza. (Processing error.)",
            "is_expert_referral_needed": True,
            "english_summary": f"API or processing error: {str(e)}"
        }