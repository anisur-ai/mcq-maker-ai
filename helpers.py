import io
import requests
import docx
import fitz  # PyMuPDF
import pypdf
import google.generativeai as genai
from groq import Groq
from openai import OpenAI

# =====================================================
# CONSTANTS
# =====================================================

MAX_CONTEXT_CHARS = 12000
MAX_WEB_CONTEXT = 10000

GROQ_FAST_MODEL = "llama-3.1-8b-instant"
GROQ_SMART_MODEL = "llama-3.3-70b-versatile"

GEMINI_MODEL = "gemini-2.5-flash"

MISTRAL_MODEL = "mistral-small-latest"

OPENROUTER_DEFAULT_MODEL = "mistralai/mistral-small-3.2-24b-instruct:free"
OPENROUTER_CODE_MODEL = "deepseek/deepseek-chat"


# =====================================================
# COMMON UTILITIES
# =====================================================

def truncate_text(text: str, max_chars: int = MAX_CONTEXT_CHARS):
    """
    Prevent huge prompts.
    """

    if not text:
        return ""

    if len(text) <= max_chars:
        return text

    return (
        text[:max_chars]
        + "\n\n[Content truncated because it exceeded the maximum context length.]"
    )


# =====================================================
# OCR.SPACE
# =====================================================

def ocr_space_file(file_obj, api_key, language="eng+ben"):

    if not api_key:
        return ""

    try:

        url = "https://api.ocr.space/parse/image"

        file_bytes = file_obj.read()

        file_type = getattr(
            file_obj,
            "type",
            "image/png"
        )

        files = {
            "filename": (
                getattr(file_obj, "name", "image.png"),
                file_bytes,
                file_type
            )
        }

        payload = {
            "apikey": api_key,
            "language": language,
            "OCREngine": 2,
            "scale": True,
            "isOverlayRequired": False
        }

        response = requests.post(
            url,
            data=payload,
            files=files,
            timeout=30
        )

        result = response.json()

        if result.get("IsErroredOnProcessing"):
            return ""

        parsed = result.get("ParsedResults")

        if parsed:
            return parsed[0].get("ParsedText", "")

    except Exception as e:
        print("OCR Error:", e)

    return ""


# =====================================================
# SMART FILE READER
# =====================================================

def smart_read_file(uploaded_file, ocr_api_key):

    if uploaded_file is None:
        return ""

    filename = uploaded_file.name.lower()

    extracted = ""

    try:

        # --------------------------
        # IMAGE
        # --------------------------

        if filename.endswith(
            (
                ".jpg",
                ".jpeg",
                ".png",
                ".webp"
            )
        ):

            return truncate_text(
                ocr_space_file(
                    uploaded_file,
                    ocr_api_key
                )
            )

        # --------------------------
        # DOCX
        # --------------------------

        elif filename.endswith(".docx"):

            document = docx.Document(uploaded_file)

            for para in document.paragraphs:
                extracted += para.text + "\n"

        # --------------------------
        # TXT
        # --------------------------

        elif filename.endswith(".txt"):

            extracted = uploaded_file.read().decode(
                "utf-8",
                errors="ignore"
            )

        # --------------------------
        # PDF
        # --------------------------

        elif filename.endswith(".pdf"):

            pdf_bytes = uploaded_file.read()

            pdf = fitz.open(
                stream=pdf_bytes,
                filetype="pdf"
            )

            for index in range(len(pdf)):

                page = pdf[index]

                text = page.get_text()

                if text.strip():

                    extracted += text + "\n"

                else:

                    pix = page.get_pixmap(
                        dpi=180
                    )

                    image_bytes = pix.tobytes("png")

                    class TempImage:

                        def __init__(self, data, name):

                            self.data = data

                            self.name = name

                        def read(self):

                            return self.data

                    img = TempImage(
                        image_bytes,
                        f"page_{index}.png"
                    )

                    ocr = ocr_space_file(
                        img,
                        ocr_api_key
                    )

                    if ocr:

                        extracted += (
                            f"\n[OCR Page {index+1}]\n"
                            + ocr
                            + "\n"
                        )

    except Exception as e:

        print("File Reader Error:", e)

    return truncate_text(extracted)
    # =====================================================
# AI INTENT DETECTOR
# =====================================================

def needs_web_search(prompt, groq_api_key):
    """
    Decide automatically whether live web search is required.
    Returns True or False.
    """

    if not groq_api_key:
        return False

    try:

        client = Groq(api_key=groq_api_key)

        response = client.chat.completions.create(
            model=GROQ_FAST_MODEL,
            temperature=0,
            max_completion_tokens=5,
            messages=[
                {
                    "role": "system",
                    "content":
                    (
                        "Reply ONLY YES or NO.\n"
                        "YES = if current information, latest news, "
                        "weather, price, sports, stock, internet facts "
                        "or live information is required.\n"
                        "NO = for programming, mathematics, writing, "
                        "translation, explanation, history or general knowledge."
                    )
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        answer = (
            response
            .choices[0]
            .message
            .content
            .strip()
            .upper()
        )

        return answer == "YES"

    except Exception as e:

        print("Intent Error:", e)

        return False


# =====================================================
# TAVILY SEARCH
# =====================================================

def smart_search(query, tavily_key, jina_key=None):

    if tavily_key:

        try:

            response = requests.post(
                "https://api.tavily.com/search",
                json={
                    "api_key": tavily_key,
                    "query": query,
                    "search_depth": "advanced",
                    "max_results": 3
                },
                timeout=12
            )

            if response.status_code == 200:

                data = response.json()

                results = data.get("results", [])

                if results:

                    text = ""

                    urls = []

                    for item in results:

                        url = item.get("url", "")

                        content = item.get("content", "")

                        urls.append(url)

                        text += (
                            f"Source: {url}\n"
                            f"{content}\n\n"
                        )

                    return truncate_text(text), urls

        except Exception as e:

            print("Tavily Error:", e)


    # -----------------------------
    # Jina Search Fallback
    # -----------------------------

    try:

        headers = {
            "Accept": "application/json"
        }

        if jina_key:

            headers["Authorization"] = f"Bearer {jina_key}"

        response = requests.get(
            f"https://s.jina.ai/{query}",
            headers=headers,
            timeout=12
        )

        if response.status_code == 200:

            data = response.json()

            items = data.get("data", [])

            if items:

                text = ""

                urls = []

                for item in items[:3]:

                    url = item.get("url", "")

                    content = item.get("content", "")

                    urls.append(url)

                    text += (
                        f"Source: {url}\n"
                        f"{content}\n\n"
                    )

                return truncate_text(text), urls

    except Exception as e:

        print("Jina Search Error:", e)

    return "", []


# =====================================================
# SMART URL SCRAPER
# =====================================================

def smart_scrape(url, firecrawl_key, jina_key):

    if firecrawl_key:

        try:

            response = requests.post(
                "https://api.firecrawl.dev/v1/scrape",
                headers={
                    "Authorization": f"Bearer {firecrawl_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "url": url,
                    "formats": ["markdown"]
                },
                timeout=15
            )

            if response.status_code == 200:

                data = response.json()

                if data.get("success"):

                    markdown = (
                        data
                        .get("data", {})
                        .get("markdown", "")
                    )

                    return (
                        truncate_text(markdown),
                        [url]
                    )

        except Exception as e:

            print("Firecrawl Error:", e)


    # ------------------------
    # Jina Reader Fallback
    # ------------------------

    try:

        headers = {
            "Accept": "application/json"
        }

        if jina_key:

            headers["Authorization"] = (
                f"Bearer {jina_key}"
            )

        response = requests.get(
            f"https://r.jina.ai/{url}",
            headers=headers,
            timeout=15
        )

        if response.status_code == 200:

            data = response.json()

            content = (
                data
                .get("data", {})
                .get("content", "")
            )

            return (
                truncate_text(content),
                [url]
            )

    except Exception as e:

        print("Jina Reader Error:", e)

    return "", []
    # =====================================================
# DYNAMIC MODEL ROUTER
# =====================================================

def select_model_by_task(user_prompt, context_text=""):
    """
    Decide which provider/model should be used.
    Returns:
    {
        "provider": "...",
        "model": "..."
    }
    """

    query = user_prompt.lower()

    total_length = len(user_prompt) + len(context_text)

    # --------------------------
    # Coding
    # --------------------------

    coding_words = [
        "python",
        "java",
        "javascript",
        "html",
        "css",
        "php",
        "sql",
        "bug",
        "debug",
        "code",
        "program",
        "api",
        "streamlit"
    ]

    if any(word in query for word in coding_words):

        return {
            "provider": "openrouter",
            "model": OPENROUTER_CODE_MODEL
        }

    # --------------------------
    # Very Large Context
    # --------------------------

    if total_length > 6000:

        return {
            "provider": "gemini",
            "model": GEMINI_MODEL
        }

    # --------------------------
    # Long Question
    # --------------------------

    if (
        len(user_prompt.split()) > 50
        or total_length > 1200
    ):

        return {
            "provider": "groq",
            "model": GROQ_SMART_MODEL
        }

    # --------------------------
    # Default
    # --------------------------

    return {
        "provider": "groq",
        "model": GROQ_FAST_MODEL
    }


# =====================================================
# CHAT MEMORY
# =====================================================

def manage_conversation_memory(
    messages,
    groq_api_key,
    previous_summary=""
):

    """
    Compress old conversations
    to reduce token usage.
    """

    if len(messages) < 18:

        return previous_summary,
        # =====================================================
# BUILD FINAL AI MESSAGES
# =====================================================

def build_ai_messages(
    system_prompt,
    managed_messages,
    user_prompt,
    file_context="",
    external_context=""
):
    """
    Build the final messages list that will
    be sent to the AI model.
    """

    ai_messages = [
        {
            "role": "system",
            "content": system_prompt
        }
    ]

    for message in managed_messages:

        if (
            message["role"] == "system"
            and message["content"] == system_prompt
        ):
            continue

        ai_messages.append(message)

    final_input = user_prompt

    if file_context.strip():
        final_input += (
            "\n\n========== FILE ==========\n"
            + file_context
        )

    if external_context.strip():
        final_input += (
            "\n\n========== WEB ==========\n"
            + external_context
        )

    ai_messages.append(
        {
            "role": "user",
            "content": final_input
        }
    )

    return ai_messages


# =====================================================
# FORMAT SOURCES
# =====================================================

def format_sources(source_list):

    if not source_list:
        return ""

    text = "\n\n**Sources**\n"

    used = set()

    for url in source_list:

        if not url:
            continue

        if url in used:
            continue

        used.add(url)

        text += f"- {url}\n"

    return text


# =====================================================
# SAFE TEXT LIMITER
# =====================================================

def safe_context(
    text,
    limit=12000
):

    if not text:
        return ""

    if len(text) <= limit:
        return# --- 4. URL Scraper (Firecrawl -> Jina Reader) ---
def smart_scrape(url_to_scrape, firecrawl_key, jina_key):
    # Firecrawl
    if firecrawl_key:
        try:
            url = "https://api.firecrawl.dev/v1/scrape"
            headers = {
                "Authorization": f"Bearer {firecrawl_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "url": url_to_scrape,
                "formats": ["markdown"]
            }

            res = requests.post(
                url,
                json=payload,
                headers=headers,
                timeout=12
            )

            if (
                res.status_code == 200
                and res.json().get("success")
            ):
                content = (
                    res.json()
                    .get("data", {})
                    .get("markdown", "")
                )
                return truncate_text(content, 10000), [url_to_scrape]

        except Exception:
            pass

    # Jina Reader Fallback
    try:
        jina_url = f"https://r.jina.ai/{url_to_scrape}"

        headers = {
            "Accept": "application/json"
        }

        if jina_key:
            headers["Authorization"] = f"Bearer {jina_key}"

        res = requests.get(
            jina_url,
            headers=headers,
            timeout=12
        )

        if res.status_code == 200:
            content = (
                res.json()
                .get("data", {})
                .get("content", "")
            )

            return truncate_text(content, 10000), [url_to_scrape]

    except Exception:
        pass

    return "Could not extract content from URL.", []# ---------- Part 5 : Provider Aware AI Fallback ----------

def provider_aware_ai_fallback(keys_dict, router_info, messages, max_tokens=4096):
    default_temp = 0.5

    preferred_provider = router_info["provider"]
    preferred_model = router_info["model"]

    providers_order = [
        preferred_provider,
        "groq",
        "gemini",
        "mistral",
        "openrouter",
    ]

    # Remove duplicates
    providers_order = list(dict.fromkeys(providers_order))

    for provider in providers_order:

        # ---------------- GROQ ----------------
        if provider == "groq" and keys_dict.get("groq"):
            try:
                client = Groq(
                    api_key=keys_dict["groq"],
                    timeout=8,
                    max_retries=0,
                )

                model_name = (
                    preferred_model
                    if preferred_provider == "groq"
                    else "llama-3.3-70b-versatile"
                )

                completion = client.chat.completions.create(
                    model=model_name,
                    messages=messages,
                    temperature=default_temp,
                    max_completion_tokens=max_tokens,
                    stream=True,
                )

                for chunk in completion:
                    if (
                        chunk.choices
                        and chunk.choices[0].delta
                        and chunk.choices[0].delta.content
                    ):
                        yield chunk.choices[0].delta.content
                return

            except Exception:
                pass

        # ---------------- GEMINI ----------------
        elif provider == "gemini" and keys_dict.get("gemini"):
            try:
                genai.configure(api_key=keys_dict["gemini"])

                model = genai.GenerativeModel("gemini-2.5-flash")

                system_prompt = ""
                history = []

                for msg in messages:
                    if msg["role"] == "system":
                        system_prompt = msg["content"]
                    elif msg["role"] == "user":
                        history.append(
                            {
                                "role": "user",
                                "parts": [msg["content"]],
                            }
                        )
                    elif msg["role"] == "assistant":
                        history.append(
                            {
                                "role": "model",
                                "parts": [msg["content"]],
                            }
                        )

                chat = model.start_chat(history=history[:-1])

                response = chat.send_message(
                    system_prompt + "\n\n" + messages[-1]["content"],
                    stream=True,
                )

                for chunk in response:
                    if chunk.text:
                        yield chunk.text
                return

            except Exception:
                pass

        # ---------------- MISTRAL ----------------
        elif provider == "mistral" and keys_dict.get("mistral"):
            try:
                client = OpenAI(
                    api_key=keys_dict["mistral"],
                    base_url="https://api.mistral.ai/v1",
                    timeout=8,
                    max_retries=0,
                )

                completion = client.chat.completions.create(
                    model="mistral-small-latest",
                    messages=messages,
                    temperature=default_temp,
                    max_tokens=max_tokens,
                    stream=True,
                )

                for chunk in completion:
                    if (
                        chunk.choices
                        and chunk.choices[0].delta
                        and chunk.choices[0].delta.content
                    ):
                        yield chunk.choices[0].delta.content
                return

            except Exception:
                pass

        # ---------------- OPENROUTER ----------------
        elif provider == "openrouter" and keys_dict.get("openrouter"):
            try:
                client = OpenAI(
                    api_key=keys_dict["openrouter"],
                    base_url="https://openrouter.ai/api/v1",
                    timeout=8,
                    max_retries=0,
                )

                model_name = (
                    preferred_model
                    if preferred_provider == "openrouter"
                    else "mistralai/mistral-small-3.2-24b-instruct:free"
                )

                completion = client.chat.completions.create(
                    model=model_name,
                    messages=messages,
                    temperature=default_temp,
                    max_tokens=max_tokens,
                    stream=True,
                )

                for chunk in completion:
                    if (
                        chunk.choices
                        and chunk.choices[0].delta
                        and chunkand chunk.choices[0].delta.content
                    ):
                        yield chunk.choices[0].delta.content
                return

            except Exception:
                pass

    yield "ERROR_ALL_FAILED"

        
