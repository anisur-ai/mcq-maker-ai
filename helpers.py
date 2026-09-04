"""
Anis AI - Backend Helper Functions & Resilient Provider Fallback Engine
Provides search, scraping, file parsing/OCR, task routing, and unified streaming fallback.
Compatible with Python 3.10+ through Python 3.14+ and modern Streamlit.
"""

import io
import json
import logging
import os
import re
import time
import urllib.parse
from typing import Any, Dict, Generator, List, Optional, Tuple

import requests
from bs4 import BeautifulSoup
import pypdf
import docx

# =====================================================
# INTERNAL LOGGING (Zero Secrets/Tokens Logged)
# =====================================================
logger = logging.getLogger("AnisAI")
logger.setLevel(logging.INFO)
if not logger.handlers:
    ch = logging.StreamHandler()
    ch.setFormatter(logging.Formatter("[%(asctime)s] [%(levelname)s] [AnisAI]: %(message)s", datefmt="%H:%M:%S"))
    logger.addHandler(ch)

# Reusable HTTP session with connection pooling for lowest possible latency
http_session = requests.Session()

# =====================================================
# CENTRALIZED PROVIDER & MODEL CONFIGURATION
# =====================================================
PROVIDER_CONFIG: Dict[str, Dict[str, str]] = {
    "groq": {
        "name": "Groq",
        "base_url": "https://api.groq.com/openai/v1/chat/completions",
        "default_model": "llama-3.3-70b-versatile",
        "fast_model": "llama-3.1-8b-instant",
        "coding_model": "llama-3.3-70b-versatile",
        "reasoning_model": "llama-3.3-70b-versatile",
    },
    "gemini": {
        "name": "Gemini",
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
        "default_model": "gemini-1.5-flash",
        "fast_model": "gemini-1.5-flash",
        "coding_model": "gemini-1.5-flash",
        "reasoning_model": "gemini-1.5-pro",
        "long_context_model": "gemini-1.5-flash",
    },
    "mistral": {
        "name": "Mistral",
        "base_url": "https://api.mistral.ai/v1/chat/completions",
        "default_model": "mistral-small-latest",
        "fast_model": "mistral-small-latest",
        "coding_model": "codestral-latest",
        "reasoning_model": "mistral-large-latest",
    },
    "openrouter": {
        "name": "OpenRouter",
        "base_url": "https://openrouter.ai/api/v1/chat/completions",
        "default_model": "meta-llama/llama-3.3-70b-instruct",
        "fast_model": "google/gemini-2.0-flash-lite-001",
        "coding_model": "meta-llama/llama-3.3-70b-instruct",
        "reasoning_model": "deepseek/deepseek-chat",
    },
}

# =====================================================
# 1. FILE & OCR PROCESSING (smart_read_file)
# =====================================================
def smart_read_file(uploaded_file, ocr_api_key: Optional[str] = None) -> str:
    """
    Extracts text from PDF, DOCX, TXT, and images (via OCR.space).
    Includes length bounds to prevent prompt bloat and memory exhaustion.
    """
    if uploaded_file is None:
        return ""

    file_name = uploaded_file.name
    file_bytes = uploaded_file.getvalue()
    file_ext = file_name.split(".")[-1].lower()
    extracted_text = ""

    try:
        if file_ext == "txt":
            try:
                extracted_text = file_bytes.decode("utf-8")
            except UnicodeDecodeError:
                extracted_text = file_bytes.decode("latin-1", errors="replace")

        elif file_ext == "pdf":
            reader = pypdf.PdfReader(io.BytesIO(file_bytes))
            pages_text = []
            max_pages = min(len(reader.pages), 30)
            for idx in range(max_pages):
                page_text = reader.pages[idx].extract_text() or ""
                if page_text.strip():
                    pages_text.append(f"--- Page {idx + 1} ---\n{page_text.strip()}")
            extracted_text = "\n\n".join(pages_text)

        elif file_ext == "docx":
            doc = docx.Document(io.BytesIO(file_bytes))
            paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
            extracted_text = "\n".join(paragraphs)

        elif file_ext in ["png", "jpg", "jpeg", "webp"]:
            api_key = ocr_api_key.strip() if ocr_api_key else ""
            if not api_key:
                return (
                    f"[Image Attached: {file_name}]\n"
                    f"(Note: OCR_API_KEY is not configured in secrets. "
                    f"Please provide an OCR.space key to parse text from images directly.)"
                )

            ocr_url = "https://api.ocr.space/parse/image"
            files = {file_name: file_bytes}
            data = {
                "apikey": api_key,
                "language": "eng",
                "isOverlayRequired": False,
                "detectOrientation": True,
                "scale": True,
            }
            res = http_session.post(ocr_url, files=files, data=data, timeout=20)
            if res.status_code == 200:
                result_json = res.json()
                if not result_json.get("IsErroredOnProcessing", False):
                    parsed_results = result_json.get("ParsedResults", [])
                    extracted_text = "\n".join(
                        [r.get("ParsedText", "").strip() for r in parsed_results if r.get("ParsedText")]
                    )
                    if not extracted_text:
                        extracted_text = "(OCR completed, but no legible text was detected in the image.)"
                else:
                    error_msg = result_json.get("ErrorMessage", ["OCR processing error"])[0]
                    extracted_text = f"(OCR Error: {error_msg})"
            else:
                extracted_text = f"(OCR Service unreachable, HTTP status: {res.status_code})"

    except Exception as e:
        logger.error(f"Error reading file {file_name}: {e}")
        extracted_text = f"(Error processing file content: {str(e)})"

    # Limit text size to ~24,000 characters (~6k tokens)
    if len(extracted_text) > 24000:
        extracted_text = extracted_text[:24000] + "\n\n... [Content truncated for prompt size limits]"

    return (
        f"=== ATTACHED FILE CONTEXT ===\n"
        f"Filename: {file_name}\n"
        f"Type: {file_ext.upper()}\n"
        f"Content:\n{extracted_text}\n"
        f"=== END OF FILE CONTEXT ===\n"
    )

# =====================================================
# 2. WEB SEARCH DETECTION (needs_web_search)
# =====================================================
SEARCH_KEYWORDS = {
    "today", "yesterday", "tomorrow", "tonight", "this week", "this month", "this year",
    "latest", "recent", "recently", "current", "currently", "now", "breaking", "news",
    "weather", "stock price", "stock", "score", "match", "election", "who is", "who won",
    "2025", "2026", "2027", "update", "updates", "release date", "price of"
}

def needs_web_search(prompt_text: str, groq_api_key: Optional[str] = None) -> bool:
    """
    Evaluates whether live search is needed. Fast regex heuristics guarantee
    0ms latency for general conversation.
    """
    clean_prompt = prompt_text.lower().strip()

    # Fast heuristic search check
    if any(kw in clean_prompt for kw in SEARCH_KEYWORDS):
        return True

    # Check for direct search intents
    if re.search(r"^(search|google|look up|find out|browse)\b", clean_prompt):
        return True

    return False

# =====================================================
# 3. WEB SEARCH ENGINE (smart_search)
# =====================================================
def smart_search(
    query: str,
    serper_key: Optional[str] = None,
    tavily_key: Optional[str] = None,
    jina_key: Optional[str] = None,
) -> Tuple[str, List[Dict[str, str]]]:
    """
    Cascading web search: Serper -> Tavily -> Jina Search.
    Returns aggregated context text and structured source references.
    """
    sources: List[Dict[str, str]] = []
    context_lines: List[str] = []

    # 1. Try Serper (Google Search API)
    if serper_key and serper_key.strip():
        try:
            res = http_session.post(
                "https://google.serper.dev/search",
                headers={"X-API-KEY": serper_key.strip(), "Content-Type": "application/json"},
                json={"q": query, "num": 5},
                timeout=7,
            )
            if res.status_code == 200:
                data = res.json()
                for item in data.get("organic", [])[:5]:
                    title = item.get("title", "")
                    link = item.get("link", "")
                    snippet = item.get("snippet", "")
                    if link:
                        sources.append({"title": title, "url": link})
                        context_lines.append(f"• {title}: {snippet} ({link})")
                if context_lines:
                    return "\n".join(context_lines), sources
        except Exception as e:
            logger.warning(f"Serper search failed: {e}. Falling back to Tavily.")

    # 2. Try Tavily Search API
    if tavily_key and tavily_key.strip():
        try:
            res = http_session.post(
                "https://api.tavily.com/search",
                headers={"Content-Type": "application/json"},
                json={"api_key": tavily_key.strip(), "query": query, "search_depth": "basic", "max_results": 5},
                timeout=7,
            )
            if res.status_code == 200:
                data = res.json()
                for item in data.get("results", [])[:5]:
                    title = item.get("title", "")
                    url = item.get("url", "")
                    content = item.get("content", "")
                    if url:
                        sources.append({"title": title, "url": url})
                        context_lines.append(f"• {title}: {content} ({url})")
                if context_lines:
                    return "\n".join(context_lines), sources
        except Exception as e:
            logger.warning(f"Tavily search failed: {e}. Falling back to Jina.")

    # 3. Try Jina Search API
    try:
        headers = {"Accept": "application/json"}
        if jina_key and jina_key.strip():
            headers["Authorization"] = f"Bearer {jina_key.strip()}"
        encoded_query = urllib.parse.quote(query)
        res = http_session.get(f"https://s.jina.ai/{encoded_query}", headers=headers, timeout=7)
        if res.status_code == 200:
            data = res.json()
            for item in data.get("data", [])[:5]:
                title = item.get("title", "")
                url = item.get("url", "")
                description = item.get("description", item.get("content", ""))[:300]
                if url:
                    sources.append({"title": title, "url": url})
                    context_lines.append(f"• {title}: {description} ({url})")
            if context_lines:
                return "\n".join(context_lines), sources
    except Exception as e:
        logger.warning(f"Jina search failed: {e}.")

    return "No search results could be retrieved.", sources

# =====================================================
# 4. URL SCRAPING ENGINE (smart_scrape)
# =====================================================
def smart_scrape(
    url: str,
    firecrawl_key: Optional[str] = None,
    jina_key: Optional[str] = None,
) -> Tuple[str, List[Dict[str, str]]]:
    """
    Cascading Web Scraper: Firecrawl -> Jina Reader -> Native HTML parser.
    """
    sources = [{"title": url, "url": url}]

    # 1. Try Firecrawl Scrape API
    if firecrawl_key and firecrawl_key.strip():
        try:
            res = http_session.post(
                "https://api.firecrawl.dev/v1/scrape",
                headers={"Authorization": f"Bearer {firecrawl_key.strip()}", "Content-Type": "application/json"},
                json={"url": url, "formats": ["markdown"]},
                timeout=12,
            )
            if res.status_code == 200:
                data = res.json()
                markdown = data.get("data", {}).get("markdown", "")
                if markdown:
                    return f"=== Scraped Content ({url}) ===\n{markdown[:6000]}\n", sources
        except Exception as e:
            logger.warning(f"Firecrawl scrape failed: {e}. Trying Jina Reader.")

    # 2. Try Jina Reader
    try:
        headers = {}
        if jina_key and jina_key.strip():
            headers["Authorization"] = f"Bearer {jina_key.strip()}"
        res = http_session.get(f"https://r.jina.ai/{url}", headers=headers, timeout=10)
        if res.status_code == 200 and res.text.strip():
            return f"=== Scraped Content ({url}) ===\n{res.text[:6000]}\n", sources
    except Exception as e:
        logger.warning(f"Jina Reader failed: {e}. Trying native fallback.")

    # 3. Native requests + BeautifulSoup fallback
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        res = http_session.get(url, headers=headers, timeout=8)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, "html.parser")
            for element in soup(["script", "style", "nav", "footer", "header", "noscript"]):
                element.decompose()
            clean_text = " ".join(soup.stripped_strings)[:5000]
            return f"=== Scraped Content ({url}) ===\n{clean_text}\n", sources
    except Exception as e:
        logger.error(f"Native scrape failed: {e}")

    return f"Could not extract content from {url}.", sources

# =====================================================
# 5. MODEL ROUTING BY TASK (select_model_by_task)
# =====================================================
def select_model_by_task(prompt_text: str, context_text: str = "") -> Dict[str, Any]:
    """
    Selects the optimal model and preferred provider by task type.
    Fallback order remains flexible and covers all available providers.
    """
    clean_p = prompt_text.lower()
    coding_triggers = {"code", "python", "javascript", "function", "bug", "sql", "html", "css", "class", "script", "api", "regex"}
    reasoning_triggers = {"explain", "prove", "why", "logic", "calculate", "solve", "math", "analyze", "quiz", "step by step", "compare"}

    if any(w in clean_p for w in coding_triggers):
        task = "coding"
        preferred = "groq"
    elif len(context_text) > 4000:
        task = "document_qa"
        preferred = "gemini"
    elif any(w in clean_p for w in reasoning_triggers):
        task = "reasoning"
        preferred = "gemini"
    elif context_text:
        task = "web_research"
        preferred = "groq"
    else:
        task = "general_chat"
        preferred = "groq"

    model_mapping = {}
    for prov, conf in PROVIDER_CONFIG.items():
        if task == "coding":
            model_mapping[prov] = conf.get("coding_model", conf["default_model"])
        elif task == "reasoning":
            model_mapping[prov] = conf.get("reasoning_model", conf["default_model"])
        elif task == "document_qa":
            model_mapping[prov] = conf.get("long_context_model", conf["default_model"])
        else:
            model_mapping[prov] = conf["default_model"]

    return {
        "task": task,
        "preferred_provider": preferred,
        "provider_models": model_mapping,
    }

# =====================================================
# 6. MESSAGE BUILDER & SOURCE FORMATTER
# =====================================================
def build_ai_messages(
    system_prompt: str,
    managed_messages: List[Dict[str, str]],
    user_prompt: str,
    file_context: str = "",
    external_context: str = "",
) -> List[Dict[str, str]]:
    """
    Assembles OpenAI-compatible messages payload including chat history,
    document context, and search context.
    """
    formatted: List[Dict[str, str]] = [{"role": "system", "content": system_prompt}]

    # Include recent chat history (last 10 turns to conserve token quota)
    recent_history = managed_messages[-10:] if len(managed_messages) > 10 else managed_messages
    for m in recent_history:
        if m.get("role") in ("user", "assistant") and m.get("content"):
            formatted.append({"role": m["role"], "content": m["content"]})

    # Build augmented current user prompt
    augmented_parts = []
    if file_context.strip():
        augmented_parts.append(file_context.strip())
    if external_context.strip():
        augmented_parts.append(f"=== SEARCH CONTEXT ===\n{external_context.strip()}\n=== END CONTEXT ===")
    augmented_parts.append(f"User Request:\n{user_prompt}")

    formatted.append({"role": "user", "content": "\n\n".join(augmented_parts)})
    return formatted

def format_sources(sources_list: List[Dict[str, str]]) -> str:
    """Formats unique sources into a clean markdown reference list."""
    if not sources_list:
        return ""
    seen_urls = set()
    unique_sources = []
    for s in sources_list:
        url = s.get("url", "").strip()
        if url and url not in seen_urls:
            seen_urls.add(url)
            title = s.get("title") or url
            unique_sources.append(f"- [{title}]({url})")

    if not unique_sources:
        return ""
    return "\n\n---\n**Sources & References:**\n" + "\n".join(unique_sources)

# =====================================================
# 7. ROBUST PROVIDER FALLBACK WITH HTTP SSE STREAMING
# =====================================================
def _stream_openai_compatible(
    provider_key: str,
    api_key: str,
    model: str,
    messages: List[Dict[str, str]],
) -> Generator[str, None, None]:
    """
    Unified, low-latency Server-Sent Events (SSE) streaming engine.
    Works natively across Groq, Gemini, Mistral, and OpenRouter without heavy SDKs.
    """
    conf = PROVIDER_CONFIG[provider_key]
    url = conf["base_url"]

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    if provider_key == "openrouter":
        headers["HTTP-Referer"] = "https://anis-ai.streamlit.app"
        headers["X-Title"] = "Anis AI"

    payload = {
        "model": model,
        "messages": messages,
        "stream": True,
        "temperature": 0.7,
    }

    # 5s connection timeout, 35s stream read timeout
    response = http_session.post(
        url,
        headers=headers,
        json=payload,
        stream=True,
        timeout=(5.0, 35.0),
    )

    if response.status_code != 200:
        error_sample = response.text[:250]
        response.close()
        raise requests.HTTPError(
            f"{provider_key} returned status {response.status_code}: {error_sample}",
            response=response,
        )

    for line in response.iter_lines(decode_unicode=True):
        if not line:
            continue
        if line.startswith("data: "):
            data_str = line[6:].strip()
            if data_str == "[DONE]":
                break
            try:
                data_json = json.loads(data_str)
                choices = data_json.get("choices", [])
                if choices:
                    delta = choices[0].get("delta", {})
                    content = delta.get("content", "")
                    if content:
                        yield content
            except json.JSONDecodeError:
                continue

    response.close()


def provider_aware_ai_fallback(
    keys_dict: Dict[str, str],
    router_info: Dict[str, Any],
    messages: List[Dict[str, str]],
) -> Generator[str, None, None]:
    """
    Primary provider -> (Transient error? brief retry) -> Next configured provider -> ...
    Yields 'ERROR_ALL_FAILED' ONLY when every usable provider has failed.
    """
    preferred = router_info.get("preferred_provider", "groq")
    all_providers = ["groq", "gemini", "mistral", "openrouter"]

    # Reorder according to preferred provider
    candidate_order = [preferred] + [p for p in all_providers if p != preferred]

    # Filter strictly to providers that have an API key configured
active_providers = [p for p in candidate_order if keys_dict.get(p, "").strip()]

    if not active_providers:
        logger.error("[AI] No valid AI provider API keys configured.")
        yield "ERROR_ALL_FAILED"
        return

    total_candidates = len(active_providers)
    success = False

    for attempt_idx, provider in enumerate(active_providers):
        api_key = keys_dict[provider].strip()
        model = router_info.get("provider_models", {}).get(provider, PROVIDER_CONFIG[provider]["default_model"])

        # Controlled retry: max 1 retry for transient errors (429, 500, 502, 503, 504)
        max_retries = 1
        for retry in range(max_retries + 1):
            t_start = time.time()
            try:
                logger.info(f"[AI] Attempting {provider.upper()} ({model}) [Attempt {retry + 1}]...")
                stream = _stream_openai_compatible(
                    provider_key=provider,
                    api_key=api_key,
                    model=model,
                    messages=messages,
                )

                yielded_any = False
                for token in stream:
                    yielded_any = True
                    yield token

                if yielded_any:
                    elapsed = round(time.time() - t_start, 2)
                    logger.info(f"[AI] {provider.upper()} completed successfully in {elapsed}s.")
                    success = True
                    return

            except requests.HTTPError as http_err:
                status = getattr(http_err.response, "status_code", 0)
                logger.warning(f"[AI] {provider.upper()} returned HTTP {status}.")

                # Immediate fallback for client, authentication, or model-not-found errors
                if status in (400, 401, 403, 404):
                    logger.info(f"[AI] Non-recoverable error ({status}). Skipping {provider.upper()}.")
                    break

                # Transient errors (429 rate limit or 5xx server issues)
                if status in (429, 500, 502, 503, 504) and retry < max_retries:
                    logger.info(f"[AI] Transient error ({status}). Backing off 1.2s before retry...")
                    time.sleep(1.2)
                    continue
                break

            except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as net_err:
                logger.warning(f"[AI] {provider.upper()} network error: {type(net_err).__name__}")
                if retry < max_retries:
                    time.sleep(1.0)
                    continue
                break

            except Exception as ex:
                logger.error(f"[AI] Unexpected exception with {provider.upper()}: {ex}")
                break

        # Log fallback step to next provider if available
        if attempt_idx < total_candidates - 1:
            next_provider = active_providers[attempt_idx + 1]
            logger.info(f"[AI] Falling back from {provider.upper()} to {next_provider.upper()}...")

    # Only reached if EVERY usable configured provider has failed
    if not success:
        logger.error("[AI] All configured providers failed.")
        yield "ERROR_ALL_FAILED"
    
