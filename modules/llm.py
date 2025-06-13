"""
LLM integration module using OpenRouter API (free models only).
"""
import os
import requests

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
# Free models (update as needed)
FREE_MODELS = [
    "nousresearch/nous-capybara-7b:free",
    "meta-llama/llama-3.3-70b-instruct:free",
    "google/gemma-3-27b-it:free"
]
DEFAULT_MODEL = "meta-llama/llama-3.3-70b-instruct:free"

class OpenRouterError(Exception):
    pass

def query_llm(prompt: str, model: str = DEFAULT_MODEL) -> str:
    """
    Query the OpenRouter API with a prompt using a free model.
    Args:
        prompt (str): The user's prompt.
        model (str): The model to use (must be in FREE_MODELS).
    Returns:
        str: The LLM's response.
    Raises:
        OpenRouterError: If the API call fails or the model is not free.
    """
    if model not in FREE_MODELS:
        raise OpenRouterError(f"Model '{model}' is not a free model on OpenRouter.")
    if not OPENROUTER_API_KEY:
        raise OpenRouterError("OPENROUTER_API_KEY is not set in the environment.")
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": model,
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }
    try:
        response = requests.post(OPENROUTER_API_URL, headers=headers, json=data, timeout=30)
        response.raise_for_status()
        result = response.json()
        return result["choices"][0]["message"]["content"]
    except Exception as e:
        raise OpenRouterError(f"OpenRouter API error: {e}") 