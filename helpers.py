# ============================================
# helper.py — PART 1 START
# (এই পার্টটা ফাইলের একদম শুরুতে বসাবেন)
# ============================================

import os
import time
import requests
import concurrent.futures
from dotenv import load_dotenv

# .env ফাইল থেকে সব key লোড হচ্ছে
load_dotenv()

# ===== সব API KEY লোড করা হচ্ছে =====
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

# ===== ব্র্যান্ডেড মডেল নেম ম্যাপিং (ইউজারকে যা দেখানো হবে) =====
MODEL_DISPLAY_NAMES = {
    "gemini": "Anis 1.0 Flash",
    "groq": "Anis 1.0 Turbo",
    "cerebras": "Anis 1.1 Flash",
    "mistral": "Anis 1.1 Pro",
    "openrouter": "Anis 1.2 Pro",
}

# ===== টাইমআউট রেপার ফাংশন (প্রতিটা প্রোভাইডারে ২ সেকেন্ড লিমিট) =====
def call_with_timeout(func, *args, timeout=2, **kwargs):
    """
    এই ফাংশনটা কোনো একটা provider ফাংশনকে কল করে,
    কিন্তু timeout সেকেন্ডের বেশি সময় নিলে সেটা বাতিল করে
    None রিটার্ন করবে (তখন পরের provider ট্রাই হবে)
    """
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(func, *args, **kwargs)
        try:
            result = future.result(timeout=timeout)
            return result
        except concurrent.futures.TimeoutError:
            print(f"[TIMEOUT] {func.__name__} {timeout} সেকেন্ডে রেসপন্স দেয়নি")
            return None
        except Exception as e:
            print(f"[ERROR] {func.__name__} এরর দিয়েছে: {e}")
            return None

# ============================================
# helper.py — PART 1 END
# (এর নিচে পরের পার্ট জোড়া দেবেন)
# ============================================
# ============================================
# helper.py — PART 2 START
# (Part 1-এর ঠিক নিচে জোড়া দেবেন)
# ============================================

# ===== 1. GEMINI প্রোভাইডার =====
def call_gemini(prompt):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}]
    }
    response = requests.post(url, json=payload, timeout=5)
    response.raise_for_status()
    data = response.json()
    return data["candidates"][0]["content"]["parts"][0]["text"]


# ===== 2. GROQ প্রোভাইডার =====
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
    response = requests.post(url, json=payload, headers=headers, timeout=5)
    response.raise_for_status()
    data = response.json()
    return data["choices"][0]["message"]["content"]


# ===== 3. CEREBRAS প্রোভাইডার =====
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
    response = requests.post(url, json=payload, headers=headers, timeout=5)
    response.raise_for_status()
    data = response.json()
    return data["choices"][0]["message"]["content"]


# ===== 4. MISTRAL প্রোভাইডার =====
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
    response = requests.post(url, json=payload, headers=headers, timeout=5)
    response.raise_for_status()
    data = response.json()
    return data["choices"][0]["message"]["content"]


# ===== 5. OPENROUTER প্রোভাইডার =====
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
    response = requests.post(url, json=payload, headers=headers, timeout=5)
    response.raise_for_status()
    data = response.json()
    return data["choices"][0]["message"]["content"]

# ============================================
# helper.py — PART 2 END
# (এর নিচে পরের পার্ট জোড়া দেবেন)
# ============================================
# ============================================
# helper.py — PART 3 START (টাস্ক ক্লাসিফায়ার + টেক্সট AI ফলব্যাক চেইন)
# (Part 2-এর ঠিক নিচে জোড়া দেবেন)
# ============================================

# ===== টাস্ক ক্লাসিফায়ার: মেসেজ দেখে ক্যাটেগরি বোঝা =====
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


# ===== প্রতিটা ক্যাটেগরির জন্য প্রোভাইডার চেইন (ক্রম অনুযায়ী) =====
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


# ===== মূল ফলব্যাক চেইন রানার (২ সেকেন্ড টাইমআউট প্রতিটায়) =====
def run_text_ai_chain(prompt, task_type="general"):
    chain = TEXT_AI_CHAINS.get(task_type, TEXT_AI_CHAINS["general"])

    for provider_key, provider_func in chain:
        result = call_with_timeout(provider_func, prompt, timeout=2)
        if result:
            return {
                "answer": result,
                "provider_used": provider_key
            }

    return {
        "answer": "⚠️ এই মুহূর্তে কোনো AI সার্ভিস উত্তর দিতে পারছে না। একটু পরে চেষ্টা করুন।",
        "provider_used": None
    }

# ============================================
# helper.py — PART 3 END
# ============================================


# ============================================
# helper.py — PART 4 START (ওয়েব সার্চ ফলব্যাক: Tavily → Serper)
# ============================================

def call_tavily(query):
    url = "https://api.tavily.com/search"
    payload = {"api_key": TAVILY_API_KEY, "query": query, "max_results": 5}
    response = requests.post(url, json=payload, timeout=5)
    response.raise_for_status()
    data = response.json()
    results = data.get("results", [])
    combined = "\n".join([f"- {r.get('title')}: {r.get('content','')[:200]}" for r in results])
    return combined if combined else None


def call_serper(query):
    url = "https://google.serper.dev/search"
    headers = {"X-API-KEY": SERPER_API_KEY, "Content-Type": "application/json"}
    payload = {"q": query}
    response = requests.post(url, json=payload, headers=headers, timeout=5)
    response.raise_for_status()
    data = response.json()
    organic = data.get("organic", [])
    combined = "\n".join([f"- {r.get('title')}: {r.get('snippet','')}" for r in organic[:5]])
    return combined if combined else None


def run_web_search(query):
    chain = [("tavily", call_tavily), ("serper", call_serper)]
    for provider_key, provider_func in chain:
        result = call_with_timeout(provider_func, query, timeout=2)
        if result:
            return result
    return None

# ============================================
# helper.py — PART 4 END
# ============================================


# ============================================
# helper.py — PART 5 START (স্ক্র্যাপিং ফলব্যাক: Firecrawl → Jina, OCR, ছবি জেনারেশন)
# ============================================

def call_firecrawl(url_to_scrape):
    api_url = "https://api.firecrawl.dev/v1/scrape"
    headers = {"Authorization": f"Bearer {FIRECRAWL_API_KEY}", "Content-Type": "application/json"}
    payload = {"url": url_to_scrape}
    response = requests.post(api_url, json=payload, headers=headers, timeout=5)
    response.raise_for_status()
    data = response.json()
    return data.get("data", {}).get("markdown")


def call_jina(url_to_scrape):
    api_url = f"https://r.jina.ai/{url_to_scrape}"
    headers = {"Authorization": f"Bearer {JINA_API_KEY}"}
    response = requests.get(api_url, headers=headers, timeout=5)
    response.raise_for_status()
    return response.text


def run_scrape(url_to_scrape):
    chain = [("firecrawl", call_firecrawl), ("jina", call_jina)]
    for provider_key, provider_func in chain:
        result = call_with_timeout(provider_func, url_to_scrape, timeout=2)
        if result:
            return result
    return None


def call_ocr(image_bytes):
    url = "https://api.ocr.space/parse/image"
    files = {"file": image_bytes}
    data = {"apikey": OCR_API_KEY, "language": "eng"}
    response = requests.post(url, files=files, data=data, timeout=5)
    response.raise_for_status()
    result = response.json()
    try:
        return result["ParsedResults"][0]["ParsedText"]
    except (KeyError, IndexError):
        return None


def call_stability_image_gen(prompt):
    url = "https://api.stability.ai/v2beta/stable-image/generate/core"
    headers = {"Authorization": f"Bearer {STABILITY_API_KEY}", "Accept": "image/*"}
    files = {"prompt": (None, prompt), "output_format": (None, "png")}
    response = requests.post(url, headers=headers, files=files, timeout=15)
    response.raise_for_status()
    return response.content  # ছবি বাইনারি ডেটা

# ============================================
# helper.py — PART 5 END
# ============================================


# ============================================
# helper.py — PART 6 START (ভয়েস: ElevenLabs TTS, AssemblyAI STT)
# ============================================

def call_elevenlabs_tts(text):
    voice_id = "21m00Tcm4TlvDq8ikWAM"  # ডিফল্ট ভয়েস, চাইলে বদলানো যাবে
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    headers = {"xi-api-key": ELEVENLABS_API_KEY, "Content-Type": "application/json"}
    payload = {"text": text, "model_id": "eleven_multilingual_v2"}
    response = requests.post(url, json=payload, headers=headers, timeout=10)
    response.raise_for_status()
    return response.content  # অডিও বাইনারি ডেটা


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

# ============================================
# helper.py — PART 6 END
# ============================================


# ============================================
# helper.py — PART 7 START (মূল ফাংশন — main.py এটাকেই কল করবে)
# ============================================

def get_ai_response(user_message, web_search_enabled=True, image_file=None):
    """
    main.py শুধু এই একটা ফাংশনকেই কল করবে।
    এর ভেতরেই টাস্ক ক্লাসিফিকেশন, ফলব্যাক চেইন, সার্চ — সবকিছু ঘটবে।
    """

    # যদি ছবি সংযুক্ত থাকে, প্রথমে OCR করে টেক্সট বের করা
    extra_context = ""
    if image_file is not None:
        image_bytes = image_file.read()
        ocr_text = call_with_timeout(call_ocr, image_bytes, timeout=5)
        if ocr_text:
            extra_context += f"\n[ছবি থেকে পাওয়া টেক্সট]: {ocr_text}"

    # টাস্ক ক্যাটেগরি বোঝা
    task_type = classify_task(user_message)

    # ওয়েব সার্চ প্রয়োজন হলে ও অন থাকলে
    search_context = ""
    if web_search_enabled and task_type == "search":
        search_result = run_web_search(user_message)
        if search_result:
            search_context = f"\n[ওয়েব সার্চ থেকে পাওয়া তথ্য]:\n{search_result}"

    # চূড়ান্ত প্রম্পট বানানো (মূল প্রশ্ন + সার্চ কনটেক্সট + ছবির কনটেক্সট)
    final_prompt = user_message + search_context + extra_context

    # টেক্সট AI ফলব্যাক চেইন কল করা
    result = run_text_ai_chain(final_prompt, task_type=task_type)

    return result

# ============================================
# helper.py — PART 7 END
# helper.py এখানেই সম্পূর্ণ
# ============================================