"""
================================================================================
                    ANIS AI - ENTERPRISE BACKEND
                         helpers.py - PART 1/2
================================================================================
"""

import os
import time
import requests
import concurrent.futures
from dotenv import load_dotenv

load_dotenv()


# ==============================================================================
# 1. API KEYS
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


# ==============================================================================
# 2. MODEL CONFIGURATION
# ==============================================================================

GEMINI_MODEL = "gemini-2.5-flash"

GROQ_MODEL = "openai/gpt-oss-120b"

CEREBRAS_MODEL = "llama-3.3-70b"

MISTRAL_MODEL = "mistral-small-latest"

OPENROUTER_MODEL = "meta-llama/llama-3.3-70b-instruct:free"


# ==============================================================================
# 3. DISPLAY NAMES
# ==============================================================================

MODEL_DISPLAY_NAMES = {
    "gemini": "Anis 1.0 Flash",
    "groq": "Anis 1.0 Turbo",
    "cerebras": "Anis 1.1 Flash",
    "mistral": "Anis 1.1 Pro",
    "openrouter": "Anis 1.2 Pro",
}


# ==============================================================================
# 4. TIMEOUT WRAPPER
# ==============================================================================

def call_with_timeout(func, *args, timeout=10, **kwargs):

    with concurrent.futures.ThreadPoolExecutor(
        max_workers=1
    ) as executor:

        future = executor.submit(
            func,
            *args,
            **kwargs
        )

        try:

            result = future.result(
                timeout=timeout
            )

            if (
                result
                and isinstance(result, str)
                and result.strip()
            ):
                return result.strip()

            print(
                f"[EMPTY RESPONSE] "
                f"{func.__name__}"
            )

            return None

        except concurrent.futures.TimeoutError:

            print(
                f"[TIMEOUT] "
                f"{func.__name__} "
                f"exceeded {timeout}s"
            )

            return None

        except Exception as e:

            print(
                f"[API ERROR] "
                f"{func.__name__}: "
                f"{type(e).__name__}: {e}"
            )

            return None


# ==============================================================================
# 5. GEMINI
# ==============================================================================

def call_gemini(prompt):

    if not GEMINI_API_KEY:
        print("[GEMINI] API key missing")
        return None

    url = (
        "https://generativelanguage.googleapis.com/"
        f"v1beta/models/{GEMINI_MODEL}:generateContent"
        f"?key={GEMINI_API_KEY}"
    )

    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": prompt
                    }
                ]
            }
        ]
    }

    response = requests.post(
        url,
        json=payload,
        timeout=10
    )

    if not response.ok:

        print(
            f"[GEMINI] HTTP "
            f"{response.status_code}: "
            f"{response.text[:1000]}"
        )

        response.raise_for_status()

    data = response.json()

    candidates = data.get(
        "candidates",
        []
    )

    if not candidates:
        raise RuntimeError(
            "Gemini returned no candidates."
        )

    parts = (
        candidates[0]
        .get("content", {})
        .get("parts", [])
    )

    text = ""

    for part in parts:

        if isinstance(part, dict):

            text += part.get(
                "text",
                ""
            )

    text = text.strip()

    if not text:
        raise RuntimeError(
            "Gemini returned empty text."
        )

    return text


# ==============================================================================
# 6. GROQ
# ==============================================================================

def call_groq(prompt):

    if not GROQ_API_KEY:
        print("[GROQ] API key missing")
        return None

    url = (
        "https://api.groq.com/"
        "openai/v1/chat/completions"
    )

    headers = {
        "Authorization": (
            f"Bearer {GROQ_API_KEY}"
        ),
        "Content-Type": "application/json"
    }

    payload = {
        "model": GROQ_MODEL,
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ],
        "temperature": 0.2
    }

    response = requests.post(
        url,
        json=payload,
        headers=headers,
        timeout=10
    )

    if not response.ok:

        print(
            f"[GROQ] HTTP "
            f"{response.status_code}: "
            f"{response.text[:1000]}"
        )

        response.raise_for_status()

    data = response.json()

    choices = data.get(
        "choices",
        []
    )

    if not choices:
        raise RuntimeError(
            "Groq returned no choices."
        )

    text = (
        choices[0]
        .get("message", {})
        .get("content", "")
    )

    if not text:
        raise RuntimeError(
            "Groq returned empty text."
        )

    return text.strip()


# ==============================================================================
# 7. CEREBRAS
# ==============================================================================

def call_cerebras(prompt):

    if not CEREBRAS_API_KEY:
        print("[CEREBRAS] API key missing")
        return None

    url = (
        "https://api.cerebras.ai/"
        "v1/chat/completions"
    )

    headers = {
        "Authorization": (
            f"Bearer {CEREBRAS_API_KEY}"
        ),
        "Content-Type": "application/json"
    }

    payload = {
        "model": CEREBRAS_MODEL,
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ],
        "temperature": 0.2
    }

    response = requests.post(
        url,
        json=payload,
        headers=headers,
        timeout=10
    )

    if not response.ok:

        print(
            f"[CEREBRAS] HTTP "
            f"{response.status_code}: "
            f"{response.text[:1000]}"
        )

        response.raise_for_status()

    data = response.json()

    choices = data.get(
        "choices",
        []
    )

    if not choices:
        raise RuntimeError(
            "Cerebras returned no choices."
        )

    text = (
        choices[0]
        .get("message", {})
        .get("content", "")
    )

    if not text:
        raise RuntimeError(
            "Cerebras returned empty text."
        )

    return text.strip()


# ==============================================================================
# 8. MISTRAL
# ==============================================================================

def call_mistral(prompt):

    if not MISTRAL_API_KEY:
        print("[MISTRAL] API key missing")
        return None

    url = (
        "https://api.mistral.ai/"
        "v1/chat/completions"
    )

    headers = {
        "Authorization": (
            f"Bearer {MISTRAL_API_KEY}"
        ),
        "Content-Type": "application/json"
    }

    payload = {
        "model": MISTRAL_MODEL,
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ],
        "temperature": 0.2
    }

    response = requests.post(
        url,
        json=payload,
        headers=headers,
        timeout=10
    )

    if not response.ok:

        print(
            f"[MISTRAL] HTTP "
            f"{response.status_code}: "
            f"{response.text[:1000]}"
        )

        response.raise_for_status()

    data = response.json()

    choices = data.get(
        "choices",
        []
    )

    if not choices:
        raise RuntimeError(
            "Mistral returned no choices."
        )

    text = (
        choices[0]
        .get("message", {})
        .get("content", "")
    )

    if not text:
        raise RuntimeError(
            "Mistral returned empty text."
        )

    return text.strip()


# ==============================================================================
# 9. OPENROUTER
# ==============================================================================

def call_openrouter(prompt):

    if not OPENROUTER_API_KEY:
        print("[OPENROUTER] API key missing")
        return None

    url = (
        "https://openrouter.ai/"
        "api/v1/chat/completions"
    )

    headers = {
        "Authorization": (
            f"Bearer {OPENROUTER_API_KEY}"
        ),
        "Content-Type": "application/json",
        "HTTP-Referer": (
            "https://anisur-mcq-2026.streamlit.app/"
        ),
        "X-Title": "Anis AI"
    }

    payload = {
        "model": OPENROUTER_MODEL,
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ],
        "temperature": 0.2
    }

    response = requests.post(
        url,
        json=payload,
        headers=headers,
        timeout=10
    )

    if not response.ok:

        print(
            f"[OPENROUTER] HTTP "
            f"{response.status_code}: "
            f"{response.text[:1000]}"
        )

        response.raise_for_status()

    data = response.json()

    choices = data.get(
        "choices",
        []
    )

    if not choices:
        raise RuntimeError(
            "OpenRouter returned no choices."
        )

    text = (
        choices[0]
        .get("message", {})
        .get("content", "")
    )

    if not text:
        raise RuntimeError(
            "OpenRouter returned empty text."
        )

    return text.strip()


# ==============================================================================
# 10. TASK CLASSIFICATION
# ==============================================================================

def classify_task(message):

    text = str(message).lower()

    code_keywords = [
        "code",
        "```",
        "function",
        "error",
        "python",
        "fix",
        "bug",
        "script",
        "কোড",
        "প্রোগ্রাম",
        "ত্রুটি",
        "ঠিক কর"
    ]

    reasoning_keywords = [
        "calculate",
        "solve",
        "logic",
        "গণনা",
        "সমাধান",
        "যোগ",
        "বিয়োগ",
        "+",
        "-",
        "="
    ]

    search_keywords = [
        "latest",
        "today",
        "news",
        "current",
        "এখন",
        "আজ",
        "সাম্প্রতিক",
        "খবর"
    ]

    if any(
        k in text
        for k in code_keywords
    ):
        return "code"

    if any(
        k in text
        for k in reasoning_keywords
    ):
        return "reasoning"

    if any(
        k in text
        for k in search_keywords
    ):
        return "search"

    return "general"


# ==============================================================================
# 11. FALLBACK CHAINS
# ==============================================================================

TEXT_AI_CHAINS = {

    "code": [
        ("groq", call_groq),
        ("cerebras", call_cerebras),
        ("gemini", call_gemini),
        ("mistral", call_mistral),
        ("openrouter", call_openrouter)
    ],

    "general": [
        ("gemini", call_gemini),
        ("groq", call_groq),
        ("cerebras", call_cerebras),
        ("mistral", call_mistral),
        ("openrouter", call_openrouter)
    ],

    "reasoning": [
        ("cerebras", call_cerebras),
        ("gemini", call_gemini),
        ("groq", call_groq),
        ("mistral", call_mistral),
        ("openrouter", call_openrouter)
    ],

    "search": [
        ("gemini", call_gemini),
        ("groq", call_groq),
        ("cerebras", call_cerebras),
        ("mistral", call_mistral),
        ("openrouter", call_openrouter)
    ]
}


# ==============================================================================
# 12. RUN FALLBACK
# ==============================================================================

def run_text_ai_chain(
    prompt,
    task_type="general"
):

    chain = TEXT_AI_CHAINS.get(
        task_type,
        TEXT_AI_CHAINS["general"]
    )

    print(
        f"[AI CHAIN] Task: {task_type}"
    )

    for provider_key, provider_func in chain:

        print(
            f"[AI] Trying: "
            f"{provider_key}"
        )

        result = call_with_timeout(
            provider_func,
            prompt,
            timeout=10
        )

        if result:

            print(
                f"[AI] SUCCESS: "
                f"{provider_key}"
            )

            return {
                "answer": result,
                "provider_used": provider_key
            }

        print(
            f"[AI] FAILED: "
            f"{provider_key} "
            f"→ next provider"
        )

    print(
        "[AI] ALL PROVIDERS FAILED"
    )

    return {
        "answer": None,
        "provider_used": None
    }
# =============================================================================
# ANIS AI - ENTERPRISE BACKEND
# helpers.py - SECOND PART (PART 2/2)
# =============================================================================


# -----------------------------------------------------------------------------
# WEB SEARCH
# -----------------------------------------------------------------------------

def call_tavily(query):
    if not TAVILY_API_KEY:
        return None

    try:
        url = "https://api.tavily.com/search"

        payload = {
            "api_key": TAVILY_API_KEY,
            "query": query,
            "search_depth": "advanced",
            "max_results": 5,
            "include_answer": True
        }

        response = requests.post(
            url,
            json=payload,
            timeout=15
        )

        if not response.ok:
            print(
                f"[TAVILY] HTTP {response.status_code}: "
                f"{response.text[:1000]}"
            )
            return None

        data = response.json()

        answer = data.get("answer")
        if answer:
            return answer.strip()

        results = data.get("results", [])

        if not results:
            return None

        text_parts = []

        for item in results:
            title = item.get("title", "")
            content = item.get("content", "")

            if title:
                text_parts.append(title)

            if content:
                text_parts.append(content)

        final_text = "\n\n".join(text_parts)

        return final_text[:12000].strip() or None

    except Exception as e:
        print(f"[TAVILY ERROR] {type(e).__name__}: {e}")
        return None


def call_serper(query):
    if not SERPER_API_KEY:
        return None

    try:
        url = "https://google.serper.dev/search"

        headers = {
            "X-API-KEY": SERPER_API_KEY,
            "Content-Type": "application/json"
        }

        payload = {
            "q": query,
            "num": 5
        }

        response = requests.post(
            url,
            json=payload,
            headers=headers,
            timeout=15
        )

        if not response.ok:
            print(
                f"[SERPER] HTTP {response.status_code}: "
                f"{response.text[:1000]}"
            )
            return None

        data = response.json()

        results = data.get("organic", [])

        if not results:
            return None

        text_parts = []

        for item in results:
            title = item.get("title", "")
            snippet = item.get("snippet", "")

            if title:
                text_parts.append(title)

            if snippet:
                text_parts.append(snippet)

        final_text = "\n\n".join(text_parts)

        return final_text[:12000].strip() or None

    except Exception as e:
        print(f"[SERPER ERROR] {type(e).__name__}: {e}")
        return None


def run_web_search(query):
    """
    Web search fallback:
    Tavily → Serper
    """

    print(f"[WEB SEARCH] Query: {query}")

    result = call_tavily(query)

    if result:
        print("[WEB SEARCH] SUCCESS: Tavily")
        return result

    print("[WEB SEARCH] Tavily failed → trying Serper")

    result = call_serper(query)

    if result:
        print("[WEB SEARCH] SUCCESS: Serper")
        return result

    print("[WEB SEARCH] ALL SEARCH PROVIDERS FAILED")

    return None


# -----------------------------------------------------------------------------
# WEB SCRAPING
# -----------------------------------------------------------------------------

def call_firecrawl(url):
    if not FIRECRAWL_API_KEY:
        return None

    try:
        endpoint = "https://api.firecrawl.dev/v1/scrape"

        headers = {
            "Authorization": f"Bearer {FIRECRAWL_API_KEY}",
            "Content-Type": "application/json"
        }

        payload = {
            "url": url,
            "formats": ["markdown"]
        }

        response = requests.post(
            endpoint,
            json=payload,
            headers=headers,
            timeout=20
        )

        if not response.ok:
            print(
                f"[FIRECRAWL] HTTP {response.status_code}: "
                f"{response.text[:1000]}"
            )
            return None

        data = response.json()

        result = data.get("data", {})

        markdown = result.get("markdown")

        if markdown:
            return markdown[:20000].strip()

        return None

    except Exception as e:
        print(f"[FIRECRAWL ERROR] {type(e).__name__}: {e}")
        return None


def call_jina(url):
    if not JINA_API_KEY:
        return None

    try:
        endpoint = f"https://r.jina.ai/{url}"

        headers = {
            "Authorization": f"Bearer {JINA_API_KEY}"
        }

        response = requests.get(
            endpoint,
            headers=headers,
            timeout=20
        )

        if not response.ok:
            print(
                f"[JINA] HTTP {response.status_code}: "
                f"{response.text[:1000]}"
            )
            return None

        text = response.text.strip()

        return text[:20000] if text else None

    except Exception as e:
        print(f"[JINA ERROR] {type(e).__name__}: {e}")
        return None


def run_scrape(url):
    """
    Scraping fallback:
    Firecrawl → Jina
    """

    print(f"[SCRAPE] URL: {url}")

    result = call_firecrawl(url)

    if result:
        print("[SCRAPE] SUCCESS: Firecrawl")
        return result

    print("[SCRAPE] Firecrawl failed → trying Jina")

    result = call_jina(url)

    if result:
        print("[SCRAPE] SUCCESS: Jina")
        return result

    print("[SCRAPE] ALL SCRAPERS FAILED")

    return None


# -----------------------------------------------------------------------------
# OCR
# -----------------------------------------------------------------------------

def call_ocr(image_file):
    if not OCR_API_KEY:
        print("[OCR] API key missing")
        return None

    try:
        url = "https://api.ocr.space/parse/image"

        with open(image_file, "rb") as file:
            files = {
                "file": file
            }

            data = {
                "apikey": OCR_API_KEY,
                "language": "eng",
                "isOverlayRequired": False,
                "OCREngine": 2,
                "scale": True
            }

            response = requests.post(
                url,
                files=files,
                data=data,
                timeout=30
            )

        if not response.ok:
            print(
                f"[OCR] HTTP {response.status_code}: "
                f"{response.text[:1000]}"
            )
            return None

        result = response.json()

        if result.get("IsErroredOnProcessing"):
            print(
                "[OCR ERROR] "
                f"{result.get('ErrorMessage')}"
            )
            return None

        parsed_results = result.get("ParsedResults", [])

        if not parsed_results:
            return None

        text_parts = []

        for item in parsed_results:
            parsed_text = item.get("ParsedText", "")

            if parsed_text:
                text_parts.append(parsed_text)

        final_text = "\n".join(text_parts).strip()

        return final_text if final_text else None

    except Exception as e:
        print(f"[OCR ERROR] {type(e).__name__}: {e}")
        return None


# -----------------------------------------------------------------------------
# IMAGE GENERATION
# -----------------------------------------------------------------------------

def call_stability_image_gen(prompt):
    if not STABILITY_API_KEY:
        print("[STABILITY] API key missing")
        return None

    try:
        url = (
            "https://api.stability.ai/"
            "v2beta/stable-image/generate/core"
        )

        headers = {
            "Authorization": f"Bearer {STABILITY_API_KEY}",
            "Accept": "image/*"
        }

        data = {
            "prompt": prompt,
            "output_format": "png"
        }

        response = requests.post(
            url,
            headers=headers,
            files={
                "none": ""
            },
            data=data,
            timeout=60
        )

        if not response.ok:
            print(
                f"[STABILITY] HTTP {response.status_code}: "
                f"{response.text[:1000]}"
            )
            return None

        return response.content

    except Exception as e:
        print(
            f"[STABILITY ERROR] "
            f"{type(e).__name__}: {e}"
        )
        return None


# -----------------------------------------------------------------------------
# TEXT TO SPEECH - ELEVENLABS
# -----------------------------------------------------------------------------

def call_elevenlabs_tts(text, voice_id=None):
    if not ELEVENLABS_API_KEY:
        print("[ELEVENLABS] API key missing")
        return None

    try:
        if not voice_id:
            voice_id = "21m00Tcm4TlvDq8ikWAM"

        url = (
            f"https://api.elevenlabs.io/v1/"
            f"text-to-speech/{voice_id}"
        )

        headers = {
            "xi-api-key": ELEVENLABS_API_KEY,
            "Content-Type": "application/json",
            "Accept": "audio/mpeg"
        }

        payload = {
            "text": text,
            "model_id": "eleven_multilingual_v2"
        }

        response = requests.post(
            url,
            headers=headers,
            json=payload,
            timeout=30
        )

        if not response.ok:
            print(
                f"[ELEVENLABS] HTTP {response.status_code}: "
                f"{response.text[:1000]}"
            )
            return None

        return response.content

    except Exception as e:
        print(
            f"[ELEVENLABS ERROR] "
            f"{type(e).__name__}: {e}"
        )
        return None


# -----------------------------------------------------------------------------
# SPEECH TO TEXT - ASSEMBLYAI
# -----------------------------------------------------------------------------

def call_assemblyai_stt(audio_file):
    if not ASSEMBLYAI_API_KEY:
        print("[ASSEMBLYAI] API key missing")
        return None

    headers = {
        "authorization": ASSEMBLYAI_API_KEY
    }

    try:
        # Upload audio
        with open(audio_file, "rb") as file:
            upload_response = requests.post(
                "https://api.assemblyai.com/v2/upload",
                headers=headers,
                data=file,
                timeout=60
            )

        if not upload_response.ok:
            print(
                f"[ASSEMBLYAI UPLOAD] HTTP "
                f"{upload_response.status_code}: "
                f"{upload_response.text[:1000]}"
            )
            return None

        upload_data = upload_response.json()

        audio_url = upload_data.get("upload_url")

        if not audio_url:
            print("[ASSEMBLYAI] Upload URL missing")
            return None

        # Create transcript
        transcript_response = requests.post(
            "https://api.assemblyai.com/v2/transcript",
            headers={
                **headers,
                "content-type": "application/json"
            },
            json={
                "audio_url": audio_url
            },
            timeout=30
        )

        if not transcript_response.ok:
            print(
                f"[ASSEMBLYAI TRANSCRIPT] HTTP "
                f"{transcript_response.status_code}: "
                f"{transcript_response.text[:1000]}"
            )
            return None

        transcript_data = transcript_response.json()

        transcript_id = transcript_data.get("id")

        if not transcript_id:
            print("[ASSEMBLYAI] Transcript ID missing")
            return None

        # Poll with a limit
        poll_url = (
            f"https://api.assemblyai.com/v2/"
            f"transcript/{transcript_id}"
        )

        for _ in range(30):
            poll_response = requests.get(
                poll_url,
                headers=headers,
                timeout=20
            )

            if not poll_response.ok:
                print(
                    f"[ASSEMBLYAI POLL] HTTP "
                    f"{poll_response.status_code}: "
                    f"{poll_response.text[:1000]}"
                )
                return None

            data = poll_response.json()

            status = data.get("status")

            if status == "completed":
                text = data.get("text", "")
                return text.strip() if text else None

            if status == "error":
                print(
                    "[ASSEMBLYAI] "
                    f"{data.get('error', 'Unknown error')}"
                )
                return None

            time.sleep(2)

        print("[ASSEMBLYAI] Transcription timeout")
        return None

    except Exception as e:
        print(
            f"[ASSEMBLYAI ERROR] "
            f"{type(e).__name__}: {e}"
        )
        return None


# -----------------------------------------------------------------------------
# MAIN AI RESPONSE FUNCTION
# -----------------------------------------------------------------------------

def generate_ai_response(
    prompt,
    task_type=None,
    use_web=False,
    web_query=None
):
    """
    Main entry point used by Anis AI.

    Flow:
        Optional Web Search
              ↓
        Task Classification
              ↓
        AI Provider Fallback Chain
              ↓
        Final Response
    """

    try:
        if not prompt:
            return {
                "answer": None,
                "provider_used": None
            }

        prompt = str(prompt).strip()

        if not task_type:
            task_type = classify_task(prompt)

        # -------------------------------------------------------------
        # OPTIONAL WEB SEARCH
        # -------------------------------------------------------------

        web_context = None

        if use_web:
            query = web_query or prompt

            print(
                f"[AI] Web search enabled: {query}"
            )

            web_context = run_web_search(query)

        # -------------------------------------------------------------
        # BUILD FINAL PROMPT
        # -------------------------------------------------------------

        final_prompt = prompt

        if web_context:
            final_prompt = f"""
You are Anis AI.

Use the web information below when it is relevant.
Do not blindly copy it.
If the information is uncertain or conflicting, clearly say so.

WEB INFORMATION:
{web_context}

USER REQUEST:
{prompt}

Give a clear, accurate and useful answer.
""".strip()

        # -------------------------------------------------------------
        # RUN AI FALLBACK CHAIN
        # -------------------------------------------------------------

        result = run_text_ai_chain(
            final_prompt,
            task_type=task_type
        )

        if result and result.get("answer"):
            return result

        # -------------------------------------------------------------
        # COMPLETE FAILURE
        # -------------------------------------------------------------

        return {
            "answer": (
                "Sorry, Anis AI could not connect to any "
                "available AI provider right now. "
                "Please try again in a moment."
            ),
            "provider_used": None
        }

    except Exception as e:
        print(
            f"[GENERATE AI ERROR] "
            f"{type(e).__name__}: {e}"
        )

        return {
            "answer": (
                "An unexpected error occurred in Anis AI. "
                "Please try again."
            ),
            "provider_used": None
        }


# -----------------------------------------------------------------------------
# BACKWARD COMPATIBILITY
# -----------------------------------------------------------------------------

get_ai_response = generate_ai_response


# -----------------------------------------------------------------------------
# FINAL STATUS
# -----------------------------------------------------------------------------

print("============================================================")
print("ANIS AI BACKEND LOADED")
print("Gemini     :", "READY" if GEMINI_API_KEY else "MISSING")
print("Groq       :", "READY" if GROQ_API_KEY else "MISSING")
print("Cerebras   :", "READY" if CEREBRAS_API_KEY else "MISSING")
print("Mistral    :", "READY" if MISTRAL_API_KEY else "MISSING")
print("OpenRouter :", "READY" if OPENROUTER_API_KEY else "MISSING")
print("============================================================")