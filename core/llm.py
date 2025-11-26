import requests
import json

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "deepseek-r1:7b"


def ask_llm(prompt: str) -> str:
    """
    Simple 1-shot LLM call.
    Returns raw text only.
    """
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


def chat_completion(prompt: str) -> str:
    """
    For multi-step instructions (schema detection, explanations).
    Always returns CLEAN text (no XML, no thinking blocks).
    Removes DeepSeek R1 chain-of-thought automatically.
    """

    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False
    }

    try:
        r = requests.post(OLLAMA_URL, json=payload)
        r.raise_for_status()
        raw = r.json().get("response", "")

        # REMOVE DeepSeek hidden reasoning (between <think> tags)
        clean = raw.split("<think>")[0].strip()
        return clean

    except Exception as e:
        return f"ERROR: {e}"
