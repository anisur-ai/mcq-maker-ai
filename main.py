import streamlit as st
import io
import requests
import docx
import fitz  # PyMuPDF
import pypdf
import google.generativeai as genai
from groq import Groq
from openai import OpenAI

from analytics import log_usage

# =========================================================
# SAFE HELPERS IMPORT (helpers.py এর সাথে সংযোগ রক্ষা করতে)
# =========================================================
try:
    from helpers import (
        smart_read_file,
        needs_web_search,
        smart_search,
        smart_scrape,
        select_model_by_task,
        manage_conversation_memory,
        provider_aware_ai_fallback,
    )
except ImportError as e:
    st.error(f"Helpers Import Error: {e}")

# ফলব্যাক ফাংশন (যদি helpers.py এ এগুলো না থাকে)
try:
    from helpers import create_chat_title
except ImportError:
    def create_chat_title(text):
        return text[:30] if text else "New Chat"

try:
    from helpers import cleanup_old_history
except ImportError:
    def cleanup_old_history(history):
        return history


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

if "active_mode" not in st.session_state:
    st.session_state.active_mode = None

if "mobile_sidebar_open" not in st.session_state:
    st.session_state.mobile_sidebar_open = False


# =========================================================
# STYLING (MOBILE APP STYLE CSS)
# =========================================================

st.markdown(
    """
    <style>
    html, body, [data-testid="stAppViewContainer"] {
        background: #000000 !important;
        color: #ffffff !important;
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
    menu_clicked = st.button("☰", key="mobile_menu_button")

with title_col:
    st.markdown('<div style="font-size:18px; font-weight:600; color:#fff; text-align:center;">✦ Anis AI</div>', unsafe_allow_html=True)

with profile_col:
    profile_clicked = st.button("A", key="mobile_profile_button")

if menu_clicked:
    st.session_state.mobile_sidebar_open = not st.session_state.mobile_sidebar_open
    st.rerun()

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
# HOME SCREEN (যখন চ্যাট খালি থাকে)
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
            st.session_state.messages.append({"role": "user", "content": "I want to create MCQs."})
            st.rerun()
        if st.button("🔍 Analyze", use_container_width=True):
            st.session_state.messages.append({"role": "user", "content": "I want to analyze something."})
            st.rerun()
    with col2:
        if st.button("📚 Help Me Learn", use_container_width=True):
            st.session_state.messages.append({"role": "user", "content": "Help me learn."})
            st.rerun()
        if st.button("🖼️ Create Image", use_container_width=True):
            st.session_state.messages.append({"role": "user", "content": "I want to create an image."})
            st.rerun()


# =========================================================
# CHAT MESSAGES DISPLAY
# =========================================================

if st.session_state.messages:
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


# =========================================================
# CHAT INPUT & PROCESSING
# =========================================================

user_input = st.chat_input("Ask Anis AI...")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})

    # মেমোরি ও কনটেক্সট প্রসেসিং
    try:
        conversation_context = manage_conversation_memory(st.session_state.messages)
    except Exception:
        conversation_context = st.session_state.messages

    # ওয়েব সার্চ চেক
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

    # মডেল সিলেকশন
    try:
        selected_model = select_model_by_task(user_input)
    except Exception:
        selected_model = None

    ai_prompt = user_input
    if search_results:
        ai_prompt += f"\n\nRelevant web information:\n{search_results}"

    # এআই রেসপন্স ফলব্যাক কল
    try:
        ai_response = provider_aware_ai_fallback(
            prompt=ai_prompt,
            model=selected_model,
            conversation=conversation_context
        )
    except Exception:
        ai_response = "দুঃখিত, এই মুহূর্তে Anis AI প্রসেস করতে পারছে না।"

    if not ai_response:
        ai_response = "দুঃখিত, কোনো উত্তর পাওয়া যায়নি।"
    elif not isinstance(ai_response, str):
        ai_response = str(ai_response)

    st.session_state.messages.append({"role": "assistant", "content": ai_response})

    try:
        log_usage("chat")
    except Exception:
        pass

    st.rerun()
    
