# Handles local LLM integration with Ollama

import requests
import base64

# OpenRouter API integration (free models only)
OPENROUTER_API_KEY = "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"
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
# Use a free model (see https://openrouter.ai/models for up-to-date list)
OPENROUTER_MODEL = "nousresearch/nous-capybara-7b:free"

# Smartest free text model (as of June 2025)
TEXT_MODEL = "meta-llama/llama-3.3-70b-instruct:free"
# Best free vision model
VISION_MODEL = "google/gemma-3-27b-it:free"

# Use this for text-only queries
def generate_text_response(prompt):
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    messages = [
        {"role": "system", "content": "You are a helpful, expert AI like Jarvis in IronMan. Answer as thoroughly and accurately as possible. Answer in short concise sentences and be causal about it"},
        {"role": "user", "content": prompt}
    ]
    payload = {
        "model": TEXT_MODEL,
        "messages": messages,
        "max_tokens": 512
    }
    try:
        response = requests.post(OPENROUTER_API_URL, headers=headers, json=payload, timeout=60)
        if response.status_code == 400:
            return f"[LLM Error: 400 Bad Request. Check if the model '{TEXT_MODEL}' is available and your payload is valid. Response: {response.text}]"
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]
    except Exception as e:
        return f"[LLM Error: {e}]"

# Use this for vision queries (returns a detailed description of the image)
def generate_vision_description(image_bytes, prompt=None):
    import base64
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    sys_prompt = "You are an expert at describing images for technical, engineering, and general purposes. Be as detailed as possible."
    user_content = []
    if prompt:
        user_content.append({"type": "text", "text": prompt})
    img_b64 = base64.b64encode(image_bytes).decode("utf-8")
    user_content.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}})
    messages = [
        {"role": "system", "content": sys_prompt},
        {"role": "user", "content": user_content}
    ]
    payload = {
        "model": VISION_MODEL,
        "messages": messages,
        "max_tokens": 512
    }
    try:
        response = requests.post(OPENROUTER_API_URL, headers=headers, json=payload, timeout=60)
        if response.status_code == 400:
            return f"[Vision LLM Error: 400 Bad Request. Check if the model '{VISION_MODEL}' is available and your payload is valid. Response: {response.text}]"
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]
    except Exception as e:
        return f"[Vision LLM Error: {e}]"

# Hybrid: decide which to use
def generate_response(prompt, image_bytes=None):
    if image_bytes is not None:
        # Step 1: Get vision model's detailed description
        vision_desc = generate_vision_description(image_bytes, prompt)
        # Step 2: Ask the text model to reason about the image and user question
        combo_prompt = (
            f"The user asked: {prompt}\n"
            f"Here is a detailed description of the image: {vision_desc}\n"
            "Based on both, provide the best possible answer."
        )
        return generate_text_response(combo_prompt)
    else:
        return generate_text_response(prompt)
