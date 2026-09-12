"""
================================================================================
                    ANIA AI - ENTERPRISE BACKEND (helpers.py)
                                [ PART 1 / 4 ]
================================================================================
"""

import os
import time
import requests
import concurrent.futures
from dotenv import load_dotenv

# .env থেকে সব API Key লোড করা
load_dotenv()

# ==============================================================================
# 1. API KEYS CONFIGURATION
# ==============================================================================
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
CEREBRAS_API_KEY = os.getenv("CEREBRAS_API_KEY")
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
SERPER_API_KEY = os.getenv("SERPER_API_KEY")
FIRECRAWL_API_KEY = os.getenv("FIRECRAWL_API_KEY")
JINA_API_KEY = os.getenv("JINA_API_KEY")
OCR_API_KEY = os.getenv("OCR_API_KEY")
STABILITY_API_KEY = os.getenv("STABILITY_API_KEY")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
ASSEMBLYAI_API_KEY = os.getenv("ASSEMBLYAI_API_KEY")

# ডিসপ্লে নেইম ম্যাপিং
MODEL_DISPLAY_NAMES = {
    "gemini": "Anis 1.0 Flash",
    "groq": "Anis 1.0 Turbo",
    "cerebras": "Anis 1.1 Flash",
    "mistral": "Anis 1.1 Pro",
    "openrouter": "Anis 1.2 Pro",
}

# ==============================================================================
# 2. TIMEOUT WRAPPER
# ==============================================================================
def call_with_timeout(func, *args, timeout=6, **kwargs):
    """ধীরগতির API-কে আটকে না রেখে দ্রুত পরবর্তী প্রোভাইডারে শিফট করে"""
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(func, *args, **kwargs)
        try:
            return future.result(timeout=timeout)
        except concurrent.futures.TimeoutError:
            print(f"[TIMEOUT] {func.__name__} {timeout}s সময়সীমা পার হয়েছে")
            return None
        except Exception as e:
            print(f"[API ERROR] {func.__name__} ব্যর্থ হয়েছে: {e}")
            return None
# ==============================================================================
#                                [ PART 2 / 4 ]
# ==============================================================================

# ==============================================================================
# 3. LLM API PROVIDERS
# ==============================================================================
def call_gemini(prompt):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    response = requests.post(url, json=payload, timeout=8)
    response.raise_for_status()
    data = response.json()
    return data["candidates"][0]["content"]["parts"][0]["text"]


def call_groq(prompt):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "user", "content": prompt}]
    }
    response = requests.post(url, json=payload, headers=headers, timeout=8)
    response.raise_for_status()
    data = response.json()
    return data["choices"][0]["message"]["content"]


def call_cerebras(prompt):
    url = "https://api.cerebras.ai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {CEREBRAS_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "llama-3.3-70b",
        "messages": [{"role": "user", "content": prompt}]
    }
    response = requests.post(url, json=payload, headers=headers, timeout=8)
    response.raise_for_status()
    data = response.json()
    return data["choices"][0]["message"]["content"]


def call_mistral(prompt):
    url = "https://api.mistral.ai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {MISTRAL_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "mistral-small-latest",
        "messages": [{"role": "user", "content": prompt}]
    }
    response = requests.post(url, json=payload, headers=headers, timeout=8)
    response.raise_for_status()
    data = response.json()
    return data["choices"][0]["message"]["content"]


def call_openrouter(prompt):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "meta-llama/llama-3.3-70b-instruct:free",
        "messages": [{"role": "user", "content": prompt}]
    }
    response = requests.post(url, json=payload, headers=headers, timeout=8)
    response.raise_for_status()
    data = response.json()
    return data["choices"][0]["message"]["content"]


# ==============================================================================
# 4. TASK CLASSIFICATION & FALLBACK CHAINS
# ==============================================================================
def classify_task(message):
    text = message.lower()
    code_keywords = ["code", "```", "function", "error", "python", "fix", "bug", "script", "কোড", "প্রোগ্রাম"]
    reasoning_keywords = ["calculate", "solve", "logic", "গণনা", "সমাধান", "+", "-", "="]
    search_keywords = ["latest", "today", "news", "current", "এখন", "আজ", "সাম্প্রতিক", "খবর"]

    if any(k in text for k in code_keywords):
        return "code"
    elif any(k in text for k in reasoning_keywords):
        return "reasoning"
    elif any(k in text for k in search_keywords):
        return "search"
    else:
        return "general"


TEXT_AI_CHAINS = {
    "code": [
        ("cerebras", call_cerebras),
        ("groq", call_groq),
        ("gemini", call_gemini),
        ("mistral", call_mistral),
        ("openrouter", call_openrouter),
    ],
    "general": [
        ("gemini", call_gemini),
        ("groq", call_groq),
        ("mistral", call_mistral),
        ("openrouter", call_openrouter),
        ("cerebras", call_cerebras),
    ],
    "reasoning": [
        ("cerebras", call_cerebras),
        ("mistral", call_mistral),
        ("gemini", call_gemini),
        ("groq", call_groq),
    ],
}


def run_text_ai_chain(prompt, task_type="general"):
    chain = TEXT_AI_CHAINS.get(task_type, TEXT_AI_CHAINS["general"])

    for provider_key, provider_func in chain:
        result = call_with_timeout(provider_func, prompt, timeout=6)
        if result:
            return {"answer": result, "provider_used": provider_key}

    return {"answer": None, "provider_used": None}
# ==============================================================================
#                                [ PART 3 / 4 ]
# ==============================================================================

# ==============================================================================
# 5. LIVE SEARCH & SCRAPING
# ==============================================================================
def call_tavily(query):
    url = "https://api.tavily.com/search"
    payload = {"api_key": TAVILY_API_KEY, "query": query, "max_results": 4}
    response = requests.post(url, json=payload, timeout=6)
    response.raise_for_status()
    results = response.json().get("results", [])
    combined = "\n".join([f"- {r.get('title')}: {r.get('content','')[:200]}" for r in results])
    return combined if combined else None


def call_serper(query):
    url = "https://google.serper.dev/search"
    headers = {"X-API-KEY": SERPER_API_KEY, "Content-Type": "application/json"}
    payload = {"q": query}
    response = requests.post(url, json=payload, headers=headers, timeout=6)
    response.raise_for_status()
    organic = response.json().get("organic", [])
    combined = "\n".join([f"- {r.get('title')}: {r.get('snippet','')}" for r in organic[:4]])
    return combined if combined else None


def run_web_search(query):
    chain = [("tavily", call_tavily), ("serper", call_serper)]
    for provider_key, provider_func in chain:
        result = call_with_timeout(provider_func, query, timeout=4)
        if result:
            return result
    return None


def call_firecrawl(url_to_scrape):
    api_url = "https://api.firecrawl.dev/v1/scrape"
    headers = {"Authorization": f"Bearer {FIRECRAWL_API_KEY}", "Content-Type": "application/json"}
    payload = {"url": url_to_scrape}
    response = requests.post(api_url, json=payload, headers=headers, timeout=8)
    response.raise_for_status()
    data = response.json()
    return data.get("data", {}).get("markdown")


def call_jina(url_to_scrape):
    api_url = f"https://r.jina.ai/{url_to_scrape}"
    headers = {"Authorization": f"Bearer {JINA_API_KEY}"}
    response = requests.get(api_url, headers=headers, timeout=8)
    response.raise_for_status()
    return response.text


def run_scrape(url_to_scrape):
    chain = [("firecrawl", call_firecrawl), ("jina", call_jina)]
    for provider_key, provider_func in chain:
        result = call_with_timeout(provider_func, url_to_scrape, timeout=5)
        if result:
            return result
    return None

# ==============================================================================
# 6. OCR, IMAGE GEN, VOICE & AUDIO
# ==============================================================================
def call_ocr(image_bytes):
    url = "https://api.ocr.space/parse/image"
    files = {"file": image_bytes}
    data = {"apikey": OCR_API_KEY, "language": "eng"}
    response = requests.post(url, files=files, data=data, timeout=8)
    response.raise_for_status()
    try:
        return response.json()["ParsedResults"][0]["ParsedText"]
    except Exception:
        return None


def call_stability_image_gen(prompt):
    url = "https://api.stability.ai/v2beta/stable-image/generate/core"
    headers = {"Authorization": f"Bearer {STABILITY_API_KEY}", "Accept": "image/*"}
    files = {"prompt": (None, prompt), "output_format": (None, "png")}
    response = requests.post(url, headers=headers, files=files, timeout=15)
    response.raise_for_status()
    return response.content


def call_elevenlabs_tts(text):
    voice_id = "21m00Tcm4TlvDq8ikWAM"
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    headers = {"xi-api-key": ELEVENLABS_API_KEY, "Content-Type": "application/json"}
    payload = {"text": text, "model_id": "eleven_multilingual_v2"}
    response = requests.post(url, json=payload, headers=headers, timeout=10)
    response.raise_for_status()
    return response.content


def call_assemblyai_stt(audio_file_path):
    headers = {"authorization": ASSEMBLYAI_API_KEY}
    with open(audio_file_path, "rb") as f:
        upload_response = requests.post(
            "https://api.assemblyai.com/v2/upload", headers=headers, data=f, timeout=10
        )
    audio_url = upload_response.json()["upload_url"]

    transcript_response = requests.post(
        "https://api.assemblyai.com/v2/transcript",
        json={"audio_url": audio_url},
        headers=headers, timeout=10
    )
    transcript_id = transcript_response.json()["id"]

    while True:
        polling = requests.get(
            f"https://api.assemblyai.com/v2/transcript/{transcript_id}",
            headers=headers, timeout=10
        ).json()
        if polling["status"] == "completed":
            return polling["text"]
        elif polling["status"] == "error":
            return None
        time.sleep(1)
# ==============================================================================
#                                [ PART 4 / 4 ]
# ==============================================================================

# ==============================================================================
# 7. MAIN INTERFACE FUNCTION (Direct Link with main.py)
# ==============================================================================
def generate_ai_response(prompt: str, model: str = "default", chat_history: list = None, web_search_enabled: bool = True, image_file=None) -> str:
    """
    main.py এর সাথে ১০০% সামঞ্জস্যপূর্ণ মূল ফাংশন।
    """
    if chat_history is None:
        chat_history = []

    # ১. ছবি প্রসেসিং (যদি থাকে)
    extra_context = ""
    if image_file is not None:
        try:
            image_bytes = image_file.read()
            ocr_text = call_with_timeout(call_ocr, image_bytes, timeout=6)
            if ocr_text:
                extra_context += f"\n[Image Extracted Context]:\n{ocr_text}"
        except Exception as e:
            print(f"[OCR Non-Fatal Error]: {e}")

    # ২. টাস্ক ক্লাসিফিকেশন
    task_type = classify_task(prompt)

    # ৩. প্রয়োজন অনুযায়ী রিয়েলটাইম ওয়েব সার্চ
    search_context = ""
    if web_search_enabled and task_type == "search":
        search_result = run_web_search(prompt)
        if search_result:
            search_context = f"\n[Live Web Search Context]:\n{search_result}"

    # ৪. পূর্বের চ্যাট হিস্ট্রি প্রম্পটে যুক্ত করা
    formatted_history = ""
    if chat_history:
        recent = chat_history[-6:]
        history_lines = []
        for msg in recent:
            role = "User" if msg.get("role") == "user" else "ANIA AI"
            history_lines.append(f"{role}: {msg.get('content', '')}")
        formatted_history = "Conversation History:\n" + "\n".join(history_lines) + "\n\n"

    # ৫. সম্পূর্ণ প্রম্পট প্রস্তুত করা
    final_prompt = f"{formatted_history}Current User Query: {prompt}{search_context}{extra_context}"

    # ৬. মাল্টি-প্রোভাইডার ফলব্যাক চেইন এক্সিকিউট করা
    result = run_text_ai_chain(final_prompt, task_type=task_type)

    # ৭. রেসপন্স চেক ও এরর রেইজ (ফেইল করলে main.py এর স্পেশাল কার্ড ওপেন হবে)
    if not result or result.get("provider_used") is None or not result.get("answer"):
        raise RuntimeError("All internal neural pipelines failed to generate completion.")

    return result["answer"]

# অ্যালিয়াস (Backwards Compatibility)
get_ai_response = generate_ai_response