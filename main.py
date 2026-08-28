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
    create_chat_title,
    cleanup_old_history,
    MAX_HISTORY_CHATS,
)


# =========================================================
# PAGE CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="Anis AI",
    page_icon="✦",
    layout="centered",
    initial_sidebar_state="collapsed",
)


# =========================================================
# SESSION STATE INITIALIZATION
# =========================================================

if "messages" not in st.session_state:
    st.session_state.messages = []

if "history" not in st.session_state:
    st.session_state.history = []

if "chat_summary" not in st.session_state:
    st.session_state.chat_summary = ""

if "selected_file" not in st.session_state:
    st.session_state.selected_file = None

if "attach_mode" not in st.session_state:
    st.session_state.attach_mode = None

if "show_attach_menu" not in st.session_state:
    st.session_state.show_attach_menu = False

if "processing" not in st.session_state:
    st.session_state.processing = False

if "active_mode" not in st.session_state:
    st.session_state.active_mode = None

if "attached_image" not in st.session_state:
    st.session_state.attached_image = None

if "pending_user_message" not in st.session_state:
    st.session_state.pending_user_message = None

if "account_email" not in st.session_state:
    st.session_state.account_email = None


# =========================================================
# ANIS AI — MOBILE APP STYLE (CSS)
# =========================================================

st.markdown(
    """
    <style>
    html, body, [data-testid="stAppViewContainer"] {
        background: #000000 !important;
        color: #ffffff !important;
    }
    [data-testid="stAppViewContainer"] {
        max-width: 100vw !important;
        min-height: 100dvh !important;
        overflow-x: hidden !important;
    }
    [data-testid="stAppViewBlockContainer"] {
        max-width: 700px !important;
        padding-left: 12px !important;
        padding-right: 12px !important;
        padding-top: 8px !important;
        padding-bottom: 110px !important;
        margin: 0 auto !important;
    }
    header[data-testid="stHeader"] {
        background: transparent !important;
    }
    #MainMenu, footer {
        visibility: hidden;
    }

    /* মোবাইল হেডার এবং কার্ড ডিজাইন */
    .anis-header {
        width: 100%;
        height: 54px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 0 4px;
        margin-bottom: 8px;
    }
    .anis-brand {
        font-size: 20px;
        font-weight: 600;
        color: #ffffff;
        letter-spacing: -0.3px;
    }
    .anis-profile {
        width: 34px;
        height: 34px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        background: #303030;
        color: #ffffff;
        font-size: 15px;
        font-weight: 600;
    }
    .user-msg {
        background: #303030;
        color: #ffffff;
        padding: 12px 16px;
        border-radius: 20px 20px 5px 20px;
        margin: 10px 0;
        max-width: 82%;
        margin-left: auto;
        font-size: 15px;
        line-height: 1.5;
    }
    .ai-msg {
        background: #181818;
        color: #eeeeee;
        padding: 12px 16px;
        border-radius: 20px 20px 20px 5px;
        margin: 14px 0;
        max-width: 90%;
        margin-right: auto;
        border: 1px solid #292929;
        font-size: 15px;
        line-height: 1.6;
    }
    .anis-ai-name {
        font-size: 12px;
        color: #858585;
        margin-bottom: 5px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# HEADER & SIDEBAR NAVIGATION
# =========================================================

menu_col, title_col, profile_col = st.columns([1, 5, 1], vertical_alignment="center")

with menu_col:
    menu_clicked = st.button("☰", key="mobile_menu_button", help="Open menu")

with title_col:
    st.markdown('<div style="font-size:18px; font-weight:600; color:#fff; text-align:center;">✦ Anis AI</div>', unsafe_allow_html=True)

with profile_col:
    profile_clicked = st.button("A", key="mobile_profile_button", help="Profile")

if "mobile_sidebar_open" not in st.session_state:
    st.session_state.mobile_sidebar_open = False

if menu_clicked:
    st.session_state.mobile_sidebar_open = not st.session_state.mobile_sidebar_open
    st.rerun()

# সাইডবার প্যানেল
if st.session_state.mobile_sidebar_open:
    with st.sidebar:
        st.markdown("### ✦ Anis AI Menu")
        if st.button("✦ New Chat", use_container_width=True):
            st.session_state.messages = []
            st.session_state.mobile_sidebar_open = False
            st.rerun()
        
        st.markdown("---")
        st.markdown("**Chat History:**")
        if not st.session_state.history:
            st.caption("No previous conversations.")
        else:
            for chat in reversed(st.session_state.history):
                if st.button(f"💬 {chat.get('title', 'Chat')}", key=f"hist_{chat.get('id')}", use_container_width=True):
                    st.session_state.messages = chat.get("messages", [])
                    st.session_state.mobile_sidebar_open = False
                    st.rerun()


# =========================================================
# HOME SCREEN (যখন কোনো চ্যাট শুরু হয়নি)
# =========================================================

if not st.session_state.messages:
    st.markdown(
        """
        <div style="min-height: calc(100dvh - 190px); display: flex; flex-direction: column; justify-content: center; padding: 10px 4px;">
            <h1 style="font-size: 36px; font-weight: 600; margin: 0; color: #ffffff;">Hi Anis</h1>
            <p style="font-size: 24px; color: #8b8b8b; margin-top: 8px;">Where should we start?</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📝 Create MCQ", use_container_width=True):
            st.session_state.active_mode = "mcq"
            st.session_state.messages.append({"role": "user", "content": "I want to create MCQs."})
            st.rerun()
        if st.button("🔍 Analyze", use_container_width=True):
            st.session_state.active_mode = "analyze"
            st.session_state.messages.append({"role": "user", "content": "I want to analyze something."})
            st.rerun()
    with col2:
        if st.button("📚 Help Me Learn", use_container_width=True):
            st.session_state.active_mode = "learn"
            st.session_state.messages.append({"role": "user", "content": "Help me learn."})
            st.rerun()
        if st.button("🖼️ Create Image", use_container_width=True):
            st.session_state.active_mode = "image"
            st.session_state.messages.append({"role": "user", "content": "I want to create an image."})
            st.rerun()


# =========================================================
# CHAT MESSAGES DISPLAY SCREEN
# =========================================================

if st.session_state.messages:
    st.markdown('<div class="anis-chat-screen">', unsafe_allow_html=True)
    for message in st.session_state.messages:
        role = message.get("role", "assistant")
        content = message.get("content", "")
        
        if role == "user":
            st.markdown(f'<div class="user-msg">{content}</div>', unsafe_allow_html=True)
        else:
            st.markdown(
                f"""
                <div class="ai-msg">
                    <div class="anis-ai-name">✦ Anis AI</div>
                    {content}
                </div>
                """,
                unsafe_allow_html=True,
            )
    st.markdown('</div>', unsafe_allow_html=True)


# =========================================================
# CHAT INPUT & HELPERS PROCESSING
# =========================================================

user_input = st.chat_input("Ask Anis AI...")

if user_input:
    # ১. ইউজারের মেসেজ যোগ করা
    st.session_state.messages.append({"role": "user", "content": user_input})

    # ২. মেমোরি এবং কনটেক্সট ম্যানেজ করা (helpers.py ফাংশন)
    try:
        conversation_context = manage_conversation_memory(st.session_state.messages)
    except Exception:
        conversation_context = st.session_state.messages

    # ৩. ওয়েব সার্চের প্রয়োজন আছে কিনা দেখা (helpers.py ফাংশন)
    try:
        should_search = needs_web_search(user_input)
    except Exception:
        should_search = False

    search_results = None
    if should_search:
        try:
            search_results = smart_search(user_input)
        except Exception:
            search_results = None

    # ৪. টাস্ক অনুযায়ী মডেল সিলেক্ট করা (helpers.py ফাংশন)
    try:
        selected_model = select_model_by_task(user_input)
    except Exception:
        selected_model = None

    ai_prompt = user_input
    if search_results:
        ai_prompt += f"\n\nRelevant web information:\n{search_results}"

    # ৫. এআই ফলব্যাক সিস্টেম কল করা (helpers.py ফাংশন)
    try:
        ai_response = provider_aware_ai_fallback(
            prompt=ai_prompt,
            model=selected_model,
            conversation=conversation_context
        )
    except TypeError:
        try:
            ai_response = provider_aware_ai_fallback(ai_prompt)
        except Exception:
            ai_response = "দুঃখিত, এই মুহূর্তে Anis AI প্রসেস করতে পারছে না।"
    except Exception:
        ai_response = "দুঃখিত, কোনো একটি সমস্যা হয়েছে।"

    if not ai_response:
        ai_response = "দুঃখিত, কোনো উত্তর পাওয়া যায়নি।"
    elif not isinstance(ai_response, str):
        ai_response = str(ai_response)

    # ৬. এআই এর উত্তর সেভ করা
    st.session_state.messages.append({"role": "assistant", "content": ai_response})

    # ৭. ইউজেজ লগ করা
    try:
        log_usage("chat")
    except Exception:
        pass

    st.rerun()
