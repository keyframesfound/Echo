"""
Web search module using SerpAPI.
"""
import os
import requests

SERPAPI_API_KEY = os.getenv("SERPAPI_API_KEY")
SEARCH_URL = "https://serpapi.com/search"

class SerpAPIError(Exception):
    pass

def search_web(query: str) -> str:
    """
    Search the web using SerpAPI and return the top result snippet.
    Args:
        query (str): Search query.
    Returns:
        str: Top result snippet or error message.
    Raises:
        SerpAPIError: If the API call fails.
    """
    if not SERPAPI_API_KEY:
        raise SerpAPIError("SERPAPI_API_KEY is not set in the environment.")
    params = {
        "q": query,
        "api_key": SERPAPI_API_KEY,
        "engine": "google"
    }
    try:
        response = requests.get(SEARCH_URL, params=params, timeout=20)
        response.raise_for_status()
        data = response.json()
        if "answer_box" in data and "answer" in data["answer_box"]:
            return data["answer_box"]["answer"]
        elif "organic_results" in data and data["organic_results"]:
            return data["organic_results"][0].get("snippet", "[No snippet found]")
        else:
            return "[No results found]"
    except Exception as e:
        raise SerpAPIError(f"SerpAPI error: {e}") 