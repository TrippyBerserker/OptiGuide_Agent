import requests
import json

# Ollama Endpoint
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "deepseek-r1:7b"


# ------------------------------------------------------------
# RAW single-shot LLM call (rarely used)
# ------------------------------------------------------------
def ask_llm(prompt: str) -> str:
    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False
    }

    try:
        r = requests.post(OLLAMA_URL, json=payload)
        r.raise_for_status()
        out = r.json().get("response", "")
        return out.strip()
    except:
        return "LLM_ERROR"


# ------------------------------------------------------------
# Main Chat Completion Interface (DeepSeek-R1 safe wrapper)
# ------------------------------------------------------------
def chat_completion(prompt: str) -> str:
    """
    - Calls DeepSeek-R1 via Ollama
    - Removes chain-of-thought (<think>)
    - Removes XML-like tags
    - Returns plain text ONLY
    - Avoids hallucinated formatting
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
