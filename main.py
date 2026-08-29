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
# PAGE CONFIGURATION (DARK & PROFESSIONAL)
# =====================================================
st.set_page_config(
    page_title="Anis AI",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =====================================================
# PURE DARK MODE + 3D DEPTH CUSTOM CSS
# =====================================================
ANIS_AI_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');

/* Main HTML & Base */
html, body, [class*="css"] {
    font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
    color: #e6edf3;
}

/* 3D Modern Obsidian Background with Radial Ambient Glows */
.stApp {
    background-color: #090a0f;
    background-image: 
        radial-gradient(at 0% 0%, rgba(66, 133, 244, 0.12) 0px, transparent 50%),
        radial-gradient(at 100% 0%, rgba(155, 114, 207, 0.10) 0px, transparent 50%),
        radial-gradient(at 50% 100%, rgba(217, 101, 112, 0.08) 0px, transparent 60%);
    background-attachment: fixed;
    color: #e6edf3;
}

/* Sidebar with 3D Glassmorphism */
[data-testid="stSidebar"] {
    background: rgba(14, 16, 22, 0.85) !important;
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
    border-right: 1px solid rgba(255, 255, 255, 0.08);
    box-shadow: 10px 0 30px rgba(0, 0, 0, 0.5);
}

[data-testid="stSidebar"] hr {
    border-color: rgba(255, 255, 255, 0.08);
}

header[data-testid="stHeader"] {
    background: transparent;
}

/* Anis AI 3D Gradient Heading */
.anis-title {
    font-size: 3.4rem;
    font-weight: 700;
    letter-spacing: -0.03em;
    background: linear-gradient(135deg, #60a5fa 0%, #c084fc 50%, #f472b6 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 0.2rem;
    line-height: 1.2;
    text-shadow: 0 10px 30px rgba(96, 165, 250, 0.2);
}

.anis-subtitle {
    font-size: 1.3rem;
    font-weight: 400;
    color: #94a3b8;
    margin-bottom: 2rem;
}

/* Chat Messages */
[data-testid="stChatMessage"] {
    background-color: transparent;
    border: none;
    padding: 1rem 0;
}

/* User Message Bubble */
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) {
    background: linear-gradient(135deg, #1e2433 0%, #171b26 100%);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 20px 20px 4px 20px;
    padding: 14px 20px;
    margin: 8px 0 16px auto;
    max-width: 80%;
    width: fit-content;
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4);
}

/* Assistant Message */
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarAssistant"]) {
    background-color: transparent;
    padding-left: 0;
}

/* 3D Elevated Input Box */
[data-testid="stChatInput"] {
    background: rgba(18, 20, 29, 0.9) !important;
    border: 1px solid rgba(255, 255, 255, 0.12) !important;
    border-radius: 24px !important;
    backdrop-filter: blur(12px);
    box-shadow: 0 10px 35px rgba(0, 0, 0, 0.6) !important;
}

[data-testid="stChatInput"]:focus-within {
    border-color: #60a5fa !important;
    box-shadow: 0 10px 40px rgba(96, 165, 250, 0.25) !important;
}

[data-testid="stChatInput"] textarea {
    color: #f1f5f9;
}

/* Plus File Upload Expander Bar */
.streamlit-expanderHeader {
    background-color: #12141d !important;
    border-radius: 12px !important;
    border: 1px solid rgba(255, 255, 255, 0.08) !important;
    color: #94a3b8 !important;
}

/* History items in Sidebar */
.history-item {
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(255, 255, 255, 0.05);
    border-radius: 10px;
    padding: 8px 12px;
    margin-bottom: 6px;
    font-size: 0.88rem;
    color: #cbd5e1;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}
.history-item:hover {
    background: rgba(255, 255, 255, 0.07);
    border-color: rgba(96, 165, 250, 0.3);
}

/* Buttons */
.stButton > button {
    background: linear-gradient(135deg, #1e2230 0%, #151821 100%);
    color: #e2e8f0;
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 14px;
    font-weight: 500;
    transition: all 0.3s ease;
    box-shadow: 0 4px 14px rgba(0, 0, 0, 0.3);
}

.stButton > button:hover {
    border-color: #60a5fa;
    color: #ffffff;
    box-shadow: 0 6px 20px rgba(96, 165, 250, 0.2);
}
</style>
"""
st.markdown(ANIS_AI_CSS, unsafe_allow_html=True)

# =====================================================
# CONSTANTS & UTILITIES
# =====================================================
DEFAULT_SYSTEM_PROMPT = (
    "You are Anis AI, a helpful, highly knowledgeable, polite, and advanced AI assistant. "
    "Format all answers with clean Markdown, bullet points, and code blocks where appropriate. "
    "Use any provided document context or web search results precisely."
)

URL_REGEX = r"https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+[^\s]*"

def get_key(key_name: str) -> str:
    """Fetch API keys securely from Session State, Streamlit Secrets, or OS Environment."""
    if st.session_state.get(key_name):
        return st.session_state[key_name].strip()
    try:
        if key_name in st.secrets:
            return str(st.secrets[key_name]).strip()
    except Exception:
        pass
    return os.getenv(key_name, "").strip()


# Load Keys Silently
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
# SESSION STATE INITIALIZATION
# =====================================================
if "messages" not in st.session_state:
    st.session_state.messages = []


# =====================================================
# SIDEBAR: CHAT HISTORY ONLY
# =====================================================
with st.sidebar:
    st.markdown("### 💬 **চ্যাট হিস্টরি**")
    
    if st.button("➕ নতুন চ্যাট (New Chat)", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

    st.markdown("---")

    # Display list of past user questions
    user_queries = [m["content"] for m in st.session_state.messages if m["role"] == "user"]
    if user_queries:
        for idx, query in enumerate(reversed(user_queries[-15:]), 1):
            st.markdown(f'<div class="history-item">💭 {query}</div>', unsafe_allow_html=True)
    else:
        st.caption("এখনো কোনো কথোপকথন শুরু হয়নি।")

    st.markdown("---")
    force_web_search = st.checkbox("🌐 সর্বদা লাইভ সার্চ করুন", value=False)


# =====================================================
# ANIS AI HERO SCREEN (ON FRESH START)
# =====================================================
if not st.session_state.messages:
    st.markdown('<div class="anis-title">Anis AI</div>', unsafe_allow_html=True)
    st.markdown('<div class="anis-subtitle">Hello! How can I assist you today?</div>', unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if st.button("📝 Create Quiz\nGenerate questions with answers", use_container_width=True):
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
# PLUS (+) FILE UPLOADER UNDER CHAT AREA
# =====================================================
with st.expander("➕ ফাইল বা ছবি যুক্ত করুন (PDF, DOCX, TXT, Images)", expanded=False):
    uploaded_file = st.file_uploader(
        "ফাইল আপলোড করুন",
        type=["pdf", "docx", "txt", "png", "jpg", "jpeg", "webp"],
        label_visibility="collapsed",
        key="file_uploader",
    )


# =====================================================
# PROCESS USER INTERACTION
# =====================================================
temp_prompt = st.session_state.pop("temp_prompt", None)
user_prompt = st.chat_input("Ask Anis AI or type a prompt...") or temp_prompt

if user_prompt:
    # 1. Show user message
    st.chat_message("user", avatar="👤").markdown(user_prompt)
    st.session_state.messages.append({"role": "user", "content": user_prompt})

    # 2. Extract Document Data
    file_context = ""
    if uploaded_file is not None:
        with st.spinner("✨ Anis AI ফাইলটি বিশ্লেষণ করছে..."):
            file_context = smart_read_file(uploaded_file, ocr_api_key=ocr_key)

    # 3. Web Search & Scraping
    external_context = ""
    sources_list = []
    urls_in_prompt = re.findall(URL_REGEX, user_prompt)

    with st.spinner("✨ Anis AI তথ্য অনুসন্ধান করছে..."):
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

    # 4. Automatic Model Selection (Internal Routing)
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

    # 6. Stream Assistant Response (NO API BADGE)
    with st.chat_message("assistant", avatar="✨"):
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

        # ইউজার-ফ্রেন্ডলি মেসেজ
        if has_failed:
            polite_message = "Sorry, please wait a moment. The problem is being fixed."
            response_container.info(f"✨ {polite_message}")
            full_response = polite_message
        else:
            if sources_list:
                full_response += format_sources(sources_list)
            response_container.markdown(full_response)

    # 7. Save Assistant Message to History & Refresh Sidebar
    st.session_state.messages.append({"role": "assistant", "content": full_response})
    st.rerun()
