import requests
import json

# Ollama Endpoint
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "deepseek-r1:7b"


# ------------------------------------------------------------
# New: Structured JSON Output Function (For OptiGuide Router)
# ------------------------------------------------------------
def get_json_output(system_instruction: str, user_prompt: str) -> str:
    """
    Calls DeepSeek-R1 with explicit system instructions to enforce strict JSON output.
    Returns the raw JSON string or an error indicator.
    """
    
    # Template designed to enforce adherence to the JSON format.
    full_prompt = (
        f"You are a strict, helpful AI assistant. Your only task is to follow the instruction and return the output as a valid JSON object. "
        f"INSTRUCTION:\n{system_instruction}\n\n"
        f"USER INPUT:\n{user_prompt}\n\n"
        f"Return ONLY the JSON object, do not include any other text, markdown formatting, or explanation."
    )

    payload = {
        "model": MODEL_NAME,
        "prompt": full_prompt,
        "stream": False,
        # Low temperature encourages deterministic, structured output
        "temperature": 0.2 
    }

    try:
        r = requests.post(OLLAMA_URL, json=payload)
        r.raise_for_status()
        raw = r.json().get("response", "")
        
        # Aggressive cleaning to find and return only the first valid JSON block
        start = raw.find('{')
        end = raw.rfind('}')
        
        if start != -1 and end != -1 and end > start:
            # Return only the content between the first { and last }
            return raw[start:end + 1]
            
        return "JSON_PARSE_ERROR" 

    except Exception as e:
        return f"ERROR: {e}"


# ------------------------------------------------------------
# Main Chat Completion Interface (kept for legacy/general use)
# ------------------------------------------------------------
def chat_completion(prompt: str) -> str:
    """
    A general-purpose completion that performs cleanup.
    """
    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False,
    }

    try:
        r = requests.post(OLLAMA_URL, json=payload)
        r.raise_for_status()
        raw = r.json().get("response", "")

        # 1. Remove <think> blocks entirely
        if "<think>" in raw:
            raw = raw.split("<think>")[0]

        # 2. Remove any leftover tags
        for tag in ["</think>", "<response>", "</response>", "<final>", "</final>"]:
            raw = raw.replace(tag, "")

        # 3. Strip whitespace noise
        return raw.strip()

    except Exception as e:
        return f"ERROR: {e}"
    
# NOTE: ask_llm function was removed as it was redundant with chat_completion.