import os
import re
import streamlit as st
from dotenv import load_dotenv

# Import functions and utilities from helpers.py without modifying helpers.py
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

# Load environment variables from a .env file if available
load_dotenv()

# =====================================================
# PAGE CONFIGURATION & SYSTEM SETTINGS
# =====================================================

st.set_page_config(
    page_title="AI Multi-Model Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

DEFAULT_SYSTEM_PROMPT = (
    "You are a helpful, accurate, and intelligent AI assistant. "
    "Use the provided context (documents or web search results) when relevant. "
    "Always provide well-structured, clear, and concise answers."
)

URL_REGEX = r"https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+[^\s]*"


# =====================================================
# API KEY RESOLUTION HELPER
# =====================================================

def get_key(key_name: str) -> str:
    """
    Retrieve API keys from Streamlit session state, st.secrets, or environment variables.
    """
    # 1. Check Session State (Sidebar user input)
    if st.session_state.get(key_name):
        return st.session_state[key_name].strip()

    # 2. Check Streamlit Secrets
    try:
        if key_name in st.secrets:
            return str(st.secrets[key_name]).strip()
    except Exception:
        pass

    # 3. Check System Environment Variables (.env / OS)
    return os.getenv(key_name, "").strip()


# =====================================================
# SIDEBAR CONFIGURATION & API KEYS
# =====================================================

with st.sidebar:
    st.title("⚙️ Configuration")
    st.markdown("Enter your API keys below or set them in your `.env` / `secrets.toml`.")

    with st.expander("🔑 AI Provider Keys", expanded=False):
        groq_key_input = st.text_input(
            "Groq API Key",
            value=get_key("GROQ_API_KEY"),
            type="password",
            key="GROQ_API_KEY",
        )
        gemini_key_input = st.text_input(
            "Gemini API Key",
            value=get_key("GEMINI_API_KEY"),
            type="password",
            key="GEMINI_API_KEY",
        )
        mistral_key_input = st.text_input(
            "Mistral API Key",
            value=get_key("MISTRAL_API_KEY"),
            type="password",
            key="MISTRAL_API_KEY",
        )
        openrouter_key_input = st.text_input(
            "OpenRouter API Key",
            value=get_key("OPENROUTER_API_KEY"),
            type="password",
            key="OPENROUTER_API_KEY",
        )

    with st.expander("🌐 Search & Tool Keys", expanded=False):
        serper_key_input = st.text_input(
            "Serper API Key",
            value=get_key("SERPER_API_KEY"),
            type="password",
            key="SERPER_API_KEY",
        )
        tavily_key_input = st.text_input(
            "Tavily API Key",
            value=get_key("TAVILY_API_KEY"),
            type="password",
            key="TAVILY_API_KEY",
        )
        jina_key_input = st.text_input(
            "Jina API Key",
            value=get_key("JINA_API_KEY"),
            type="password",
            key="JINA_API_KEY",
        )
        firecrawl_key_input = st.text_input(
            "Firecrawl API Key",
            value=get_key("FIRECRAWL_API_KEY"),
            type="password",
            key="FIRECRAWL_API_KEY",
        )
        ocr_key_input = st.text_input(
            "OCR.space API Key",
            value=get_key("OCR_API_KEY"),
            type="password",
            key="OCR_API_KEY",
        )

    st.markdown("---")
    st.subheader("📁 Upload Context File")
    uploaded_file = st.file_uploader(
        "Upload PDF, DOCX, TXT, or Image",
        type=["pdf", "docx", "txt", "png", "jpg", "jpeg", "webp"],
        key="file_uploader",
    )

    force_web_search = st.checkbox("Force Web Search", value=False)

    if st.button("🗑️ Clear Conversation", use_container_width=True):
        st.session_state.messages = []
        st.rerun()


# =====================================================
# SESSION STATE INITIALIZATION
# =====================================================

if "messages" not in st.session_state:
    st.session_state.messages = []


# Collect all active API keys into a standard dictionary
keys_dict = {
    "groq": get_key("GROQ_API_KEY"),
    "gemini": get_key("GEMINI_API_KEY"),
    "mistral": get_key("MISTRAL_API_KEY"),
    "openrouter": get_key("OPENROUTER_API_KEY"),
}

serper_key = get_key("SERPER_API_KEY")
tavily_key = get_key("TAVILY_API_KEY")
jina_key = get_key("JINA_API_KEY")
firecrawl_key = get_key("FIRECRAWL_API_KEY")
ocr_key = get_key("OCR_API_KEY")


# =====================================================
# RENDER CHAT INTERFACE
# =====================================================

st.title("🤖 Multi-Model AI Assistant")

# Display previous conversation messages
for msg in st.session_state.messages:
    if msg["role"] in ["user", "assistant"]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])


# =====================================================
# PROCESS USER INPUT & MAIN LOGIC
# =====================================================

user_prompt = st.chat_input("Ask a question, paste a link, or inquire about your uploaded file...")

if user_prompt:
    # 1. Display User Message
    st.chat_message("user").markdown(user_prompt)
    st.session_state.messages.append({"role": "user", "content": user_prompt})

    # 2. Extract Document Context if a file is uploaded
    file_context = ""
    if uploaded_file is not None:
        with st.spinner("Processing attached document/image..."):
            file_context = smart_read_file(uploaded_file, ocr_api_key=ocr_key)

    # 3. Detect URLs for direct scraping or perform Smart Search
    external_context = ""
    sources_list = []

    urls_in_prompt = re.findall(URL_REGEX, user_prompt)

    with st.spinner("Checking web context and routing query..."):
        # If user provided a URL in the prompt, scrape it directly
        if urls_in_prompt:
            target_url = urls_in_prompt[0]
            scraped_content, scraped_sources = smart_scrape(
                url=target_url,
                firecrawl_key=firecrawl_key,
                jina_key=jina_key,
            )
            external_context += scraped_content
            sources_list.extend(scraped_sources)

        # Otherwise, check if live search is needed
        elif force_web_search or needs_web_search(user_prompt, groq_api_key=keys_dict.get("groq")):
            search_content, search_sources = smart_search(
                query=user_prompt,
                serper_key=serper_key,
                tavily_key=tavily_key,
                jina_key=jina_key,
            )
            external_context += search_content
            sources_list.extend(search_sources)

    # 4. Route Task to Optimal Model/Provider
    combined_context = f"{file_context}\n{external_context}"
    router_info = select_model_by_task(user_prompt, context_text=combined_context)

    # 5. Build AI Message Payload
    formatted_ai_messages = build_ai_messages(
        system_prompt=DEFAULT_SYSTEM_PROMPT,
        managed_messages=st.session_state.messages[:-1],  # previous history
        user_prompt=user_prompt,
        file_context=file_context,
        external_context=external_context,
    )

    # 6. Stream Assistant Response with Automatic Fallback
    with st.chat_message("assistant"):
        response_container = st.empty()
        full_response = ""

        # Status badge displaying selected primary route
        st.caption(f"⚡ Routed to: **{router_info['provider'].upper()}** (`{router_info['model']}`)")

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
            response_container.markdown(full_response + "▌")

        if has_failed:
            error_message = (
                "⚠️ Sorry, please wait a moment... technical issues are being fixed."
            )
            response_container.error(error_message)
            full_response = error_message
        else:
            # Append formatted sources if any were discovered
            if sources_list:
                full_response += format_sources(sources_list)

            response_container.markdown(full_response)

    # 7. Store Assistant Message in Session History
    st.session_state.messages.append({"role": "assistant", "content": full_response})
