import streamlit as st
import re
import time
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
    page_title="Anis AI - Premium Business Suite",
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
    "message_input": "",
    "show_history": False,
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
# ULTRA-PREMIUM 3D GLASS UI STYLES
# =========================================================

st.markdown(
    """
<style>
/* ---------- Global & No-Scroll Layout ---------- */
html, body, [data-testid="stAppViewContainer"] {
    background: #08090d !important;
    color: #f4f4f5 !important;
    overflow: hidden !important;
    height: 100vh !important;
}

[data-testid="stHeader"] {
    background: transparent !important;
}

footer, [data-testid="collapsedControl"] {
    display: none !important;
}

.block-container {
    max-width: 1000px !important;
    height: 100vh !important;
    padding-top: 1rem !important;
    padding-bottom: 90px !important;
    margin: auto;
    display: flex;
    flex-direction: column;
}

/* ---------- 3D Floating Sphere Atmosphere ---------- */
[data-testid="stAppViewContainer"]::before,
[data-testid="stAppViewContainer"]::after {
    content: "";
    position: fixed;
    width: 300px;
    height: 300px;
    border-radius: 50%;
    pointer-events: none;
    filter: blur(90px);
    opacity: 0.18;
    z-index: 0;
    animation: anisFloat3D 12s ease-in-out infinite alternate;
}

[data-testid="stAppViewContainer"]::before {
    top: 5%;
    left: -50px;
    background: radial-gradient(circle, #6f8cff 0%, #3a55ff 100%);
}

[data-testid="stAppViewContainer"]::after {
    right: -50px;
    bottom: 5%;
    background: radial-gradient(circle, #a855f7 0%, #6366f1 100%);
    animation-delay: -6s;
}

@keyframes anisFloat3D {
    0% { transform: translate3d(0, 0, 0) scale(1) rotate(0deg); }
    50% { transform: translate3d(40px, -30px, 50px) scale(1.15) rotate(180deg); }
    100% { transform: translate3d(-20px, 20px, -30px) scale(0.95) rotate(360deg); }
}

/* ---------- Top bar ---------- */
.anis-topbar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 8px 16px;
    background: rgba(18, 20, 26, 0.65);
    backdrop-filter: blur(16px);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 16px;
    margin-bottom: 12px;
}

.anis-brand {
    display: flex;
    align-items: center;
    gap: 12px;
}

.anis-logo {
    width: 36px;
    height: 36px;
    border-radius: 10px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: linear-gradient(135deg, #6366f1, #a855f7);
    box-shadow: 0 4px 20px rgba(99, 102, 241, 0.35);
    font-size: 18px;
}

.anis-name {
    font-size: 17px;
    font-weight: 700;
    letter-spacing: -0.3px;
    color: #ffffff;
}

.anis-sub {
    font-size: 10px;
    color: #94a3b8;
}

.top-credit {
    color: #e2e8f0;
    font-size: 12px;
    padding: 5px 12px;
    border: 1px solid rgba(255, 255, 255, 0.12);
    border-radius: 999px;
    background: rgba(30, 32, 42, 0.7);
}

/* ---------- Welcome Container ---------- */
.welcome-wrap {
    text-align: center;
    padding: 40px 15px;
    margin: auto 0;
}

.welcome-orb {
    width: 64px;
    height: 64px;
    margin: 0 auto 16px;
    border-radius: 20px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 30px;
    background: linear-gradient(135deg, rgba(99, 102, 241, 0.25), rgba(168, 85, 247, 0.25));
    border: 1px solid rgba(255, 255, 255, 0.15);
    box-shadow: 0 12px 35px rgba(0, 0, 0, 0.45);
    animation: welcomeFloat 4s ease-in-out infinite;
}

@keyframes welcomeFloat {
    0%, 100% { transform: translateY(0); }
    50% { transform: translateY(-8px); }
}

.welcome-title {
    font-size: clamp(24px, 4vw, 36px);
    font-weight: 800;
    letter-spacing: -1px;
    margin: 0;
    background: linear-gradient(to right, #ffffff, #cbd5e1);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

.welcome-text {
    max-width: 550px;
    margin: 10px auto 0;
    color: #94a3b8;
    line-height: 1.5;
    font-size: 13px;
}

/* ---------- Chat Area Scroll Container ---------- */
[data-testid="stVerticalBlock"] > div:has(div.stChatMessage) {
    overflow-y: auto !important;
    max-height: calc(100vh - 210px) !important;
    padding-right: 6px;
}

.stChatMessage {
    background: transparent !important;
    border: 0 !important;
}

[data-testid="stChatMessageContent"] {
    border-radius: 16px;
    background: rgba(23, 25, 35, 0.65) !important;
    border: 1px solid rgba(255, 255, 255, 0.07) !important;
    backdrop-filter: blur(12px);
}

div[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) [data-testid="stChatMessageContent"] {
    background: linear-gradient(135deg, rgba(99, 102, 241, 0.2), rgba(168, 85, 247, 0.15)) !important;
    border: 1px solid rgba(99, 102, 241, 0.3) !important;
}

/* ---------- Fixed Composer ---------- */
.anis-composer {
    position: fixed;
    left: 50%;
    bottom: 12px;
    transform: translateX(-50%);
    width: min(960px, calc(100% - 20px));
    z-index: 999;
    padding: 8px 12px;
    border: 1px solid rgba(255, 255, 255, 0.12);
    border-radius: 20px;
    background: rgba(16, 18, 24, 0.85);
    box-shadow: 0 16px 40px rgba(0, 0, 0, 0.6);
    backdrop-filter: blur(20px);
}

div[data-testid="stTextArea"] textarea {
    background: transparent !important;
    color: #f8fafc !important;
    border: none !important;
    box-shadow: none !important;
    resize: none !important;
    font-size: 14px !important;
}

.attach-menu-box {
    position: fixed;
    left: 50%;
    bottom: 85px;
    transform: translateX(-50%);
    width: 280px;
    z-index: 1000;
    padding: 10px;
    border-radius: 16px;
    border: 1px solid rgba(255, 255, 255, 0.12);
    background: rgba(18, 20, 28, 0.95);
    backdrop-filter: blur(20px);
    box-shadow: 0 12px 30px rgba(0, 0, 0, 0.5);
}

div[data-testid="stTextArea"] label {
    display: none !important;
}
</style>
""",
    unsafe_allow_html=True,
)

# =========================================================
# TOP BAR
# =========================================================

top_left, top_mid, top_right = st.columns([3, 2, 2])

with top_left:
    st.markdown(
        """
        <div class="anis-topbar">
            <div class="anis-brand">
                <div class="anis-logo">✦</div>
                <div>
                    <div class="anis-name">Anis AI</div>
                    <div class="anis-sub">Enterprise Assistant</div>
                </div>
            </div>
            <span class="top-credit">✦ Credit: {}</span>
        </div>
        """.format(st.session_state.credits),
        unsafe_allow_html=True,
    )

with top_mid:
    if st.button("🕘 History", key="history_btn", use_container_width=True):
        st.session_state.show_history = not st.session_state.get("show_history", False)
        st.rerun()

with top_right:
    if st.button("🆕 New Chat", key="new_chat_btn", use_container_width=True):
        if st.session_state.messages:
            st.session_state.history.append(list(st.session_state.messages))
        st.session_state.messages = []
        st.session_state.chat_summary = ""
        st.session_state.selected_file = None
        st.session_state.show_history = False
        st.rerun()

# =========================================================
# HISTORY PANEL
# =========================================================

if st.session_state.get("show_history", False):
    st.markdown(
        """
        <div style="padding:10px 14px; margin:4px 0 12px; border:1px solid rgba(255,255,255,0.1); border-radius:14px; background:rgba(20,22,30,0.85);">
            <b>🕘 Conversation History</b>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if not st.session_state.history:
        st.caption("No previous chats stored.")
    else:
        for i, old_chat in enumerate(reversed(st.session_state.history[-10:])):
            title = "New Conversation"
            for msg in old_chat:
                if msg.get("role") == "user":
                    title = msg.get("content", "")[:50]
                    break

            if st.button(title, key=f"history_item_{i}", use_container_width=True):
                st.session_state.messages = old_chat
                st.session_state.show_history = False
                st.rerun()

# =========================================================
# WELCOME SCREEN
# =========================================================

if not st.session_state.messages:
    st.markdown(
        """
        <section class="welcome-wrap">
            <div class="welcome-orb">✦</div>
            <h1 class="welcome-title">How can Anis AI help you today?</h1>
            <p class="welcome-text">
                সহজে প্রশ্ন করুন, কোড সমাধান করুন অথবা যেকোনো ফাইল প্রসেস করুন।
            </p>
        </section>
        """,
        unsafe_allow_html=True,
    )

# =========================================================
# CHAT MESSAGES DISPLAY
# =========================================================

for idx, message in enumerate(st.session_state.messages):
    role = message["role"]
    content = message["content"]

    with st.chat_message(role):
        st.markdown(content)

    if role == "assistant":
        a1, a2, a3, a4, _ = st.columns([1, 1, 1, 1, 8])

        with a1:
            if st.button("📋", key=f"copy_{idx}", help="Copy response"):
                st.code(content, language=None)

        with a2:
            st.button("👍", key=f"like_{idx}", help="Like")

        with a3:
            st.button("👎", key=f"dislike_{idx}", help="Dislike")

        with a4:
            st.button("↗", key=f"share_{idx}", help="Share")

# =========================================================
# ATTACHMENT MODAL & PREVIEW
# =========================================================

if st.session_state.attach_mode == "camera":
    cam = st.camera_input("Take Picture")
    if cam is not None:
        st.session_state.selected_file = cam
        st.session_state.attach_mode = None
        st.rerun()

elif st.session_state.attach_mode == "gallery":
    gallery_file = st.file_uploader(
        "Upload Image",
        type=["jpg", "jpeg", "png", "webp"],
        key="gallery_uploader",
    )
    if gallery_file is not None:
        st.session_state.selected_file = gallery_file
        st.session_state.attach_mode = None
        st.rerun()

elif st.session_state.attach_mode == "file":
    doc_file = st.file_uploader(
        "Upload Document",
        type=None,
        key="doc_uploader",
    )
    if doc_file is not None:
        st.session_state.selected_file = doc_file
        st.session_state.attach_mode = None
        st.rerun()

if st.session_state.selected_file is not None:
    sel = st.session_state.selected_file
    file_name = getattr(sel, "name", "Attached File")
    st.info(f"📎 Attached: {html.escape(file_name)}")

if st.session_state.show_attach_menu:
    st.markdown("<div class='attach-menu-box'>", unsafe_allow_html=True)
    m1, m2, m3 = st.columns(3)

    with m1:
        if st.button("📷 Cam", key="btn_cam", use_container_width=True):
            st.session_state.attach_mode = "camera"
            st.session_state.show_attach_menu = False
            st.rerun()

    with m2:
        if st.button("🖼️ Img", key="btn_gal", use_container_width=True):
            st.session_state.attach_mode = "gallery"
            st.session_state.show_attach_menu = False
            st.rerun()

    with m3:
        if st.button("📁 File", key="btn_file", use_container_width=True):
            st.session_state.attach_mode = "file"
            st.session_state.show_attach_menu = False
            st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)

# =========================================================
# FIXED COMPOSER (TEXT INPUT & BUTTONS)
# =========================================================

st.markdown("<div class='anis-composer'>", unsafe_allow_html=True)

user_text = st.text_area(
    "Message",
    key="message_input",
    height=45,
    placeholder="Ask Anis AI anything...",
    label_visibility="collapsed",
)

col_left, col_mid, col_right = st.columns([1, 8, 1])

with col_left:
    if st.button("＋", key="plus_btn_nav", help="Attach items", use_container_width=True):
        st.session_state.show_attach_menu = not st.session_state.show_attach_menu
        st.rerun()

with col_mid:
    st.empty()

with col_right:
    submitted = st.button("➤", key="send_btn_nav", help="Send Message", use_container_width=True)

st.markdown("</div>", unsafe_allow_html=True)

# =========================================================
# BACKEND EXECUTION LOGIC (FULLY PRESERVED & FIXED)
# =========================================================

if submitted and user_text and user_text.strip():
    prompt = user_text.strip()

    st.session_state.messages.append(
        {"role": "user", "content": prompt}
    )

    collected_sources = []
    file_context = ""
    external_context = ""
    scraped_text = ""
    search_text = ""

    # File Read Section
    if st.session_state.selected_file is not None:
        try:
            file_context = smart_read_file(
                st.session_state.selected_file,
                ocr_api_key,
            )
            if file_context:
                file_context = (
                    "\n\n--- ATTACHED FILE CONTENT ---\n"
                    + file_context
                )
        except Exception as e:
            print("File read error:", e)

        st.session_state.selected_file = None

    # Syntax Safe URL & Search Handling
    url_match = re.search(r"https?://[^\s]+", prompt)

    if url_match:
        target_url = url_match.group(0)
        scraped_text, collected_sources = smart_scrape(
            target_url,
            keys_dict.get("firecrawl"),
            keys_dict.get("jina"),
        )
        external_context = (
            "\n\n--- URL CONTENT ---\n"
            + scraped_text
        )
    else:
        should_search = needs_web_search(
            prompt,
            keys_dict.get("groq"),
        )
        if should_search:
            search_text, collected_sources = smart_search(
                prompt,
                keys_dict.get("serper"),
                keys_dict.get("tavily"),
                keys_dict.get("jina"),
            )
            if search_text:
                external_context = (
                    "\n\n--- LIVE WEB SEARCH RESULTS ---\n"
                    + search_text
                )

    # Model Routing
    router_info = select_model_by_task(
        prompt,
        file_context + external_context,
    )

    # Memory Management
    managed_messages = st.session_state.messages
    st.session_state.chat_summary = ""

    # System Instructions
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

    ai_messages = [{"role": "system", "content": system_prompt}]
    for msg in managed_messages:
        ai_messages.append(msg)

    final_prompt = prompt + file_context + external_context
    ai_messages.append({"role": "user", "content": final_prompt})

    # Response Stream Generation
    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        full_response = ""
        has_error = False

        try:
            response_placeholder.markdown("🧠 Processing...")

            stream = provider_aware_ai_fallback(
                keys_dict,
                router_info,
                ai_messages,
            )

            for chunk in stream:
                if chunk == "ERROR_ALL_FAILED" or chunk.startswith("দুঃখিত"):
                    has_error = True
                    break

                full_response += chunk
                response_placeholder.markdown(full_response + "▌")

            if has_error or not full_response:
                error_message = (
                    "দুঃখিত, কিছুক্ষণ অপেক্ষা করুন। "
                    "টেকনিক্যাল সমস্যা হয়েছে, ঠিক করা হচ্ছে।"
                )
                response_placeholder.markdown(error_message)
                st.session_state.messages.append(
                    {"role": "assistant", "content": error_message}
                )
            else:
                if collected_sources:
                    full_response += "\n\n**Sources**\n"
                    for source in sorted(set(collected_sources)):
                        full_response += f"- {source}\n"

                response_placeholder.markdown(full_response)
                st.session_state.messages.append(
                    {"role": "assistant", "content": full_response}
                )

        except Exception as e:
            print("AI response error:", e)
            error_message = (
                "দুঃখিত, কিছুক্ষণ অপেক্ষা করুন। "
                "টেকনিক্যাল সমস্যা হয়েছে, ঠিক করা হচ্ছে।"
            )
            response_placeholder.markdown(error_message)
            st.session_state.messages.append(
                {"role": "assistant", "content": error_message}
            )

    if st.session_state.credits > 0:
        st.session_state.credits -= 1

    st.session_state.message_input = ""
    st.rerun()
