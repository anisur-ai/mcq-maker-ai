import os
import re
import streamlit as st

# Safe import for dotenv: Environment variable loader
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Import all necessary functions directly from helpers.py
from helpers import (
    smart_read_file,
    needs_web_search,
    smart_search,
    smart_scrape,
    select_model_by_task,
    build_ai_messages,
    format_sources,
    provider_aware_ai_fallback,
)

# =====================================================
# PAGE CONFIGURATION
# =====================================================
st.set_page_config(
    page_title="Gemini AI",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# =====================================================
# GEMINI UI - CUSTOM CSS
# =====================================================
GEMINI_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
    color: #e3e3e3;
}

/* Gemini Dark Background */
.stApp {
    background-color: #131314;
    color: #e3e3e3;
}

/* Sidebar styling */
[data-testid="stSidebar"] {
    background-color: #1e1f20 !important;
    border-right: 1px solid #2d2f31;
}

[data-testid="stSidebar"] hr {
    border-color: #2d2f31;
}

header[data-testid="stHeader"] {
    background: transparent;
}

/* Gemini Gradient Heading */
.gemini-title {
    font-size: 3.2rem;
    font-weight: 700;
    letter-spacing: -0.02em;
    background: linear-gradient(74deg, #4285f4 0%, #9b72cf 35%, #d96570 70%, #d96570 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 0.2rem;
    line-height: 1.2;
}

.gemini-subtitle {
    font-size: 1.4rem;
    font-weight: 500;
    color: #c4c7c5;
    margin-bottom: 2rem;
}

/* Gemini Badge Pill */
.gemini-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: #1e1f20;
    border: 1px solid #333538;
    padding: 4px 12px;
    border-radius: 20px;
    font-size: 0.8rem;
    color: #c4c7c5;
    font-weight: 500;
    margin-bottom: 12px;
}

.gemini-sparkle {
    background: linear-gradient(74deg, #4285f4, #9b72cf, #d96570);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-size: 0.95rem;
}

/* Chat Messages */
[data-testid="stChatMessage"] {
    background-color: transparent;
    border: none;
    padding: 1.2rem 0;
}

/* User Message Pill */
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) {
    background-color: #282a2c;
    border-radius: 24px;
    padding: 14px 20px;
    margin: 8px 0 16px auto;
    max-width: 80%;
    width: fit-content;
}

/* Assistant Message */
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarAssistant"]) {
    background-color: transparent;
    padding-left: 0;
}

/* Rounded Input Bar & Action Buttons */
[data-testid="stChatInput"] {
    background-color: #1e1f20;
    border: 1px solid #333538;
    border-radius: 28px;
    padding: 4px 8px;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.25);
}

[data-testid="stChatInput"]:focus-within {
    border-color: #4285f4;
    box-shadow: 0 4px 24px rgba(66, 133, 244, 0.2);
}

[data-testid="stChatInput"] textarea {
    color: #e3e3e3;
    font-size: 0.98rem;
}

/* Attachment button & Send button inside input */
[data-testid="stChatInput"] button {
    border-radius: 50% !important;
    transition: background-color 0.2s ease;
}

/* Button UI */
.stButton > button {
    background-color: #1e1f20;
    color: #e3e3e3;
    border: 1px solid #333538;
    border-radius: 20px;
    padding: 6px 18px;
    font-weight: 500;
    transition: all 0.2s;
}

.stButton > button:hover {
    background-color: #2d2f31;
    border-color: #55575a;
    color: #ffffff;
}
</style>
"""
st.markdown(GEMINI_CSS, unsafe_allow_html=True)

# =====================================================
# CONSTANTS & UTILITIES
# =====================================================
DEFAULT_SYSTEM_PROMPT = (
    "You are Gemini, a helpful, highly knowledgeable, and polite AI assistant built by Google. "
    "Format all answers with clean Markdown, bullet points, and code blocks where appropriate. "
    "Use any provided document context or web search results precisely."
)

URL_REGEX = r"https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+[^\s]*"

def get_key(key_name: str) -> str:
    """
    Fetch API keys securely from Session State, Streamlit Secrets, or OS Environment.
    """
    if st.session_state.get(key_name):
        return st.session_state[key_name].strip()
    try:
        if key_name in st.secrets:
            return str(st.secrets[key_name]).strip()
    except Exception:
        pass
    return os.getenv(key_name, "").strip()


# =====================================================
# SIDEBAR DRAWER (SETTINGS & KEYS)
# =====================================================
with st.sidebar:
    st.markdown("### ✨ **Gemini Settings**")
    
    with st.expander("🔑 AI Provider Keys", expanded=False):
        st.text_input("Gemini API Key", value=get_key("GEMINI_API_KEY"), type="password", key="GEMINI_API_KEY")
        st.text_input("Groq API Key", value=get_key("GROQ_API_KEY"), type="password", key="GROQ_API_KEY")
        st.text_input("Mistral API Key", value=get_key("MISTRAL_API_KEY"), type="password", key="MISTRAL_API_KEY")
        st.text_input("OpenRouter API Key", value=get_key("OPENROUTER_API_KEY"), type="password", key="OPENROUTER_API_KEY")

    with st.expander("🌐 Web Search & OCR Tools", expanded=False):
        st.text_input("Serper API Key (Google Search)", value=get_key("SERPER_API_KEY"), type="password", key="SERPER_API_KEY")
        st.text_input("Tavily API Key", value=get_key("TAVILY_API_KEY"), type="password", key="TAVILY_API_KEY")
        st.text_input("Jina API Key", value=get_key("JINA_API_KEY"), type="password", key="JINA_API_KEY")
        st.text_input("Firecrawl API Key", value=get_key("FIRECRAWL_API_KEY"), type="password", key="FIRECRAWL_API_KEY")
        st.text_input("OCR.space API Key", value=get_key("OCR_API_KEY"), type="password", key="OCR_API_KEY")

    st.markdown("---")
    st.markdown("### ⚙️ **Chat Options**")
    force_web_search = st.checkbox("Always Search Google Live", value=False)

    if st.button("🗑️ Reset Chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()


# =====================================================
# SESSION STATE & ACTIVE KEYS
# =====================================================
if "messages" not in st.session_state:
    st.session_state.messages = []

keys_dict = {
    "gemini": get_key("GEMINI_API_KEY"),
    "groq": get_key("GROQ_API_KEY"),
    "mistral": get_key("MISTRAL_API_KEY"),
    "openrouter": get_key("OPENROUTER_API_KEY"),
}

serper_key = get_key("SERPER_API_KEY")
tavily_key = get_key("TAVILY_API_KEY")
jina_key = get_key("JINA_API_KEY")
firecrawl_key = get_key("FIRECRAWL_API_KEY")
ocr_key = get_key("OCR_API_KEY")


# =====================================================
# GEMINI HERO SCREEN (ON FRESH START)
# =====================================================
if not st.session_state.messages:
    st.markdown('<div class="gemini-title">Hello, Explorer</div>', unsafe_allow_html=True)
    st.markdown('<div class="gemini-subtitle">How can I assist you today?</div>', unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if st.button("📝 Create Quiz\nGenerate questions with explanations", use_container_width=True):
            st.session_state.temp_prompt = "Create a 5-question multiple choice quiz on artificial intelligence with answer keys and explanations."
    with col2:
        if st.button("🔍 Live Search\nGet real-time updates from web", use_container_width=True):
            st.session_state.temp_prompt = "What are the latest scientific discoveries and tech news today?"
    with col3:
        if st.button("💻 Debug & Code\nAnalyze and write Python code", use_container_width=True):
            st.session_state.temp_prompt = "Write a high-performance Python script to parse large JSON files concurrently."
    with col4:
        if st.button("📄 Document QA\nExtract key insights from files", use_container_width=True):
            st.session_state.temp_prompt = "Summarize the key points of the uploaded document in clear bullet points."


# =====================================================
# RENDER CHAT HISTORY
# =====================================================
for msg in st.session_state.messages:
    if msg["role"] == "user":
        with st.chat_message("user", avatar="👤"):
            st.markdown(msg["content"])
    elif msg["role"] == "assistant":
        with st.chat_message("assistant", avatar="✨"):
            st.markdown(msg["content"])


# =====================================================
# PROCESS USER INTERACTION (+ ICON FILE UPLOADER)
# =====================================================
temp_prompt = st.session_state.pop("temp_prompt", None)

# st.chat_input with accept_file adds the '+' file upload button beside the text box
chat_input_val = st.chat_input(
    "Ask Gemini AI or attach a file...",
    accept_file=True,
    file_type=["pdf", "docx", "txt", "png", "jpg", "jpeg", "webp"],
)

user_prompt = None
uploaded_file = None

if chat_input_val:
    if hasattr(chat_input_val, "text"):
        user_prompt = chat_input_val.text
        if hasattr(chat_input_val, "files") and chat_input_val.files:
            uploaded_file = chat_input_val.files[0]
    elif isinstance(chat_input_val, dict):
        user_prompt = chat_input_val.get("text", "")
        files = chat_input_val.get("files", [])
        if files:
            uploaded_file = files[0]
    else:
        user_prompt = str(chat_input_val)
elif temp_prompt:
    user_prompt = temp_prompt

if user_prompt or uploaded_file:
    # If the user only attached a file without entering text
    if not user_prompt:
        user_prompt = f"Please analyze and summarize the attached file: {uploaded_file.name}"

    # 1. Show user message with file attachment pill if present
    with st.chat_message("user", avatar="👤"):
        if uploaded_file is not None:
            st.caption(f"📎 Attached: **{uploaded_file.name}**")
        st.markdown(user_prompt)

    display_message = user_prompt
    if uploaded_file is not None:
        display_message = f"📎 *Attached file: {uploaded_file.name}*\n\n{user_prompt}"
    st.session_state.messages.append({"role": "user", "content": display_message})

    # 2. Extract Document Data
    file_context = ""
    if uploaded_file is not None:
        with st.spinner("✨ Gemini is reading your document..."):
            file_context = smart_read_file(uploaded_file, ocr_api_key=ocr_key)

    # 3. Web Search & Scraping
    external_context = ""
    sources_list = []
    urls_in_prompt = re.findall(URL_REGEX, user_prompt)

    with st.spinner("✨ Gemini is searching and analyzing..."):
        if urls_in_prompt:
            target_url = urls_in_prompt[0]
            scraped_content, scraped_sources = smart_scrape(
                url=target_url,
                firecrawl_key=firecrawl_key,
                jina_key=jina_key,
            )
            external_context += scraped_content
            sources_list.extend(scraped_sources)

        elif force_web_search or needs_web_search(user_prompt, groq_api_key=keys_dict.get("groq")):
            search_content, search_sources = smart_search(
                query=user_prompt,
                serper_key=serper_key,
                tavily_key=tavily_key,
                jina_key=jina_key,
            )
            external_context += search_content
            sources_list.extend(search_sources)

    # 4. Automatic Model Selection
    combined_context = f"{file_context}\n{external_context}"
    router_info = select_model_by_task(user_prompt, context_text=combined_context)

    # 5. Build AI Message Payload
    formatted_ai_messages = build_ai_messages(
        system_prompt=DEFAULT_SYSTEM_PROMPT,
        managed_messages=st.session_state.messages[:-1],
        user_prompt=user_prompt,
        file_context=file_context,
        external_context=external_context,
    )

    # 6. Stream Assistant Response
    with st.chat_message("assistant", avatar="✨"):
        # Model Badge
        st.markdown(
            f'<div class="gemini-badge"><span class="gemini-sparkle">✦</span> Powered by <b>{router_info["provider"].title()}</b> ({router_info["model"]})</div>',
            unsafe_allow_html=True,
        )

        response_container = st.empty()
        full_response = ""

        stream_generator = provider_aware_ai_fallback(
            keys_dict=keys_dict,
            router_info=router_info,
            messages=formatted_ai_messages,
        )

        has_failed = False
        for chunk in stream_generator:
            if chunk == "ERROR_ALL_FAILED":
                has_failed = True
                break
            full_response += chunk
            response_container.markdown(full_response + " ▌")

        if has_failed:
            polite_message = "Sorry, please wait a moment. The problem is being fixed."
            response_container.info(f"✨ {polite_message}")
            full_response = polite_message
        else:
            if sources_list:
                full_response += format_sources(sources_list)
            response_container.markdown(full_response)

    # 7. Save Assistant Message to History
    st.session_state.messages.append({"role": "assistant", "content": full_response})
