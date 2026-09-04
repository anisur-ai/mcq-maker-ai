import os
import re
import uuid
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
    page_title="Anis AI - Next-Gen Intelligence",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =====================================================
# MODERN 3D OBSIDIAN CSS THEME & GEMINI AURA
# =====================================================
ANIS_AI_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif !important;
    color: #e2e8f0;
}

/* Background Aura */
.stApp {
    background-color: #08090d !important;
    background-image: 
        radial-gradient(at 0% 0%, rgba(59, 130, 246, 0.12) 0px, transparent 50%),
        radial-gradient(at 100% 100%, rgba(168, 85, 247, 0.12) 0px, transparent 50%) !important;
    overflow-x: hidden;
}

/* 3D Glassmorphic Sidebar */
[data-testid="stSidebar"] {
    background: rgba(13, 15, 22, 0.85) !important;
    backdrop-filter: blur(24px) saturate(180%);
    -webkit-backdrop-filter: blur(24px) saturate(180%);
    border-right: 1px solid rgba(255, 255, 255, 0.07);
    box-shadow: 10px 0 40px rgba(0, 0, 0, 0.7);
}

[data-testid="stSidebar"] hr {
    border-color: rgba(255, 255, 255, 0.08);
}

header[data-testid="stHeader"] {
    background: transparent !important;
}

/* Hero Branding */
.anis-title {
    font-size: 3.2rem;
    font-weight: 800;
    letter-spacing: -0.04em;
    background: linear-gradient(135deg, #60a5fa 0%, #c084fc 50%, #f472b6 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 0.3rem;
    filter: drop-shadow(0 4px 18px rgba(96, 165, 250, 0.3));
}

.anis-subtitle {
    font-size: 1.15rem;
    font-weight: 400;
    color: #94a3b8;
    margin-bottom: 1.8rem;
}

/* Chat Input Bar */
[data-testid="stChatInput"] {
    background: rgba(18, 21, 31, 0.95) !important;
    border: 1px solid rgba(255, 255, 255, 0.12) !important;
    border-radius: 20px !important;
    backdrop-filter: blur(16px);
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5) !important;
    transition: all 0.25s ease-in-out;
}

[data-testid="stChatInput"]:focus-within {
    border-color: #60a5fa !important;
    box-shadow: 0 0 25px rgba(96, 165, 250, 0.35) !important;
}

/* Chat Messages */
[data-testid="stChatMessage"] {
    background-color: transparent;
    padding: 0.6rem 0;
}

/* Assistant Message Markdown Formatting */
[data-testid="stChatMessage"] .stMarkdown p {
    font-size: 1.02rem;
    line-height: 1.65;
}

/* Sidebar Chat History Buttons */
[data-testid="stSidebar"] .stButton > button {
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(255, 255, 255, 0.06);
    color: #cbd5e1;
    border-radius: 10px;
    padding: 8px 14px;
    font-size: 0.88rem;
    text-align: left;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

[data-testid="stSidebar"] .stButton > button:hover {
    background: rgba(96, 165, 250, 0.12);
    border-color: rgba(96, 165, 250, 0.4);
    color: #ffffff;
    transform: translateX(3px);
}

/* Quick Action Prompt Cards */
.prompt-card button {
    height: 90px;
    white-space: normal !important;
    text-align: left !important;
    border: 1px solid rgba(255, 255, 255, 0.07) !important;
    background: rgba(255, 255, 255, 0.02) !important;
    border-radius: 14px !important;
    transition: all 0.25s ease;
}

.prompt-card button:hover {
    border-color: #60a5fa !important;
    background: rgba(96, 165, 250, 0.08) !important;
    transform: translateY(-2px);
    box-shadow: 0 8px 25px rgba(0,0,0,0.4);
}
</style>
"""
st.markdown(ANIS_AI_CSS, unsafe_allow_html=True)

# =====================================================
# CONFIGURATION & KEYS
# =====================================================
DEFAULT_SYSTEM_PROMPT = (
    "You are Anis AI, an advanced, highly intelligent, and polite AI assistant. "
    "Always provide answers in a professional, structured Markdown format using headers, bullet points, and code blocks where necessary. "
    "Be direct, insightful, and use any provided document context or web search context accurately."
)

URL_REGEX = r"https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+[^\s]*"

def get_key(key_name: str) -> str:
    """Safely retrieve keys from Streamlit Session State, Secrets, or Environment."""
    if st.session_state.get(key_name):
        return st.session_state[key_name].strip()
    try:
        if key_name in st.secrets:
            return str(st.secrets[key_name]).strip()
    except Exception:
        pass
    return os.getenv(key_name, "").strip()

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
# SESSION STATE & CACHE INITIALIZATION
# =====================================================
if "sessions" not in st.session_state:
    initial_id = str(uuid.uuid4())
    st.session_state.sessions = {
        initial_id: {
            "title": "New Chat",
            "messages": [],
            "file_cache": {}  # Keyed by filename to avoid redundant OCR / reading
        }
    }
    st.session_state.current_session_id = initial_id

if st.session_state.current_session_id not in st.session_state.sessions:
    st.session_state.current_session_id = list(st.session_state.sessions.keys())[0]

current_session = st.session_state.sessions[st.session_state.current_session_id]
messages = current_session["messages"]

# =====================================================
# SIDEBAR: HISTORY & CONTROLS
# =====================================================
with st.sidebar:
    st.markdown("### 💬 **Conversations**")
    
    col_new, col_clear = st.columns([3, 1])
    with col_new:
        if st.button("➕ New Chat", use_container_width=True):
            new_id = str(uuid.uuid4())
            st.session_state.sessions[new_id] = {
                "title": "New Chat",
                "messages": [],
                "file_cache": {}
            }
            st.session_state.current_session_id = new_id
            st.rerun()
            
    with col_clear:
        if st.button("🗑️", help="Clear current chat"):
            current_session["messages"] = []
            current_session["file_cache"] = {}
            st.rerun()

    st.markdown("---")

    # Render conversations
    for sess_id in reversed(list(st.session_state.sessions.keys())):
        sess_data = st.session_state.sessions[sess_id]
        is_active = (sess_id == st.session_state.current_session_id)
        btn_label = f"✨ {sess_data['title']}" if is_active else f"💭 {sess_data['title']}"

        if st.button(btn_label, key=f"sess_{sess_id}", use_container_width=True):
            st.session_state.current_session_id = sess_id
            st.rerun()

    st.markdown("---")
    st.markdown("### 📎 **Attach Context**")
    uploaded_file = st.file_uploader(
        "Upload document or image",
        type=["png", "jpg", "jpeg", "webp", "pdf", "docx", "txt"],
        key="chat_file_uploader",
        label_visibility="collapsed"
    )
    
    force_web_search = st.toggle("🌐 Force Live Web Search", value=False)

# =====================================================
# HERO SCREEN (WHEN CHAT IS EMPTY)
# =====================================================
if not messages:
    st.markdown('<div class="anis-title">Anis AI</div>', unsafe_allow_html=True)
    st.markdown('<div class="anis-subtitle">Empowered with ultra-fast search, multi-model fallback, and intelligence.</div>', unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown('<div class="prompt-card">', unsafe_allow_html=True)
        if st.button("📝 **Create Quiz**\nGenerate interactive questions & answers", use_container_width=True):
            st.session_state.temp_prompt = "Create a 5-question multiple choice quiz on modern AI with explanations."
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
        
    with c2:
        st.markdown('<div class="prompt-card">', unsafe_allow_html=True)
        if st.button("🔍 **Live Research**\nReal-time updates from the web", use_container_width=True):
            st.session_state.temp_prompt = "What are the latest scientific discoveries and tech breakthroughs today?"
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
        
    with c3:
        st.markdown('<div class="prompt-card">', unsafe_allow_html=True)
        if st.button("💻 **Code Engine**\nDebug, write, and optimize code", use_container_width=True):
            st.session_state.temp_prompt = "Write a high-performance Python script to parse large JSON files asynchronously."
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
        
    with c4:
        st.markdown('<div class="prompt-card">', unsafe_allow_html=True)
        if st.button("📄 **Summarize File**\nExtract key insights from documents", use_container_width=True):
            st.session_state.temp_prompt = "Extract and summarize the critical points of the attached document into bullet points."
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

# =====================================================
# RENDER EXISTING CHAT HISTORY
# =====================================================
for msg in messages:
    with st.chat_message(msg["role"], avatar="👤" if msg["role"] == "user" else "✨"):
        st.markdown(msg["content"])

# =====================================================
# USER INPUT & INSTANT PIPELINE EXECUTION
# =====================================================
temp_prompt = st.session_state.pop("temp_prompt", None)
user_input = st.chat_input("Ask Anis AI anything...")

prompt_text = None
if user_input:
    prompt_text = user_input.strip()
elif temp_prompt:
    prompt_text = temp_prompt
elif uploaded_file and not messages:
    prompt_text = f"Analyze the uploaded document '{uploaded_file.name}' and highlight key insights."

if prompt_text:
    # 1. Update Title if first interaction
    if not messages:
        current_session["title"] = prompt_text[:30] + ("..." if len(prompt_text) > 30 else "")

    # 2. Append & Render User Message immediately
    messages.append({"role": "user", "content": prompt_text})
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt_text)

    # 3. Dynamic Status Tracking (Gemini/Perplexity style)
    file_context = ""
    external_context = ""
    sources_list = []

    with st.status("Thinking & gathering information...", expanded=False) as status:
        # A. Process Attached File (With caching to eliminate repeated delay)
        if uploaded_file is not None:
            file_key = f"{uploaded_file.name}_{uploaded_file.size}"
            if file_key in current_session["file_cache"]:
                status.write("⚡ Retrieved file insights from cache...")
                file_context = current_session["file_cache"][file_key]
            else:
                status.write(f"📄 Reading '{uploaded_file.name}'...")
                try:
                    file_context = smart_read_file(uploaded_file, ocr_api_key=ocr_key)
                    current_session["file_cache"][file_key] = file_context
                except Exception as e:
                    status.write(f"⚠️ Could not fully read file: {e}")
                    file_context = ""

        # B. URL Scraping & Live Web Search
        urls_in_prompt = re.findall(URL_REGEX, prompt_text)
        if urls_in_prompt:
            target_url = urls_in_prompt[0]
            status.write(f"🌐 Scraping {target_url}...")
            try:
                scraped_content, scraped_sources = smart_scrape(
                    url=target_url,
                    firecrawl_key=firecrawl_key,
                    jina_key=jina_key,
                )
                external_context += scraped_content
                sources_list.extend(scraped_sources)
            except Exception:
                pass

        elif force_web_search or needs_web_search(prompt_text, groq_api_key=keys_dict.get("groq")):
            status.write("🔍 Searching the live web...")
            try:
                search_content, search_sources = smart_search(
                    query=prompt_text,
                    serper_key=serper_key,
                    tavily_key=tavily_key,
                    jina_key=jina_key,
                )
                external_context += search_content
                sources_list.extend(search_sources)
            except Exception:
                pass

        status.update(label="Ready! Synthesizing response...", state="complete")

    # 4. Model Selection & Context Assembly
    combined_context = f"{file_context}\n{external_context}".strip()
    router_info = select_model_by_task(prompt_text, context_text=combined_context)

    formatted_ai_messages = build_ai_messages(
        system_prompt=DEFAULT_SYSTEM_PROMPT,
        managed_messages=messages[:-1],  # Exclude current user prompt (handled inside builder)
        user_prompt=prompt_text,
        file_context=file_context,
        external_context=external_context,
    )

    # 5. Instant AI Streaming with Reliable Fallback
    with st.chat_message("assistant", avatar="✨"):
        response_box = st.empty()
        full_response = ""

        try:
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
                response_box.markdown(full_response + " ▌")

            if has_failed or not full_response.strip():
                full_response = (
                    "I apologize, but all AI providers are currently experiencing heavy traffic. "
                    "Please try again in a few seconds."
                )
                response_box.warning(f"✨ {full_response}")
            else:
                if sources_list:
                    full_response += "\n\n" + format_sources(sources_list)
                response_box.markdown(full_response)

        except Exception as err:
            full_response = "An unexpected error occurred. Please verify your API keys and try again."
            response_box.error(f"⚠️ {full_response}")

    # 6. Save message directly into session state (No page reload needed!)
    messages.append({"role": "assistant", "content": full_response})
