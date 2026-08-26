import streamlit as st
import re
import html
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
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="Anis AI",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="expanded",
)


# =========================================================
# CONSTANTS
# =========================================================

HISTORY_DAYS = 5
MAX_HISTORY_ITEMS = 50


# =========================================================
# SESSION STATE
# =========================================================

defaults = {
    "messages": [],
    "history": [],
    "chat_summary": "",
    "show_attach_menu": False,
    "attach_mode": None,
    "selected_file": None,
    "credits": 100,
    "analytics_logged": False,
    "processing": False,
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


# =========================================================
# USER ID + ANALYTICS
# =========================================================

if not st.session_state.analytics_logged:

    user_id = st.session_state.get("user_id")

    if not user_id:
        user_id = f"user_{id(st.session_state)}"
        st.session_state.user_id = user_id

    try:
        log_usage(
            user_id,
            event_type="visit"
        )
    except Exception:
        pass

    st.session_state.analytics_logged = True


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
# 5-DAY HISTORY CLEANUP
# =========================================================

def cleanup_old_history():

    cutoff = datetime.now() - timedelta(days=HISTORY_DAYS)

    cleaned_history = []

    for chat in st.session_state.history:

        try:
            created_at = chat.get("created_at")

            if isinstance(created_at, str):
                created_at = datetime.fromisoformat(created_at)

            if created_at and created_at >= cutoff:
                cleaned_history.append(chat)

        except Exception:
            continue

    st.session_state.history = cleaned_history[-MAX_HISTORY_ITEMS:]


cleanup_old_history()


# =========================================================
# SAVE CURRENT CHAT
# =========================================================

def save_current_chat():

    if not st.session_state.messages:
        return

    first_user_message = "New Conversation"

    for message in st.session_state.messages:

        if message.get("role") == "user":

            content = message.get("content", "").strip()

            if content:
                first_user_message = content[:45]
                break

    chat_record = {
        "id": datetime.now().timestamp(),
        "created_at": datetime.now().isoformat(),
        "title": first_user_message,
        "messages": list(st.session_state.messages),
    }

    st.session_state.history.append(chat_record)

    st.session_state.history = (
        st.session_state.history[-MAX_HISTORY_ITEMS:]
    )


# =========================================================
# NEW CHAT
# =========================================================

def start_new_chat():

    if st.session_state.messages:
        save_current_chat()

    st.session_state.messages = []
    st.session_state.chat_summary = ""
    st.session_state.selected_file = None
    st.session_state.attach_mode = None
    st.session_state.show_attach_menu = False
    st.session_state.processing = False

    st.rerun()


# =========================================================
# LOAD CHAT
# =========================================================

def load_chat(chat):

    st.session_state.messages = list(
        chat.get("messages", [])
    )

    st.session_state.chat_summary = ""
    st.session_state.selected_file = None
    st.session_state.attach_mode = None
    st.session_state.show_attach_menu = False

    st.rerun()


# =========================================================
# PROFESSIONAL DARK UI
# =========================================================

st.markdown(
    """
    <style>

    /* ==============================================
       GLOBAL
       ============================================== */

    #MainMenu {
        visibility: hidden;
    }

    footer {
        visibility: hidden;
    }

    header {
        visibility: hidden;
    }

    .stApp {
        background:
            radial-gradient(
                circle at 15% 5%,
                rgba(76, 141, 246, 0.08),
                transparent 28%
            ),
            radial-gradient(
                circle at 85% 10%,
                rgba(120, 90, 255, 0.07),
                transparent 28%
            ),
            #131314;

        color: #e8eaed;
    }


    /* ==============================================
       MAIN CONTAINER
       ============================================== */

    .block-container {
        max-width: 1050px;
        padding-top: 1rem;
        padding-bottom: 7rem;
    }


    /* ==============================================
       TOP BAR
       ============================================== */

    .anis-navbar {
        height: 58px;

        display: flex;
        align-items: center;
        justify-content: space-between;

        padding: 0 4px;

        margin-bottom: 20px;

        border-bottom: 1px solid #292a2d;
    }


    .anis-brand {
        display: flex;
        align-items: center;
        gap: 9px;

        font-size: 21px;
        font-weight: 700;

        color: #f1f3f4;

        letter-spacing: -0.4px;
    }


    .anis-logo {
        width: 31px;
        height: 31px;

        display: flex;
        align-items: center;
        justify-content: center;

        border-radius: 10px;

        background:
            linear-gradient(
                135deg,
                #477df5,
                #7658e8
            );

        color: white;

        font-size: 17px;

        box-shadow:
            0 6px 22px
            rgba(76, 100, 240, 0.25);
    }


    /* ==============================================
       WELCOME
       ============================================== */

    .welcome-wrapper {

        min-height: 55vh;

        display: flex;

        flex-direction: column;

        align-items: center;

        justify-content: center;

        text-align: center;
    }


    .welcome-icon {

        width: 68px;
        height: 68px;

        display: flex;

        align-items: center;
        justify-content: center;

        border-radius: 20px;

        background:
            linear-gradient(
                135deg,
                rgba(76, 141, 246, 0.18),
                rgba(120, 90, 255, 0.16)
            );

        border: 1px solid
            rgba(255,255,255,0.06);

        font-size: 30px;

        margin-bottom: 22px;
    }


    .welcome-title {

        font-size: 34px;

        font-weight: 650;

        color: #f1f3f4;

        letter-spacing: -0.8px;

        margin-bottom: 8px;
    }


    .welcome-subtitle {

        max-width: 600px;

        font-size: 15px;

        line-height: 1.6;

        color: #9aa0a6;
    }


    /* ==============================================
       CHAT
       ============================================== */

    [data-testid="stChatMessage"] {

        padding-top: 8px;
        padding-bottom: 8px;

        margin-bottom: 8px;
    }


    [data-testid="stChatMessageContent"] {

        font-size: 15px;

        line-height: 1.7;

        color: #e4e6eb;
    }


    /* ==============================================
       BUTTONS
       ============================================== */

    .stButton > button {

        border-radius: 12px;

        border: 1px solid #303134;

        background: #1b1c1f;

        color: #e8eaed;

        transition: all 0.2s ease;
    }


    .stButton > button:hover {

        border-color: #5f6368;

        background: #232428;

        transform: translateY(-1px);
    }


    /* ==============================================
       CHAT INPUT
       ============================================== */

    [data-testid="stChatInput"] {

        border-radius: 18px;
    }


    [data-testid="stChatInput"] textarea {

        background: #1e1f22 !important;

        border: 1px solid #34363a !important;

        border-radius: 18px !important;

        color: #f1f3f4 !important;

        padding: 16px !important;
    }


    [data-testid="stChatInput"] textarea:focus {

        border-color: #5f8ff7 !important;

        box-shadow:
            0 0 0 1px
            rgba(95,143,247,0.25) !important;
    }


    /* ==============================================
       SIDEBAR
       ============================================== */

    section[data-testid="stSidebar"] {

        background: #17181a;

        border-right: 1px solid #292a2d;
    }


    section[data-testid="stSidebar"]
    .block-container {

        padding-top: 1.3rem;
    }


    /* ==============================================
       HISTORY ITEM
       ============================================== */

    .history-label {

        font-size: 11px;

        font-weight: 600;

        text-transform: uppercase;

        letter-spacing: 0.7px;

        color: #777b82;

        margin-top: 18px;

        margin-bottom: 7px;
    }


    /* ==============================================
       ATTACHMENT
       ============================================== */

    .attachment-card {

        background: #1b1c1f;

        border: 1px solid #303134;

        border-radius: 14px;

        padding: 12px 15px;

        margin: 10px 0;

        color: #c9cdd2;
    }


    /* ==============================================
       CREDIT BADGE
       ============================================== */

    .credit-badge {

        display: inline-block;

        padding: 6px 10px;

        border-radius: 10px;

        background: rgba(76,141,246,0.10);

        border: 1px solid
            rgba(76,141,246,0.20);

        color: #9bbcff;

        font-size: 12px;
    }


    /* ==============================================
       MOBILE
       ============================================== */

    @media (max-width: 768px) {

        .block-container {

            padding-left: 12px;
            padding-right: 12px;
        }

        .welcome-title {

            font-size: 27px;
        }

        .welcome-subtitle {

            font-size: 14px;
        }

        .anis-brand {

            font-size: 19px;
        }
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# TOP NAVBAR
# =========================================================

nav_left, nav_right = st.columns([7, 3])


with nav_left:

    st.markdown(
        """
        <div class="anis-navbar">

            <div class="anis-brand">

                <div class="anis-logo">
                    ✦
                </div>

                Anis AI

            </div>

        </div>
        """,
        unsafe_allow_html=True,
    )


with nav_right:

    if st.button(
        "＋ New Chat",
        key="top_new_chat",
        use_container_width=True,
    ):

        start_new_chat()


# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:

    st.markdown(
        """
        <div class="anis-brand">
            <div class="anis-logo">✦</div>
            Anis AI
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.write("")

    if st.button(
        "＋  New Chat",
        key="sidebar_new_chat",
        use_container_width=True,
    ):

        start_new_chat()


    st.markdown("---")


    # Credits

    st.markdown(
        f"""
        <div class="credit-badge">
            ✦ {st.session_state.credits} credits
        </div>
        """,
        unsafe_allow_html=True,
    )


    st.markdown(
        '<div class="history-label">Recent Chats</div>',
        unsafe_allow_html=True,
    )


    if not st.session_state.history:

        st.caption(
            "Your last 5 days of chats will appear here."
        )

    else:

        for chat in reversed(
            st.session_state.history
        ):

            title = chat.get(
                "title",
                "Conversation"
            )

            if st.button(
                f"💬 {title}",
                key=f"history_{chat.get('id')}",
                use_container_width=True,
            ):

                load_chat(chat)


# =========================================================
# WELCOME SCREEN
# =========================================================

if not st.session_state.messages:

    st.markdown(
        """
        <div class="welcome-wrapper">

            <div class="welcome-icon">
                ✦
            </div>

            <div class="welcome-title">
                Hi Anis, how can I help?
            </div>

            <div class="welcome-subtitle">
                Ask questions, analyze files,
                search the web, or explore ideas
                with Anis AI.
            </div>

        </div>
        """,
        unsafe_allow_html=True,
    )


# =========================================================
# CHAT DISPLAY
# =========================================================

for message in st.session_state.messages:

    role = message.get("role")

    content = message.get(
        "content",
        ""
    )

    if role in ["user", "assistant"]:

        with st.chat_message(role):

            st.markdown(content)
