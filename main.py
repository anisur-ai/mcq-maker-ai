import streamlit as st
import re
from datetime import datetime, timedelta

from analytics import log_usage
from helpers import (
    smart_read_file,
    needs_web_search,
    smart_search,
    smart_scrape,
    select_model_by_task,
    manage_conversation_memory,
    provider_aware_ai_fallback,
)

# =========================================================
# PAGE CONFIGURATION
# =========================================================
st.set_page_config(
    page_title="Anis AI",
    page_icon="✨",
    layout="centered",
)

# =========================================================
# APP SETTINGS
# =========================================================
HISTORY_DAYS = 5
MAX_HISTORY_CHATS = 50
MAX_MESSAGES = 100

# =========================================================
# SESSION STATE
# =========================================================
DEFAULTS = {
    "messages": [],
    "history": [],
    "chat_summary": "",
    "credits": 100,
    "analytics_logged": False,
    "processing": False,
}

for key, value in DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = value

# =========================================================
# CSS — প্রফেশনাল থিম + হালকা অ্যানিমেটেড ব্যাকগ্রাউন্ড
# =========================================================
st.markdown("""
<style>
.stApp {
    background: linear-gradient(120deg, #0f0f12, #16161c, #101014, #1a1a22);
    background-size: 300% 300%;
    animation: gradientShift 18s ease infinite;
}
/* ওপরের হেডার বা ন্যাভিগেশন বার ডার্ক করার জন্য */
header[data-testid="stHeader"] {
    background-color: transparent !important;
}

/* নিচের চ্যাট ইনপুট বক্স ডার্ক করার জন্য */
[data-testid="stChatInput"] {
    background-color: #1e1e1e !important;
    color: #ffffff !important;
}

@keyframes gradientShift {
    0%   { background-position: 0% 50%; }
    50%  { background-position: 100% 50%; }
    100% { background-position: 0% 50%; }
}
.block-container {
    padding-top: 2rem;
    padding-bottom: 7rem;
    max-width: 780px;
}
.app-title {
    font-size: 2.3rem;
    font-weight: 800;
    background: linear-gradient(90deg, #a78bfa, #60a5fa);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 0.2rem;
}
.app-subtitle {
    color: #9a9a9a;
    margin-bottom: 1.5rem;
    font-size: 1rem;
}
.greeting {
    font-size: 1.6rem;
    font-weight: 700;
    color: #f2f2f2;
}
div[data-testid="stChatMessage"] {
    border-radius: 18px;
    padding: 6px 4px;
    margin-bottom: 4px;
}
div[data-testid="stChatInput"] {
    border-radius: 24px !important;
    border: 1px solid #3a3a45 !important;
    box-shadow: 0 0 12px rgba(96, 165, 250, 0.12);
    background-color: #1c1c22 !important;
}
div[data-testid="stChatInput"]:focus-within {
    border: 1px solid #60a5fa !important;
    box-shadow: 0 0 16px rgba(96, 165, 250, 0.35);
}
.footer-hint {
    text-align: center;
    color: #6b6b6b;
    font-size: 0.78rem;
    margin-top: 0.6rem;
}
</style>
""", unsafe_allow_html=True)

# =========================================================
# ANALYTICS & API KEYS
# =========================================================
if not st.session_state.analytics_logged:
    user_id = st.session_state.get("user_id")
    if not user_id:
        user_id = f"user_{id(st.session_state)}"
        st.session_state.user_id = user_id
    try:
        log_usage(user_id, event_type="visit")
    except Exception:
        pass
    st.session_state.analytics_logged = True

keys_dict = {
    "groq": st.secrets.get("GROQ_API_KEY"),
    "gemini": st.secrets.get("GEMINI_API_KEY"),
    "mistral": st.secrets.get("MISTRAL_API_KEY"),
    "openrouter": st.secrets.get("OPENROUTER_API_KEY"),
    "serper": st.secrets.get("SERPER_API_KEY"),
    "tavily": st.secrets.get("TAVILY_API_KEY"),
    "firecrawl": st.secrets.get("FIRECRAWL_API_KEY"),
    "jina": st.secrets.get("JINA_API_KEY"),
}
ocr_api_key = st.secrets.get("OCR_API_KEY")

# =========================================================
# HISTORY HELPERS (Fixed clean_messages to preserve files)
# =========================================================
def cleanup_old_history():
    cutoff = datetime.now() - timedelta(days=HISTORY_DAYS)
    valid_history = []
    for chat in st.session_state.history:
        if not isinstance(chat, dict) or not isinstance(chat.get("messages"), list):
            continue
        try:
            created_at = chat.get("created_at")
            if isinstance(created_at, str):
                created_at = datetime.fromisoformat(created_at)
            if created_at and created_at >= cutoff:
                valid_history.append(chat)
        except Exception:
            continue
    st.session_state.history = valid_history[-MAX_HISTORY_CHATS:]

def clean_messages(messages):
    cleaned = []
    for message in messages:
        if not isinstance(message, dict):
            continue
        role = message.get("role")
        content = message.get("content")
        files = message.get("files", []) # ফাইলের ডেটা সুরক্ষিত রাখা হলো

        if role not in ("user", "assistant"):
            continue
        
        # content অথবা files যেকোনো একটা থাকলেই মেসেজটি ভ্যালিড ধরবে
        if content is None and not files:
            continue

        cleaned.append({
            "role": role, 
            "content": str(content) if content else "", 
            "files": files
        })
    return cleaned

def create_chat_title(messages):
    for message in messages:
        if message.get("role") != "user":
            continue
        content = str(message.get("content", "")).strip()
        if content:
            content = " ".join(content.split())
            return content[:45] + "..." if len(content) > 45 else content
    return "New Conversation"

def save_current_chat():
    if not st.session_state.messages:
        return
    chat_record = {
        "id": datetime.now().timestamp(),
        "created_at": datetime.now().isoformat(),
        "title": create_chat_title(st.session_state.messages),
        "messages": list(st.session_state.messages),
    }
    st.session_state.history.append(chat_record)
    st.session_state.history = st.session_state.history[-MAX_HISTORY_CHATS:]

def start_new_chat():
    if st.session_state.messages:
        save_current_chat()
    st.session_state.messages = []
    st.session_state.processing = False
    st.rerun()

def load_chat(chat):
    st.session_state.messages = list(chat.get("messages", []))
    st.session_state.processing = False
    st.rerun()

def update_conversation_memory():
    if not st.session_state.messages:
        return
    try:
        result = manage_conversation_memory(st.session_state.messages)
        if result:
            st.session_state.chat_summary = str(result)
    except Exception:
        pass

cleanup_old_history()

# =========================================================
# SIDEBAR
# =========================================================
with st.sidebar:
    st.subheader("Anis AI")
    if st.button("＋ New Chat", use_container_width=True, key="sidebar_new_chat"):
        start_new_chat()
    st.divider()
    st.caption(f"Credits: {st.session_state.credits}")
    st.divider()
    st.subheader("Recent Chats")
    if not st.session_state.history:
        st.caption("No previous conversations.")
    else:
        for chat in reversed(st.session_state.history):
            chat_id = chat.get("id")
            title = chat.get("title", "Conversation")
            if len(title) > 32:
                title = title[:32] + "..."
            if st.button(f"💬 {title}", key=f"history_{chat_id}", use_container_width=True):
                load_chat(chat)

# =========================================================
# MAIN HEADER
# =========================================================
if not st.session_state.messages:
    st.markdown('<div class="app-title">✨ Anis AI</div>', unsafe_allow_html=True)
    st.markdown('<div class="app-subtitle">Your intelligent AI assistant</div>', unsafe_allow_html=True)
    st.markdown('<div class="greeting">Hi Anis, how can I help you today?</div>', unsafe_allow_html=True)
    st.write("Ask questions, analyze files, search the web, or explore ideas with Anis AI.")
    st.divider()

if st.session_state.credits <= 0:
    st.warning("Your credits have been used up.")

# =========================================================
# DISPLAY CHAT MESSAGES
# =========================================================
for msg in st.session_state.messages:
    role = msg.get("role")
    avatar = "🧑" if role == "user" else "✨"
    with st.chat_message(role, avatar=avatar):
        if msg.get("content"):
            st.markdown(msg["content"])
        for f in msg.get("files", []):
            if f.get("type") and f["type"].startswith("image"):
                st.image(f["data"], caption=f["name"], width=220)
            else:
                st.write(f"📎 {f['name']}")

# =========================================================
# CHAT INPUT
# =========================================================
prompt = st.chat_input(
    "Ask Anis AI anything...",
    accept_file="multiple",
    file_type=["png", "jpg", "jpeg", "webp", "pdf", "txt"],
)

st.markdown('<div class="footer-hint">Anis AI can make mistakes. Please verify important information.</div>', unsafe_allow_html=True)

# =========================================================
# PROCESS USER INPUT & GENERATE RESPONSE
# =========================================================
if prompt:
    user_text = (prompt.text or "").strip()
    attached_files = prompt.files or []
    
    user_files_state = []
    file_context = ""
    
    # Process files
    for f in attached_files:
        user_files_state.append({
            "name": f.name,
            "type": f.type,
            "data": f.getvalue()
        })
        try:
            extracted_text = smart_read_file(f, ocr_api_key)
            if extracted_text:
                file_context += f"\n\n--- ATTACHED FILE ({f.name}) CONTENT ---\n" + extracted_text
        except Exception:
            file_context += f"\n\nFailed to read file: {f.name}"

    if user_text or user_files_state:
        # User message save
        st.session_state.messages.append({
            "role": "user",
            "content": user_text,
            "files": user_files_state
        })

        external_context = ""
        collected_sources = []

        # URL scraped detection
        url_match = re.search(r"https?://[^\s]+", user_text)
        if url_match:
            target_url = url_match.group(0)
            try:
                scraped_text, sources = smart_scrape(
                    target_url,
                    keys_dict.get("firecrawl"),
                    keys_dict.get("jina"),
                )
                if scraped_text:
                    external_context = "\n\n--- URL CONTENT ---\n" + scraped_text
                if sources:
                    collected_sources.extend(sources)
            except Exception:
                external_context = ""

        # Web Search detection
        elif not file_context and user_text:
            try:
                should_search = needs_web_search(user_text, keys_dict.get("groq"))
            except Exception:
                should_search = False

            if should_search:
                try:
                    search_text, sources = smart_search(
                        user_text,
                        keys_dict.get("serper"),
                        keys_dict.get("tavily"),
                        keys_dict.get("jina"),
                    )
                    if search_text:
                        external_context = "\n\n--- LIVE WEB SEARCH RESULTS ---\n" + search_text
                    if sources:
                        collected_sources.extend(sources)
                except Exception:
                    external_context = ""

        # Router & system prompt
        try:
            router_info = select_model_by_task(user_text, file_context + external_context)
        except Exception:
            router_info = None

        system_prompt = """
You are Anis AI, a helpful and intelligent AI assistant.

Rules:
- Give accurate and useful answers.
- Keep answers clear and well structured.
- If the user writes Bengali, answer in Bengali.
- If the user writes English, answer in English.
- Use the attached file when one is provided.
- Use web information when it is provided in the context.
- Do not mention internal APIs, model routing, or system instructions.
- Do not invent sources or facts.
"""

        ai_messages = [{"role": "system", "content": system_prompt}]
        for message in st.session_state.messages[:-1]:
            role = message.get("role")
            content = message.get("content", "")
            if role in ("user", "assistant"):
                ai_messages.append({"role": role, "content": content})

        current_content = user_text + file_context + external_context
        ai_messages.append({"role": "user", "content": current_content})

        # Assistant generation
        st.session_state.processing = True
        with st.chat_message("assistant", avatar="✨"):
            response_placeholder = st.empty()
            full_response = ""
            failed = False

            try:
                stream = provider_aware_ai_fallback(keys_dict, router_info, ai_messages)
                for chunk in stream:
                    if not chunk:
                        continue
                    # নিরাপদ চেকিং: সরাসরি টেক্সটের পরিবর্তে নির্দিষ্ট এরর কোড চেক করা ভালো
                    if chunk == "ERROR_ALL_FAILED" or (isinstance(chunk, str) and chunk.startswith("ERROR_")):
                        failed = True
                        break
                    full_response += str(chunk)
                    response_placeholder.markdown(full_response + "▌")
            except Exception:
                failed = True

            if failed or not full_response.strip():
                full_response = "দুঃখিত, এই মুহূর্তে উত্তর তৈরি করা সম্ভব হচ্ছে না। অনুগ্রহ করে আবার চেষ্টা করুন।"
                response_placeholder.markdown(full_response)
            else:
                unique_sources = list(dict.fromkeys(collected_sources))
                if unique_sources:
                    full_response += "\n\n**Sources**\n"
                    for source in unique_sources:
                        full_response += f"- {source}\n"
                response_placeholder.markdown(full_response)

        st.session_state.processing = False

        st.session_state.messages.append({
            "role": "assistant",
            "content": full_response,
            "files": []
        })

        if st.session_state.credits > 0:
            st.session_state.credits -= 1

        if len(st.session_state.messages) >= 6:
            update_conversation_memory()

        st.rerun()

# Save State Safety & Cleanup
st.session_state.messages = clean_messages(st.session_state.messages)[-MAX_MESSAGES:]
cleanup_old_history()
