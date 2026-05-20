import os
import json
from dotenv import load_dotenv

load_dotenv()

def get_available_chat_model():
    """Get an available chat model from Groq by testing them"""
    try:
        from groq import Groq
    except ImportError:
        raise ImportError("Groq library not found. Run: pip install groq")
    
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY not found in .env file")
    
    client = Groq(api_key=api_key)
    
    # Models to try (in order of preference)
    models_to_try = [
        "llama-3.2-90b-text-preview",
        "llama-3.1-70b-versatile",
        "llama-3.1-8b-instant",
        "llama-3-70b-8192",
        "llama-3-8b-8192",
        "mixtral-8x7b-32768",
        "gemma-7b-it",
        "gemma2-9b-it",
    ]
    
    for model_name in models_to_try:
        try:
            # Try to create a completion with this model
            test_response = client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": "test"}],
                max_tokens=1,
                temperature=0.1
            )
            print(f"✅ Using model: {model_name}")
            return model_name
        except Exception as e:
            error_msg = str(e).lower()
            if "model" in error_msg or "not found" in error_msg or "decommissioned" in error_msg:
                continue
            else:
                raise
    
    raise Exception(f"No available chat models found. Tried: {models_to_try}")


def extract_booking_details(user_input):
    try:
        from groq import Groq
    except ImportError:
        raise ImportError("Groq library not found. Run: pip install groq")
    
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY not found in .env file")
    
    client = Groq(api_key=api_key)
    
    # Get available model dynamically
    model_id = get_available_chat_model()
    
    prompt = f"""
    Extract appointment details from the text.
    
    Return ONLY a valid JSON object with these exact fields:
    - name (string)
    - service (string)
    - date (string)
    - time (string)
    
    If any field is missing, use "Not specified" as the value.
    
    Example response format:
    {{"name": "John Doe", "service": "Haircut", "date": "May 25, 2026", "time": "3:00 PM"}}
    
    Text:
    {user_input}
    """
    
    message = client.chat.completions.create(
        model=model_id,
        messages=[
            {"role": "system", "content": "You are a helpful assistant that extracts appointment details from text and returns only valid JSON."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.5,
        max_tokens=1024
    )
    
    response_text = message.choices[0].message.content.strip()
    
    # Try to extract JSON from the response
    # First, try markdown code blocks
    if "```json" in response_text:
        start = response_text.find("```json") + 7
        end = response_text.find("```", start)
        if end != -1:
            response_text = response_text[start:end].strip()
    elif "```" in response_text:
        start = response_text.find("```") + 3
        end = response_text.find("```", start)
        if end != -1:
            response_text = response_text[start:end].strip()
    
    # If no code blocks, try to find JSON object in response
    if "{" in response_text:
        start = response_text.find("{")
        end = response_text.rfind("}") + 1
        if start != -1 and end > start:
            response_text = response_text[start:end].strip()
    
    return response_text