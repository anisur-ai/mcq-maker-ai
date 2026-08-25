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
    page_title="Anis AI - Personal AI Assistant & Study Partner",
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
# PREMIUM DARK / GLASS UI
# =========================================================

st.markdown(
    """
<style>
/* ---------- Global ---------- */
html, body, [data-testid="stAppViewContainer"] {
    background:
        radial-gradient(circle at 15% 15%, rgba(80, 120, 255, .08), transparent 28%),
        radial-gradient(circle at 85% 25%, rgba(170, 80, 255, .07), transparent 30%),
        radial-gradient(circle at 50% 90%, rgba(0, 210, 190, .05), transparent 28%),
        #08090b !important;
    color: #f4f4f5 !important;
}

[data-testid="stHeader"] {
    background: transparent !important;
}

footer {
    visibility: hidden;
}

[data-testid="collapsedControl"] {
    display: none;
}

.block-container {
    max-width: 920px;
    padding-top: 1rem !important;
    padding-bottom: 190px !important;
    margin: auto;
}

/* ---------- Very subtle 3D atmosphere ---------- */
[data-testid="stAppViewContainer"]::before,
[data-testid="stAppViewContainer"]::after {
    content: "";
    position: fixed;
    width: 220px;
    height: 220px;
    border-radius: 50%;
    pointer-events: none;
    filter: blur(60px);
    opacity: .13;
    z-index: 0;
    animation: anisFloat 14s ease-in-out infinite alternate;
}

[data-testid="stAppViewContainer"]::before {
    top: 12%;
    left: -80px;
    background: #4f7cff;
}

[data-testid="stAppViewContainer"]::after {
    right: -80px;
    bottom: 12%;
    background: #9b5cff;
    animation-delay: -6s;
}

@keyframes anisFloat {
    from { transform: translate3d(0, 0, 0) scale(1); }
    to   { transform: translate3d(25px, -18px, 0) scale(1.08); }
}

/* ---------- Top bar ---------- */
.anis-topbar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    margin-bottom: 18px;
}

.anis-brand {
    display: flex;
    align-items: center;
    gap: 10px;
}

.anis-logo {
    width: 38px;
    height: 38px;
    border-radius: 13px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: linear-gradient(135deg, #6f8cff, #9b5cff);
    box-shadow: 0 8px 25px rgba(111,140,255,.22);
    font-size: 20px;
}

.anis-name {
    font-size: 19px;
    font-weight: 700;
    letter-spacing: -.3px;
}

.anis-sub {
    font-size: 11px;
    color: #888b94;
    margin-top: 1px;
}

.top-credit {
    color: #bfc3cc;
    font-size: 12px;
    padding: 7px 10px;
    border: 1px solid #292c33;
    border-radius: 999px;
    background: rgba(24,25,29,.65);
}

/* ---------- Welcome ---------- */
.welcome-wrap {
    text-align: center;
    padding: 12vh 10px 30px;
    position: relative;
    z-index: 1;
}

.welcome-orb {
    width: 72px;
    height: 72px;
    margin: 0 auto 22px;
    border-radius: 24px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 34px;
    background: linear-gradient(135deg, rgba(111,140,255,.22), rgba(155,92,255,.16));
    border: 1px solid rgba(255,255,255,.09);
    box-shadow:
        inset 0 1px 0 rgba(255,255,255,.08),
        0 18px 55px rgba(0,0,0,.28);
    animation: welcomeFloat 5s ease-in-out infinite;
}

@keyframes welcomeFloat {
    50% { transform: translateY(-5px); }
}

.welcome-title {
    font-size: clamp(30px, 6vw, 48px);
    font-weight: 750;
    letter-spacing: -1.5px;
    margin: 0;
}

.welcome-text {
    max-width: 620px;
    margin: 12px auto 0;
    color: #9ea2ad;
    line-height: 1.65;
    font-size: 14px;
}

.suggestion-grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 10px;
    max-width: 720px;
    margin: 28px auto 0;
}

.suggestion {
    padding: 13px 14px;
    text-align: left;
    border: 1px solid #292c33;
    background: rgba(20,21,25,.55);
    border-radius: 16px;
    color: #d7d9df;
    font-size: 13px;
    backdrop-filter: blur(12px);
}

/* ---------- Chat ---------- */
.stChatMessage {
    background: transparent !important;
    border: 0 !important;
    position: relative;
    z-index: 1;
}

[data-testid="stChatMessageContent"] {
    border-radius: 18px;
}

div[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) {
    background: rgba(30,32,38,.72) !important;
    border: 1px solid #292c33 !important;
    border-radius: 18px !important;
    padding: 8px 12px !important;
    margin: 8px 0 !important;
}

/* ---------- Assistant actions ---------- */
.assistant-actions {
    display: flex;
    gap: 4px;
    margin: -4px 0 15px 48px;
    position: relative;
    z-index: 2;
}

.assistant-actions button {
    border: none !important;
    background: transparent !important;
    color: #777b86 !important;
    min-width: 32px !important;
    width: 32px !important;
    height: 30px !important;
    padding: 0 !important;
    border-radius: 9px !important;
    font-size: 14px !important;
}

.assistant-actions button:hover {
    background: #1d1f24 !important;
    color: #e7e8eb !important;
}

/* ---------- Fixed composer ---------- */
.anis-composer {
    position: fixed;
    left: 50%;
    bottom: 16px;
    transform: translateX(-50%);
    width: min(900px, calc(100% - 24px));
    z-index: 999;
    padding: 10px;
    border: 1px solid rgba(255,255,255,.10);
    border-radius: 25px;
    background: rgba(24,25,29,.88);
    box-shadow:
        0 18px 55px rgba(0,0,0,.45),
        inset 0 1px 0 rgba(255,255,255,.05);
    backdrop-filter: blur(22px);
    -webkit-backdrop-filter: blur(22px);
}

div[data-testid="stTextArea"] textarea {
    background: transparent !important;
    color: #f4f4f5 !important;
    border: none !important;
    box-shadow: none !important;
    resize: none !important;
    font-size: 15px !important;
}

div[data-testid="stTextArea"] textarea::placeholder {
    color: #777b85 !important;
}

.anis-composer button {
    border-radius: 50% !important;
    border: 1px solid #30333b !important;
    background: #202228 !important;
    color: #f5f5f5 !important;
    min-width: 40px !important;
    width: 40px !important;
    height: 40px !important;
    padding: 0 !important;
}

.anis-composer button:hover {
    background: #2b2e36 !important;
    transform: translateY(-1px);
}

.anis-send button {
    background: linear-gradient(135deg, #6f8cff, #8b65ff) !important;
    border: none !important;
    box-shadow: 0 7px 20px rgba(111,140,255,.25);
    animation: sendPulse 2.8s ease-in-out infinite;
}

@keyframes sendPulse {
    50% { box-shadow: 0 7px 28px rgba(111,140,255,.40); }
}

/* ---------- Attachment preview ---------- */
.attachment-preview {
    display: flex;
    align-items: center;
    gap: 9px;
    padding: 7px 9px;
    margin: 2px 3px 7px;
    border: 1px solid #30333b;
    border-radius: 12px;
    background: rgba(255,255,255,.035);
    color: #c9ccd3;
    font-size: 12px;
}

/* ---------- Attachment menu ---------- */
.attach-menu-box {
    position: fixed;
    left: 50%;
    bottom: 112px;
    transform: translateX(calc(-50% - 320px));
    width: 235px;
    z-index: 1000;
    padding: 8px;
    border-radius: 16px;
    border: 1px solid #30333b;
    background: rgba(28,29,34,.96);
    box-shadow: 0 16px 40px rgba(0,0,0,.45);
    backdrop-filter: blur(18px);
}

.attach-menu-box button {
    width: 100% !important;
    height: 40px !important;
    border-radius: 10px !important;
    border: none !important;
    background: transparent !important;
    text-align: left !important;
}

.attach-menu-box button:hover {
    background: #25272d !important;
}

/* ---------- Hide Streamlit labels ---------- */
div[data-testid="stTextArea"] label {
    display: none !important;
}

/* ---------- Mobile ---------- */
@media (max-width: 700px) {
    .block-container {
        padding-top: .6rem !important;
        padding-bottom: 180px !important;
        width: 100% !important;
    }

    .anis-composer {
        bottom: 9px;
        width: calc(100% - 14px);
        border-radius: 22px;
        padding: 8px;
    }

    .welcome-wrap {
        padding-top: 9vh;
    }

    .suggestion-grid {
        grid-template-columns: 1fr;
        max-width: 100%;
    }

    .assistant-actions {
        margin-left: 42px;
    }

    .attach-menu-box {
        left: 12px;
        bottom: 105px;
        transform: none;
        width: calc(100% - 24px);
    }

    .anis-name {
        font-size: 17px;
    }
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
                    <div class="anis-sub">Personal AI Assistant</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with top_mid:
    if st.button("🕘 History", key="history_btn"):
        st.session_state.show_history = not st.session_state.get("show_history", False)
        st.rerun()

with top_right:
    if st.button("🆕 New Chat", key="new_chat_btn"):
        if st.session_state.messages:
            st.session_state.history.append(list(st.session_state.messages))
        st.session_state.messages = []
        st.session_state.chat_summary = ""
        st.session_state.selected_file = None
        st.session_state.show_history = False
        st.rerun()

# Small credit/value indicator beside the top controls.
st.markdown(
    f"""
    <div style="text-align:right; margin-top:-12px; margin-bottom:8px;">
        <span class="top-credit">✦ {st.session_state.credits}</span>
    </div>
    """,
    unsafe_allow_html=True,
)

# =========================================================
# HISTORY PANEL
# =========================================================

if st.session_state.get("show_history", False):
    st.markdown(
        """
        <div style="
            padding:14px;
            margin:8px 0 18px;
            border:1px solid #292c33;
            border-radius:16px;
            background:rgba(20,21,25,.72);
        ">
            <b>🕘 Chat History</b>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if not st.session_state.history:
        st.caption("No previous chats yet.")
    else:
        for i, old_chat in enumerate(reversed(st.session_state.history[-10:])):
            title = "New conversation"
            for msg in old_chat:
                if msg.get("role") == "user":
                    title = msg.get("content", "")[:55]
                    break

            if st.button(title, key=f"history_item_{i}"):
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
            <h1 class="welcome-title">Hello, I'm Anis AI</h1>
            <p class="welcome-text">
                আপনার বুদ্ধিমান AI সহকারী। প্রশ্ন করুন, লিখুন, ছবি বা ফাইল দিন—
                Anis AI আপনার কাজ, পড়াশোনা ও দৈনন্দিন প্রশ্নে সহজ এবং পরিষ্কারভাবে সাহায্য করবে।
            </p>

            <div class="suggestion-grid">
                <div class="suggestion">💡 একটি কঠিন বিষয় সহজ ভাষায় বুঝিয়ে দাও</div>
                <div class="suggestion">📝 আমার জন্য একটি সুন্দর লেখা তৈরি করো</div>
                <div class="suggestion">📚 এই বিষয়টি পরীক্ষার জন্য বুঝিয়ে দাও</div>
                <div class="suggestion">🔎 এই প্রশ্নের সঠিক উত্তর খুঁজে দাও</div>
            </div>
        </section>
        """,
        unsafe_allow_html=True,
    )

# =========================================================
# SHOW CHAT
# =========================================================

for idx, message in enumerate(st.session_state.messages):
    role = message["role"]
    content = message["content"]

    with st.chat_message(role):
        st.markdown(content)

    if role == "assistant":
        # Native Streamlit buttons provide the actions without changing helper.py.
        a1, a2, a3, a4, a5, a6, _ = st.columns([1, 1, 1, 1, 1, 1, 7])

        with a1:
            if st.button("📋", key=f"copy_{idx}", help="Copy"):
                st.code(content, language=None)

        with a2:
            st.button("👍", key=f"like_{idx}", help="Like")

        with a3:
            st.button("👎", key=f"dislike_{idx}", help="Dislike")

        with a4:
            if st.button("🔊", key=f"read_{idx}", help="Read aloud"):
                st.info("Read-aloud UI is ready; a voice service can be connected later.")

        with a5:
            st.button("↗", key=f"share_{idx}", help="Share")

        with a6:
            st.button("⋮", key=f"more_{idx}", help="More")

# =========================================================
# ATTACHMENT INPUT
# =========================================================

if st.session_state.attach_mode == "camera":
    cam = st.camera_input("Capture an image")
    if cam is not None:
        st.session_state.selected_file = cam
        st.session_state.attach_mode = None
        st.rerun()

elif st.session_state.attach_mode == "gallery":
    gallery_file = st.file_uploader(
        "Select an image",
        type=["jpg", "jpeg", "png", "webp"],
        key="gallery_uploader",
    )
    if gallery_file is not None:
        st.session_state.selected_file = gallery_file
        st.session_state.attach_mode = None
        st.rerun()

elif st.session_state.attach_mode == "file":
    doc_file = st.file_uploader(
        "Select a document or file",
        type=None,
        key="doc_uploader",
    )
    if doc_file is not None:
        st.session_state.selected_file = doc_file
        st.session_state.attach_mode = None
        st.rerun()

# =========================================================
# ATTACHMENT PREVIEW
# =========================================================

if st.session_state.selected_file is not None:
    sel = st.session_state.selected_file
    file_name = getattr(sel, "name", "Attached file")

    st.markdown(
        f"""
        <div class="attachment-preview">
            <span>📎</span>
            <span>{html.escape(file_name)}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

# =========================================================
# ATTACHMENT MENU
# =========================================================

if st.session_state.show_attach_menu:
    st.markdown("<div class='attach-menu-box'>", unsafe_allow_html=True)

    m1, m2, m3 = st.columns(3)

    with m1:
        if st.button("📷 Camera", key="btn_cam"):
            st.session_state.attach_mode = "camera"
            st.session_state.show_attach_menu = False
            st.rerun()

    with m2:
        if st.button("🖼️ Image", key="btn_gal"):
            st.session_state.attach_mode = "gallery"
            st.session_state.show_attach_menu = False
            st.rerun()

    with m3:
        if st.button("📁 File", key="btn_file"):
            st.session_state.attach_mode = "file"
            st.session_state.show_attach_menu = False
            st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)

# =========================================================
# FIXED CHAT COMPOSER
# =========================================================

st.markdown("<div class='anis-composer'>", unsafe_allow_html=True)

user_text = st.text_area(
    "Ask Anis AI",
    key="message_input",
    height=58,
    placeholder="Ask Anis AI...",
    label_visibility="collapsed",
)

col_left, col_mid, col_right = st.columns([1, 8, 1])

with col_left:
    if st.button("＋", key="plus_btn_nav", help="Attach image or file"):
        st.session_state.show_attach_menu = not st.session_state.show_attach_menu
        st.rerun()

with col_mid:
    st.caption("")

with col_right:
    submitted = st.button("➤", key="send_btn_nav", help="Send")

st.markdown("</div>", unsafe_allow_html=True)

# =========================================================
# HANDLE SEND
# =========================================================

if submitted and user_text and user_text.strip():
    prompt = user_text.strip()

    st.session_state.messages.append(
        {"role": "user", "content": prompt}
    )

    collected_sources = []
    file_context = ""
    external_context = ""

    # -----------------------------------------------------
    # Read attached file without changing helpers.py
    # -----------------------------------------------------
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

    # -----------------------------------------------------
    # URL detection
    # -----------------------------------------------------
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

    # -----------------------------------------------------
    # Model router
    # -----------------------------------------------------
    router_info = select_model_by_task(
        prompt,
        file_context + external_context,
    )

    # -----------------------------------------------------
    # Conversation memory
    # -----------------------------------------------------
    managed_messages = st.session_state.messages
    st.session_state.chat_summary = ""

    # -----------------------------------------------------
    # System prompt
    # -----------------------------------------------------
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

    ai_messages.append(
        {"role": "user", "content": final_prompt}
    )

    # -----------------------------------------------------
    # Assistant response
    # -----------------------------------------------------
    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        full_response = ""
        has_error = False

        try:
            # Small loading state before streaming starts.
            response_placeholder.markdown("🧠 Anis AI is thinking…")

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
                    "দুঃখিত, কিছুক্ষণ অপেক্ষা করুন। "
                    "টেকনিক্যাল সমস্যা হয়েছে, ঠিক করা হচ্ছে।"
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

        except Exception as e:
            print("AI response error:", e)

            error_message = (
                "দুঃখিত, কিছুক্ষণ অপেক্ষা করুন। "
                "টেকনিক্যাল সমস্যা হয়েছে, ঠিক করা হচ্ছে।"
            )

            response_placeholder.markdown(error_message)

            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": error_message,
                }
            )

    # Simple usage counter. Replace with your real billing/credit
    # system later if you already have one in helpers.py.
    if st.session_state.credits > 0:
        st.session_state.credits -= 1

    # Clear input after send.
    st.session_state.message_input = ""
    st.rerun()


