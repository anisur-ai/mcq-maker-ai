# ============================================
# main.py — PART 1 START
# (এই পার্টটা ফাইলের একদম শুরুতে বসাবেন)
# ============================================

import streamlit as st
import time
from helper import (
    get_ai_response,
    MODEL_DISPLAY_NAMES,
)

# ===== পেজ কনফিগারেশন =====
st.set_page_config(
    page_title="Anis Ai",
    page_icon="assets/logo.png",
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

    /* ইনপুট বক্স ও বাটন হোভার ইফেক্ট (লাইটওয়েট, লো-RAM ফোনের জন্য সিম্পল transition) */
    .stButton button {
        transition: transform 0.15s ease, box-shadow 0.15s ease;
        border-radius: 12px !important;
    }
    .stButton button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 14px rgba(79, 168, 255, 0.25);
    }

    /* স্ক্রলবার হালকা/মিনিমাল রাখা (পারফরম্যান্সের জন্য ভারী কিছু না) */
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
# (এর নিচে পরের পার্ট জোড়া দেবেন)
# ============================================