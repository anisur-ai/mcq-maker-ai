import streamlit as st
import re
import html

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
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="Anis AI",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# =========================================================
# ANALYTICS
# =========================================================

if "analytics_logged" not in st.session_state:
    user_id = st.session_state.get("user_id")
    if not user_id:
        user_id = f"user_{id(st.session_state)}"
        st.session_state.user_id = user_id

    log_usage(user_id, event_type="visit")
    st.session_state.analytics_logged = True

# =========================================================
# SESSION STATE
# =========================================================

defaults = {
    "messages": [],
    "chat_summary": "",
    "show_attach_menu": False,
    "attach_mode": None,
    "selected_file": None,
    "history": [],
    "credits": 100,
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value

# =========================================================
# API KEYS
# =========================================================

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
# GEMINI STYLED CSS CUSTOMIZATION
# =========================================================

st.markdown(
    """
<style>
/* Global Layout Base */
html, body, [data-testid="stAppViewContainer"] {
    background: #131314 !important;
    color: #e3e2e6 !important;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
}

[data-testid="stHeader"] {
    display: none !important;
}

footer, [data-testid="collapsedControl"] {
    display: none !important;
}

.block-container {
    max-width: 850px !important;
    padding-top: 60px !important;
    padding-bottom: 110px !important;
    margin: auto;
}

/* Fixed Header Navbar (Ref: Image 1) */
.gemini-topbar {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    height: 56px;
    background: #131314;
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 16px;
    z-index: 999;
}

.gemini-title {
    font-size: 17px;
    font-weight: 500;
    color: #e3e2e6;
    display: flex;
    align-items: center;
    gap: 8px;
}

/* Welcome Screen */
.welcome-wrap {
    text-align: left;
    padding: 40px 10px 20px;
}

.welcome-orb {
    font-size: 32px;
    color: #4c8df6;
    margin-bottom: 12px;
}

.welcome-title {
    font-size: 32px;
    font-weight: 500;
    color: #e3e2e6;
    margin: 0 0 8px;
}

/* Chat Messages */
.stChatMessage {
    background: transparent !important;
    border: 0 !important;
    padding: 12px 0 !important;
}

[data-testid="stChatMessageContent"] {
    border-radius: 18px;
    background: #1e1f20 !important;
    color: #e3e2e6 !important;
}

div[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) [data-testid="stChatMessageContent"] {
    background: #282a2c !important;
}

/* Bottom Input Floating Pill Container (Ref: Image 3) */
div[data-testid="stForm"] {
    position: fixed;
    bottom: 16px;
    left: 50%;
    transform: translateX(-50%);
    width: min(820px, calc(100% - 24px));
    background: #1e1f20 !important;
    border: 1px solid #333537 !important;
    border-radius: 28px !important;
    padding: 4px 12px !important;
    z-index: 1000;
    box-shadow: 0 4px 20px rgba(0,0,0,0.4);
}

div[data-testid="stTextInput"] input {
    background: transparent !important;
    color: #e3e2e6 !important;
    border: none !important;
    box-shadow: none !important;
    font-size: 15px !important;
}

div[data-testid="stTextInput"] label {
    display: none !important;
}

/* Custom Buttons Styling */
.stFormSubmitButton > button {
    background: transparent !important;
    border: none !important;
    color: #c4c6d0 !important;
    font-size: 20px !important;
    box-shadow: none !important;
}

.send-btn-pill > button {
    background: #4c8df6 !important;
    color: #ffffff !important;
    border-radius: 50% !important;
    width: 40px !important;
    height: 40px !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
}

/* Bottom Drawer Attachment Sheet (Ref: Image 2) */
.attach-sheet {
    position: fixed;
    bottom: 80px;
    left: 50%;
    transform: translateX(-50%);
    width: min(800px, calc(100% - 32px));
    background: #282a2c;
    border-radius: 24px 24px 16px 16px;
    padding: 16px;
    z-index: 1001;
    border: 1px solid #3d3f42;
}

.sheet-handle {
    width: 32px;
    height: 4px;
    background: #8e918f;
    border-radius: 2px;
    margin: 0 auto 16px;
}
</style>
""",
    unsafe_allow_html=True,
)

# =========================================================
# SIDEBAR (HISTORY DRAGGER)
# =========================================================

with st.sidebar:
    st.markdown("### 🕘 Chat History")
    if st.button("➕ New Chat", use_container_width=True):
        if st.session_state.messages:
            st.session_state.history.append(list(st.session_state.messages))
        st.session_state.messages = []
        st.session_state.chat_summary = ""
        st.session_state.selected_file = None
        st.rerun()

    st.markdown("---")
    if not st.session_state.history:
        st.caption("No previous history")
    else:
        for i, old_chat in enumerate(reversed(st.session_state.history[-15:])):
            title = "Conversation"
            for msg in old_chat:
                if msg.get("role") == "user":
                    title = msg.get("content", "")[:30]
                    break
            if st.button(title, key=f"hist_{i}", use_container_width=True):
                st.session_state.messages = old_chat
                st.rerun()

# =========================================================
# TOP NAVBAR (1st Image Inspired)
# =========================================================

h_left, h_right = st.columns([6, 1])

with h_left:
    st.markdown(
        """
        <div class="gemini-topbar">
            <div class="gemini-title">
                ✦ Anis AI
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with h_right:
    if st.button("➕ New", key="top_new_chat"):
        if st.session_state.messages:
            st.session_state.history.append(list(st.session_state.messages))
        st.session_state.messages = []
        st.session_state.chat_summary = ""
        st.session_state.selected_file = None
        st.rerun()

# =========================================================
# WELCOME SCREEN
# =========================================================

if not st.session_state.messages:
    st.markdown(
        """
        <div class="welcome-wrap">
            <div class="welcome-orb">✦</div>
            <h1 class="welcome-title">How can Anis AI help you today?</h1>
        </div>
        """,
        unsafe_allow_html=True,
    )

# =========================================================
# CHAT CONTAINER (STAYS ABOVE INPUT)
# =========================================================

chat_container = st.container()

with chat_container:
    for idx, message in enumerate(st.session_state.messages):
        role = message["role"]
        content = message["content"]

        with st.chat_message(role):
            st.markdown(content)

# =========================================================
# ATTACHMENT MODAL SHEET (2nd Image Inspired)
# =========================================================

if st.session_state.show_attach_menu:
    st.markdown('<div class="attach-sheet"><div class="sheet-handle"></div>', unsafe_allow_html=True)
    
    if st.button("📷   Camera", use_container_width=True, key="opt_cam"):
        st.session_state.attach_mode = "camera"
        st.session_state.show_attach_menu = False
        st.rerun()

    if st.button("🖼️   Gallery", use_container_width=True, key="opt_gal"):
        st.session_state.attach_mode = "gallery"
        st.session_state.show_attach_menu = False
        st.rerun()

    if st.button("📁   Files", use_container_width=True, key="opt_file"):
        st.session_state.attach_mode = "file"
        st.session_state.show_attach_menu = False
        st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)

# Attachment Pickers Execution
if st.session_state.attach_mode == "camera":
    cam = st.camera_input("Take Photo")
    if cam:
        st.session_state.selected_file = cam
        st.session_state.attach_mode = None
        st.rerun()

elif st.session_state.attach_mode == "gallery":
    gal = st.file_uploader("Select Image", type=["jpg", "png", "jpeg", "webp"], key="gal_up")
    if gal:
        st.session_state.selected_file = gal
        st.session_state.attach_mode = None
        st.rerun()

elif st.session_state.attach_mode == "file":
    doc = st.file_uploader("Select File", type=None, key="doc_up")
    if doc:
        st.session_state.selected_file = doc
        st.session_state.attach_mode = None
        st.rerun()

# Attachment Preview
if st.session_state.selected_file is not None:
    f_name = getattr(st.session_state.selected_file, "name", "Image/File Attached")
    st.info(f"📎 Attached: {html.escape(f_name)}")

# =========================================================
# CAPSULE INPUT BAR (3rd Image Inspired)
# =========================================================

with st.form(key="chat_form", clear_on_submit=True):
    col_plus, col_input, col_send = st.columns([1, 8, 1])

    with col_plus:
        attach_clicked = st.form_submit_button("＋")

    with col_input:
        user_text = st.text_input("Message", placeholder="Ask Anis AI...", label_visibility="collapsed")

    with col_send:
        submitted = st.form_submit_button("➔")

if attach_clicked:
    st.session_state.show_attach_menu = not st.session_state.show_attach_menu
    st.rerun()

# =========================================================
# BACKEND AI PROCESSING
# =========================================================

has_file = st.session_state.selected_file is not None
if submitted and (user_text.strip() or has_file):
    prompt = user_text.strip() if user_text else "Analyze this attached file/image."

    st.session_state.messages.append({"role": "user", "content": prompt})

    collected_sources = []
    file_context = ""
    external_context = ""
    scraped_text = ""
    search_text = ""

    if has_file:
        try:
            file_context = smart_read_file(st.session_state.selected_file, ocr_api_key)
            if file_context:
                file_context = "\n\n--- ATTACHED FILE CONTENT ---\n" + file_context
        except Exception as e:
            print("File read error:", e)

        st.session_state.selected_file = None

    url_match = re.search(r"https?://[^\s]+", prompt)

    if url_match:
        target_url = url_match.group(0)
        scraped_text, collected_sources = smart_scrape(
            target_url,
            keys_dict.get("firecrawl"),
            keys_dict.get("jina"),
        )
        external_context = "\n\n--- URL CONTENT ---\n" + scraped_text
    else:
        should_search = needs_web_search(prompt, keys_dict.get("groq"))
        if should_search:
            search_text, collected_sources = smart_search(
                prompt,
                keys_dict.get("serper"),
                keys_dict.get("tavily"),
                keys_dict.get("jina"),
            )
            if search_text:
                external_context = "\n\n--- LIVE WEB SEARCH RESULTS ---\n" + search_text

    router_info = select_model_by_task(prompt, file_context + external_context)
    managed_messages = st.session_state.messages

    system_prompt = (
        "You are Anis AI, a professional autonomous AI assistant.\n\n"
        "Rules:\n"
        "- Respond concisely and directly.\n"
        "- Reply in Bengali if user writes in Bengali.\n"
        "- Analyze attached context or files properly.\n"
    )

    ai_messages = [{"role": "system", "content": system_prompt}]
    for msg in managed_messages:
        ai_messages.append(msg)

    final_prompt = prompt + file_context + external_context
    ai_messages.append({"role": "user", "content": final_prompt})

    with chat_container:
        with st.chat_message("assistant"):
            response_placeholder = st.empty()
            full_response = ""
            has_error = False

            try:
                stream = provider_aware_ai_fallback(keys_dict, router_info, ai_messages)

                for chunk in stream:
                    if chunk == "ERROR_ALL_FAILED" or chunk.startswith("দুঃখিত"):
                        has_error = True
                        break

                    full_response += chunk
                    response_placeholder.markdown(full_response + "▌")

                if has_error or not full_response:
                    error_message = "দুঃখিত, টেকনিক্যাল সমস্যা হয়েছে। আবার চেষ্টা করুন।"
                    response_placeholder.markdown(error_message)
                    st.session_state.messages.append({"role": "assistant", "content": error_message})
                else:
                    if collected_sources:
                        full_response += "\n\n**Sources**\n"
                        for source in sorted(set(collected_sources)):
                            full_response += f"- {source}\n"

                    response_placeholder.markdown(full_response)
                    st.session_state.messages.append({"role": "assistant", "content": full_response})

            except Exception as e:
                error_message = "দুঃখিত, টেকনিক্যাল সমস্যা হয়েছে। আবার চেষ্টা করুন।"
                response_placeholder.markdown(error_message)
                st.session_state.messages.append({"role": "assistant", "content": error_message})

    if st.session_state.credits > 0:
        st.session_state.credits -= 1

    st.rerun()
