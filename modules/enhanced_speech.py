"""
Enhanced speech recognition module using OpenRouter Whisper (free model).
"""
import os
import requests

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
WHISPER_MODEL = "openai/whisper"
API_URL = "https://openrouter.ai/api/v1/audio/transcriptions"

class OpenRouterWhisperError(Exception):
    pass

def transcribe_audio(audio_path: str) -> str:
    """
    Transcribe audio file to text using OpenRouter Whisper.
    Args:
        audio_path (str): Path to the audio file.
    Returns:
        str: Transcribed text.
    Raises:
        OpenRouterWhisperError: If the API call fails.
    """
    if not OPENROUTER_API_KEY:
        raise OpenRouterWhisperError("OPENROUTER_API_KEY is not set in the environment.")
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}"
    }
    files = {
        "file": open(audio_path, "rb")
    }
    data = {
        "model": WHISPER_MODEL
    }
    try:
        response = requests.post(API_URL, headers=headers, files=files, data=data, timeout=60)
        response.raise_for_status()
        result = response.json()
        return result.get("text", "[No transcription returned]")
    except Exception as e:
        raise OpenRouterWhisperError(f"OpenRouter Whisper API error: {e}") 