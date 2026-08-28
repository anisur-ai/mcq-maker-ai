import streamlit as st
from datetime import datetime

# helpers.py থেকে প্রয়োজনীয় ফাংশনগুলো ইমপোর্ট করা হলো
from helpers import (
    smart_read_file,
    needs_web_search,
    smart_search,
    smart_scrape,
    select_model_by_task,
    manage_conversation_memory,
    provider_aware_ai_fallback,
)

# ==========================================
# পেজ কনফিগারেশন
# ==========================================
st.set_page_config(
    page_title="Anis AI Assistant",
    page_icon="🤖",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ==========================================
# কাস্টম CSS স্টাইল (মডার্ন চ্যাট অ্যাপ লুক)
# ==========================================
st.markdown(
    """
    <style>
    html, body, [data-testid="stAppViewContainer"] {
        background-color: #121212;
        color: #ffffff;
    }
    header[data-testid="stHeader"] {
        background: transparent;
    }
    .block-container {
        max-width: 700px;
        padding-top: 2rem;
        padding-bottom: 110px;
    }
    .user-msg {
        background: #2b2b2b;
        color: #ffffff;
        padding: 12px 16px;
        border-radius: 18px 18px 4px 18px;
        margin: 10px 0;
        max-width: 80%;
        margin-left: auto;
        font-size: 15px;
    }
    .ai-msg {
        background: #1e1e1e;
        color: #e0e0e0;
        padding: 12px 16px;
        border-radius: 18px 18px 18px 4px;
        margin: 10px 0;
        max-width: 80%;
        margin-right: auto;
        border: 1px solid #2a2a2a;
        font-size: 15px;
    }
    .app-title {
        text-align: center;
        font-size: 26px;
        font-weight: 700;
        margin-bottom: 20px;
        color: #ffffff;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ==========================================
# সেশন স্টেট ইনিশিয়ালাইজেশন
# ==========================================
if "messages" not in st.session_state:
    st.session_state.messages = []

# ==========================================
# ইউজার ইন্টারফেস (UI)
# ==========================================
st.markdown('<div class="app-title">🤖 Anis AI Assistant</div>', unsafe_allow_html=True)

# চ্যাট হিস্ট্রি প্রদর্শন করা
for message in st.session_state.messages:
    if message["role"] == "user":
        st.markdown(f'<div class="user-msg">{message["content"]}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="ai-msg"><b>✦ Anis AI:</b><br>{message["content"]}</div>', unsafe_allow_html=True)

# ==========================================
# চ্যাট ইনপুট এবং প্রসেসিং
# ==========================================
user_input = st.chat_input("আপনার মেসেজ এখানে লিখুন...")

if user_input:
    # ১. ইউজারের মেসেজ সেভ করা
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    # ২. কনভার্সেশন মেমোরি ম্যানেজ করা (helpers.py এর ফাংশন)
    try:
        conversation_context = manage_conversation_memory(st.session_state.messages)
    except Exception:
        conversation_context = st.session_state.messages

    # ৩. ওয়েবে সার্চ করার প্রয়োজন আছে কিনা চেক করা (helpers.py এর ফাংশন)
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

    # ৪. টাস্ক অনুযায়ী মডেল সিলেক্ট করা (helpers.py এর ফাংশন)
    try:
        selected_model = select_model_by_task(user_input)
    except Exception:
        selected_model = None

    # ৫. প্রম্পট তৈরি করা
    ai_prompt = user_input
    if search_results:
        ai_prompt += f"\n\nRelevant web information:\n{search_results}"

    # ৬. এআই রেসপন্স জেনरेट করা (helpers.py এর ফলব্যাক সিস্টেম)
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

    # নর্মালাইজেশন
    if not ai_response:
        ai_response = "দুঃখিত, কোনো উত্তর পাওয়া যায়নি।"
    elif not isinstance(ai_response, str):
        ai_response = str(ai_response)

    # ৭. এআই-এর রেসপন্স সেভ করা
    st.session_state.messages.append({"role": "assistant", "content": ai_response})
    
    # পেজ রিলোড করা
    st.rerun()
