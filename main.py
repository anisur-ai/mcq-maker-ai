import streamlit as st
import re

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

# -------------------------------
# Streamlit Page Configuration
# -------------------------------

st.set_page_config(
    page_title="Anis AI - Personal AI Assistant & Study Partner",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# -------------------------------
# Usage Analytics
# -------------------------------

if "analytics_logged" not in st.session_state:
    user_id = st.session_state.get("user_id")

    if not user_id:
        user_id = f"user_{id(st.session_state)}"
        st.session_state.user_id = user_id

    log_usage(user_id, event_type="visit")
    st.session_state.analytics_logged = True

# -------------------------------
# Styling - Gemini-like Input Bar
# -------------------------------

st.markdown("""
<style>

[data-testid="collapsedControl"]{
    display: none;
}

.stChatMessage{
    background: transparent !important;
}

.block-container{
    padding-top: 2rem;
    padding-bottom: 6rem;
    max-width: 900px;
    margin: 0 auto;
}

footer{
    visibility: hidden;
}

/* Gemini-style input card at bottom */
.input-card {
    position: fixed;
    bottom: 20px;
    left: 50%;
    transform: translateX(-50%);
    width: 90%;
    max-width: 900px;
    background: #1e1e1e;
    border: 1px solid #3f3f3f;
    border-radius: 24px;
    padding: 16px;
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3);
    z-index: 999;
}

.input-card textarea {
    background: transparent !important;
    border: none !important;
    color: #fff !important;
    font-size: 15px !important;
    resize: none !important;
    outline: none !important;
}

.input-card textarea::placeholder {
    color: #999 !important;
}

.input-row {
    display: flex;
    gap: 12px;
    align-items: flex-end;
}

.plus-btn-container {
    display: flex;
    align-items: center;
    justify-content: center;
}

.plus-btn-container button {
    width: 40px !important;
    height: 40px !important;
    min-width: 40px !important;
    padding: 0 !important;
    border-radius: 50% !important;
    font-size: 20px !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    background-color: transparent !important;
    border: none !important;
    cursor: pointer !important;
}

.action-buttons {
    display: flex;
    gap: 8px;
    align-items: center;
}

.action-buttons button {
    min-width: 0 !important;
    height: 40px !important;
    padding: 0 12px !important;
    border-radius: 20px !important;
    font-size: 14px !important;
    font-weight: 500 !important;
}

/* Attachment menu styling */
.attach-menu {
    background: #2a2a2a;
    border: 1px solid #3f3f3f;
    border-radius: 12px;
    padding: 8px;
    margin-top: 8px;
}

.attach-menu button {
    width: 100% !important;
    text-align: left !important;
    padding: 10px 12px !important;
    border-radius: 8px !important;
    font-size: 13px !important;
    border: none !important;
    background: transparent !important;
    color: #fff !important;
    cursor: pointer !important;
}

.attach-menu button:hover {
    background: #3f3f3f !important;
}

</style>
""", unsafe_allow_html=True)

# -------------------------------
# API Keys
# -------------------------------

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

# -------------------------------
# Header
# -------------------------------

st.markdown(
"""
<h1 style="text-align:center; margin-bottom: 2rem;">
Anis AI
</h1>
""",
unsafe_allow_html=True,
)

st.markdown(
"""
<p style="text-align:center; color:#888; margin-bottom: 3rem;">
How can I help you today?
</p>
""",
unsafe_allow_html=True,
)

# -------------------------------
# Session State
# -------------------------------

if "messages" not in st.session_state:
    st.session_state.messages = []

if "chat_summary" not in st.session_state:
    st.session_state.chat_summary = ""

if "show_attach_menu" not in st.session_state:
    st.session_state.show_attach_menu = False

if "attach_mode" not in st.session_state:
    st.session_state.attach_mode = None

if "selected_file" not in st.session_state:
    st.session_state.selected_file = None

# -------------------------------
# Show Previous Chat
# -------------------------------

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# If a file was previously selected, show a small preview/notice
if st.session_state.selected_file is not None:
    sel = st.session_state.selected_file
    try:
        if hasattr(sel, 'type') and sel.type.startswith('image'):
            st.image(sel.getvalue() if hasattr(sel, 'getvalue') else sel.read())
        else:
            st.markdown(f"**Attached:** {getattr(sel, 'name', 'file')}")
    except Exception:
        st.markdown(f"**Attached:** {getattr(sel, 'name', 'file')}")

# Add spacing for sticky bottom input
st.markdown("<div style='height: 150px;'></div>", unsafe_allow_html=True)

# -------------------------------
# Attachment Input Widgets (BEFORE Chat Input Form)
# -------------------------------

if st.session_state.attach_mode == 'camera':
    cam = st.camera_input("Capture an image")
    if cam is not None:
        st.session_state.selected_file = cam
        st.session_state.attach_mode = None
        st.rerun()

elif st.session_state.attach_mode == 'gallery':
    gallery_file = st.file_uploader("Select an image from gallery", type=["jpg","jpeg","png","webp"], key="gallery_uploader")
    if gallery_file is not None:
        st.session_state.selected_file = gallery_file
        st.session_state.attach_mode = None
        st.rerun()

elif st.session_state.attach_mode == 'file':
    doc_file = st.file_uploader("Select a document or file", type=None, key="doc_uploader")
    if doc_file is not None:
        st.session_state.selected_file = doc_file
        st.session_state.attach_mode = None
        st.rerun()

# -------------------------------
# Gemini-Style Bottom Input Bar (Fixed Position)
# ==========================================
# Gemini-Style Bottom Input Bar & CSS
# ==========================================
st.markdown("""
<style>
/* Streamlit-এর কলামগুলোকে মোবাইলেও এক সারিতে পাশাপাশি রাখার ফিক্স */
[data-testid="column"] {
    width: calc(33.3333% - 1rem) !important;
    flex: 1 1 calc(33.3333% - 1rem) !important;
    min-width: calc(33.3333% - 1rem) !important;
}

/* বটম ইনপুট কন্টেইনার স্টাইলিং */
div[data-testid="stForm"] {
    border: 1px solid #30363d !important;
    background-color: #1e1f23 !important;
    border-radius: 20px !important;
    padding: 10px 14px !important;
    box-shadow: 0 4px 12px rgba(0,0,0,0.3) !important;
}

/* ইনপুট ফিল্ডের বর্ডার ও ব্যাকগ্রাউন্ড ক্লিন করা */
div[data-testid="stTextArea"] textarea {
    background-color: transparent !important;
    border: none !important;
    color: #ffffff !important;
    font-size: 15px !important;
    box-shadow: none !important;
}

div[data-testid="stTextArea"] textarea:focus {
    border: none !important;
    box-shadow: none !important;
}

/* প্লাস এবং সেন্ড বাটন গোল করা */
div[data-testid="stForm"] button {
    border-radius: 50% !important;
    width: 38px !important;
    height: 38px !important;
    padding: 0 !important;
    background-color: #2b2d31 !important;
    color: #ffffff !important;
    border: none !important;
}

/* অ্যাটাচমেন্ট পপ-আপ মেনু বাটন স্টাইল */
.attach-box button {
    width: 100% !important;
    background-color: #2b2d31 !important;
    color: #ffffff !important;
    border: 1px solid #3e4046 !important;
    border-radius: 10px !important;
    padding: 6px 2px !important;
    font-size: 12px !important;
}
</style>
""", unsafe_allow_html=True)

# --- Attachment Popover Menu (ইনপুট বক্সের ঠিক উপরে দেখাবে) ---
if st.session_state.get("show_attach_menu", False):
    st.markdown("<div class='attach-box'>", unsafe_allow_html=True)
    m_col1, m_col2, m_col3 = st.columns(3)

    with m_col1:
        if st.button("📷 Camera", key="btn_cam"):
            st.session_state.attach_mode = 'camera'
            st.session_state.show_attach_menu = False
            st.rerun()

    with m_col2:
        if st.button("🖼️ Gallery", key="btn_gal"):
            st.session_state.attach_mode = 'gallery'
            st.session_state.show_attach_menu = False
            st.rerun()

    with m_col3:
        if st.button("📁 File", key="btn_file"):
            st.session_state.attach_mode = 'file'
            st.session_state.show_attach_menu = False
            st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

# --- Main Input Form ---
with st.form(key="chat_form", clear_on_submit=True):
    user_text = st.text_area(
        "Ask Anis AI...",
        key="message_input",
        height=60,
        placeholder="Ask Anis AI...",
        label_visibility="collapsed"
    )
    
    btn_col1, btn_col2, btn_col3 = st.columns([1, 6, 1])
    
    with btn_col1:
        plus_clicked = st.form_submit_button("➕")
        
    with btn_col2:
        pass
        
    with btn_col3:
        submitted = st.form_submit_button("➔")

if plus_clicked:
    st.session_state.show_attach_menu = not st.session_state.get("show_attach_menu", False)
    st.rerun()

# -------------------------------
# Handle Send / Message Submission
# -------------------------------

if submitted and (user_text and user_text.strip()):

    prompt = user_text.strip()

    st.session_state.messages.append(
        {
            "role": "user",
            "content": prompt,
        }
    )

    with st.chat_message("user"):
        st.markdown(prompt)

    collected_sources = []
    file_context = ""
    external_context = ""

    # Read Attached File (if any)
    if st.session_state.selected_file is not None:
        try:
            file_context = smart_read_file(
                st.session_state.selected_file,
                ocr_api_key
            )

            if file_context:
                file_context = (
                    "\n\n--- ATTACHED FILE CONTENT ---\n"
                    + file_context
                )
        except Exception as e:
            print("File read error:", e)

        st.session_state.selected_file = None

    # URL Detection
    url_match = re.search(
        r"https?://[^\s]+",
        prompt
    )

    # External Context
    if url_match:
        target_url = url_match.group(0)

        scraped_text, collected_sources = smart_scrape(
            target_url,
            keys_dict.get("firecrawl"),
            keys_dict.get("jina")
        )

        external_context = (
            "\n\n--- URL CONTENT ---\n"
            + scraped_text
        )

    else:
        should_search = needs_web_search(
            prompt,
            keys_dict.get("groq")
        )

        if should_search:
            search_text, collected_sources = smart_search(
                prompt,
                keys_dict.get("serper"),
                keys_dict.get("tavily"),
                keys_dict.get("jina")
            )

            if search_text:
                external_context = f"\n\n--- LIVE WEB SEARCH RESULTS ---\n{search_text}"

    # Model Router
    router_info = select_model_by_task(
        prompt,
        file_context + external_context
    )

    # Conversation Memory
    managed_messages = st.session_state.messages
    st.session_state.chat_summary = ""

    # System Prompt
    system_prompt = (
        "You are Anis AI, a professional autonomous AI assistant.\n\n"
        "Rules:\n"
        "- Think carefully before answering.\n"
        "- Never expose internal reasoning.\n"
        "- Never mention routing, fallback, providers or internal systems.\n"
        "- Automatically detect the user's language.\n"
        "- Reply in Bengali if the user writes in Bengali.\n"
        "- Read attached files automatically.\n"
        "- Read URLs automatically.\n"
        "- Use live web search only when necessary.\n"
        "- Give accurate and concise answers.\n"
        "- If external information was used, add a Sources section.\n"
        "- If no external information was used, do not add Sources.\n"
    )

    ai_messages = [
        {
            "role": "system",
            "content": system_prompt,
        }
    ]

    for msg in managed_messages:
        ai_messages.append(msg)

    final_prompt = (
        prompt
        + file_context
        + external_context
    )

    ai_messages.append(
        {
            "role": "user",
            "content": final_prompt,
        }
    )

    # Assistant Response
    with st.chat_message("assistant"):

        response_placeholder = st.empty()
        full_response = ""
        has_error = False

        try:
            stream = provider_aware_ai_fallback(
                keys_dict,
                router_info,
                ai_messages,
            )

            for chunk in stream:
                if (
                    chunk == "ERROR_ALL_FAILED"
                    or chunk.startswith("দুঃখিত")
                ):
                    has_error = True
                    break

                full_response += chunk
                response_placeholder.markdown(
                    full_response + "▌"
                )

            if has_error or not full_response:
                error_message = (
                    "দুঃখিত কিছুক্ষণ অপেক্ষা করুন "
                    "টেকনিক্যাল সমস্যা হয়েছে ঠিক করা হচ্ছে"
                )

                response_placeholder.markdown(error_message)
                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": error_message,
                    }
                )

            else:
                if collected_sources:
                    full_response += "\n\n**Sources**\n"
                    for source in sorted(set(collected_sources)):
                        full_response += f"- {source}\n"

                response_placeholder.markdown(full_response)
                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": full_response,
                    }
                )

        except Exception:
            error_message = (
                "দুঃখিত কিছুক্ষণ অপেক্ষা করুন "
                "টেকনিক্যাল সমস্যা হয়েছে ঠিক করা হচ্ছে"
            )

            response_placeholder.markdown(error_message)
            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": error_message,
                }
            )
