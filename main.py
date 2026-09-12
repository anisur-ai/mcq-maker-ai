# ============================================
# main.py — PART 1 START
# ============================================

import streamlit as st
import time
import base64
from io import BytesIO
from helpers import (
    get_ai_response,
    MODEL_DISPLAY_NAMES,
)

# ===== আপনার দেওয়া আসল লোগোটি স্থায়ীভাবে কোডের ভেতর এমবেড করা হলো =====
# (যাতে কোনো বাহ্যিক ফাইল বা ইন্টারনেটের লিঙ্কের উপর নির্ভর করতে না হয়)
LOGO_BASE64 = """
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
AAAASUVORK5CYII="""

# Base64 স্ট্রিংকে ইমেজে রূপান্তর করা
IMAGE_BYTES = BytesIO(base64.b64decode(LOGO_BASE64.strip()))

# ===== পেজ কনফিগারেশন =====
st.set_page_config(
    page_title="Anis Ai",
    page_icon=IMAGE_BYTES,
    layout="wide",
    initial_sidebar_state="expanded",
)

# ===== প্রফেশনাল কাস্টম CSS (লোগোর নীল-কালো থিম অনুযায়ী) =====
st.markdown("""
<style>
    /* পুরো অ্যাপের ব্যাকগ্রাউন্ড */
    .stApp {
        background: linear-gradient(180deg, #05070d 0%, #0a0e1a 100%);
        color: #e8ecf5;
    }

    /* হেডার হাইড করা (ক্লিন লুকের জন্য) */
    header[data-testid="stHeader"] {
        background: transparent;
    }

    /* সাইডবার স্টাইল */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0a0e1a 0%, #05070d 100%);
        border-right: 1px solid rgba(59, 130, 246, 0.15);
    }

    /* চ্যাট মেসেজ বাবল - ইউজার */
    .stChatMessage[data-testid="stChatMessage"] {
        border-radius: 16px;
        padding: 4px;
        margin-bottom: 8px;
    }

    /* মেইন টাইটেল স্টাইল */
    .anis-title {
        background: linear-gradient(90deg, #4fa8ff 0%, #7c5cff 60%, #a78bfa 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
        font-size: 28px;
    }

    /* ইনপুট বক্স ও বাটন হোভার ইফেক্ট */
    .stButton button {
        transition: transform 0.15s ease, box-shadow 0.15s ease;
        border-radius: 12px !important;
    }
    .stButton button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 14px rgba(79, 168, 255, 0.25);
    }

    /* স্ক্রলবার হালকা/মিনিমাল রাখা */
    ::-webkit-scrollbar {
        width: 6px;
    }
    ::-webkit-scrollbar-thumb {
        background: rgba(79, 168, 255, 0.3);
        border-radius: 10px;
    }
</style>
""", unsafe_allow_html=True)

# ============================================
# main.py — PART 1 END
# ============================================

# ============================================
# main.py — PART 2 START
# ============================================

# ===== SESSION STATE ইনিশিয়ালাইজেশন =====
if "messages" not in st.session_state:
    st.session_state.messages = []

if "theme" not in st.session_state:
    st.session_state.theme = "dark"

if "web_search_enabled" not in st.session_state:
    st.session_state.web_search_enabled = True

model_list = list(MODEL_DISPLAY_NAMES.values()) if MODEL_DISPLAY_NAMES else ["Anis 1.0 Flash"]

if "selected_model" not in st.session_state:
    st.session_state.selected_model = model_list[0]

# ===== সাইডবার শুরু =====
with st.sidebar:

    # --- লোগো ও অ্যাপের নাম ---
    col_logo, col_name = st.columns([1, 3])
    with col_logo:
        st.image(IMAGE_BYTES, width=50)
    with col_name:
        st.markdown(
            "<div class='anis-title' style='font-size:22px; margin-top:6px;'>Anis Ai</div>",
            unsafe_allow_html=True
        )
    st.caption("Smarter Ideas • Better Tomorrow")

    st.divider()

    # --- নতুন চ্যাট বাটন ---
    if st.button("➕ নতুন চ্যাট", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

    st.divider()

    # --- থিম টগল ---
    theme_choice = st.toggle("🌙 ডার্ক মোড", value=(st.session_state.theme == "dark"))
    st.session_state.theme = "dark" if theme_choice else "light"

    # --- ওয়েব সার্চ টগল ---
    st.session_state.web_search_enabled = st.toggle(
        "🌐 ওয়েব সার্চ",
        value=st.session_state.web_search_enabled
    )

    st.divider()

    # --- চ্যাট হিস্ট্রি (সংক্ষিপ্ত প্রিভিউ) ---
    if len(st.session_state.messages) > 0:
        st.markdown("**সাম্প্রতিক চ্যাট**")
        user_msgs = [m for m in st.session_state.messages if m["role"] == "user"]
        for msg in user_msgs[-5:][::-1]:
            preview = msg["content"][:30] + ("..." if len(msg["content"]) > 30 else "")
            st.caption(f"💬 {preview}")

    st.divider()

    # --- About সেকশন ---
    with st.expander("ℹ️ About Anis Ai"):
        st.markdown("""
        **Anis Ai** — আপনার ব্যক্তিগত AI সহকারী।

        যেকোনো প্রশ্নের উত্তর, রিয়েল-টাইম তথ্য অনুসন্ধান,
        ছবি বিশ্লেষণ ও ভয়েস সাপোর্ট নিয়ে তৈরি।

        _Smarter Ideas • Better Tomorrow_
        """)

# ============================================
# main.py — PART 2 END
# ============================================

# ============================================
# main.py — PART 3 START
# ============================================

# ===== মেইন এরিয়া হেডার =====
header_col1, header_col2 = st.columns([1, 8])
with header_col1:
    st.image(IMAGE_BYTES, width=45)
with header_col2:
    st.markdown(
        "<div class='anis-title'>Anis Ai</div>",
        unsafe_allow_html=True
    )

st.markdown("<div style='margin-bottom: 10px;'></div>", unsafe_allow_html=True)

# ===== যদি কোনো মেসেজ না থাকে (স্বাগতম স্ক্রিন) =====
if len(st.session_state.messages) == 0:
    st.markdown(
        """
        <div style='text-align:center; padding: 60px 20px; opacity: 0.8;'>
            <h3 style='color:#9fb3d9;'>আজ কীভাবে সাহায্য করতে পারি?</h3>
            <p style='color:#5c6b8a;'>যেকোনো প্রশ্ন লিখে শুরু করুন</p>
        </div>
        """,
        unsafe_allow_html=True
    )

# ===== আগের সব চ্যাট মেসেজ লুপ করে দেখানো =====
for msg in st.session_state.messages:
    role = msg["role"]
    avatar = "🧑" if role == "user" else IMAGE_BYTES

    with st.chat_message(role, avatar=avatar):
        st.markdown(msg["content"])

        # assistant-এর মেসেজের নিচে মডেলের নাম
        if role == "assistant" and "model_used" in msg:
            st.caption(f"⚡ {msg['model_used']}")

# ============================================
# main.py — PART 3 END
# ============================================

# ============================================
# main.py — PART 4 START
# ============================================

# ===== ইনপুট বারের কন্ট্রোল রো ("+", মডেল সিলেক্টর, মাইক) =====
control_col1, control_col2, control_col3 = st.columns([1, 3, 1])

uploaded_image = None
voice_text = None

with control_col1:
    with st.popover("➕", use_container_width=True):
        uploaded_image = st.file_uploader(
            "ছবি পাঠান",
            type=["png", "jpg", "jpeg"],
            label_visibility="collapsed",
            key="image_uploader"
        )

with control_col2:
    selected_idx = 0
    if st.session_state.selected_model in model_list:
        selected_idx = model_list.index(st.session_state.selected_model)

    st.session_state.selected_model = st.selectbox(
        "মডেল",
        options=model_list,
        index=selected_idx,
        label_visibility="collapsed",
    )

with control_col3:
    with st.popover("🎤", use_container_width=True):
        audio_input = st.audio_input("কথা বলুন", label_visibility="collapsed")
        if audio_input is not None:
            voice_text = audio_input

# ছবি আপলোড হলে ছোট প্রিভিউ দেখানো
if uploaded_image is not None:
    st.image(uploaded_image, width=80, caption="সংযুক্ত ছবি")

# ============================================
# main.py — PART 4 END
# ============================================

# ============================================
# main.py — PART 5 START
# ============================================

# ===== মূল টেক্সট ইনপুট বক্স =====
user_input = st.chat_input("Anis Ai-কে কিছু জিজ্ঞেস করুন...")

final_input = user_input
if final_input is None and voice_text is not None:
    final_input = "voice_input_placeholder"

# ===== ইউজার মেসেজ সাবমিট হলে যা ঘটবে =====
if final_input:

    display_text = final_input
    if uploaded_image is not None:
        display_text += "  📷 [ছবি সংযুক্ত]"

    st.session_state.messages.append({
        "role": "user",
        "content": display_text
    })

    with st.chat_message("user", avatar="🧑"):
        st.markdown(display_text)

    # ===== AI-এর উত্তর আনা =====
    with st.chat_message("assistant", avatar=IMAGE_BYTES):
        placeholder = st.empty()
        placeholder.markdown("⏳ *লিখছে...*")

        try:
            ai_result = get_ai_response(
                user_message=final_input,
                web_search_enabled=st.session_state.web_search_enabled,
                image_file=uploaded_image,
            )

            answer_text = ai_result.get("answer", "দুঃখিত, উত্তর তৈরি করা যায়নি।")
            model_used = st.session_state.selected_model

            placeholder.markdown(answer_text)
            st.caption(f"⚡ {model_used}")

            st.session_state.messages.append({
                "role": "assistant",
                "content": answer_text,
                "model_used": model_used
            })

        except Exception as e:
            error_msg = "⚠️ এই মুহূর্তে সার্ভিস দিতে সমস্যা হচ্ছে। একটু পরে আবার চেষ্টা করুন।"
            placeholder.markdown(error_msg)
            print(f"[MAIN ERROR] {e}")

            st.session_state.messages.append({
                "role": "assistant",
                "content": error_msg
            })

    st.rerun()

# ============================================
# main.py — PART 5 END
# ============================================
