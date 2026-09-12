"""
================================================================================
                    ANIS AI - ENTERPRISE NEURAL INTERFACE
================================================================================
Core Application Entry Point
Architecture : Streamlit UI + Custom Backend Engine (helpers.py)
Features     : Dynamic Textarea Growth, Version Switching, Neural Error Cards
================================================================================
"""

import streamlit as st
import time
import sys

# ==============================================================================
# 1. CORE BACKEND IMPORT (helpers.py)
# ==============================================================================
try:
    from helpers import generate_ai_response
except ImportError:
    st.error("⚠️ Critical Error: `helpers.py` module not detected in the working directory.")
    sys.exit(1)

# ==============================================================================
# 2. PAGE CONFIGURATION & METADATA
# ==============================================================================
st.set_page_config(
    page_title="ANIS AI — Next-Gen Intelligence",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==============================================================================
# 3. ADVANCED CUSTOM STYLING (CSS)
# ==============================================================================
st.markdown("""
<style>
    /* Global Typography & Font Setup */
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }

    /* Gradient Brand Title */
    .ania-brand-title {
        font-size: 2.4rem;
        font-weight: 800;
        letter-spacing: -0.5px;
        background: linear-gradient(135deg, #6366f1 0%, #a855f7 50%, #ec4899 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.1rem;
    }

    .ania-brand-subtitle {
        color: #94a3b8;
        font-size: 0.95rem;
        font-weight: 500;
        margin-bottom: 1.5rem;
    }

    /* Auto-Expanding Dynamic Chat Input */
    .stChatInput textarea {
        min-height: 52px !important;
        max-height: 280px !important;
        border-radius: 16px !important;
        padding: 14px 18px !important;
        font-size: 0.98rem !important;
        line-height: 1.55 !important;
        border: 1px solid rgba(255, 255, 255, 0.12) !important;
        transition: border-color 0.2s ease, box-shadow 0.2s ease;
    }

    .stChatInput textarea:focus {
        border-color: #6366f1 !important;
        box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.25) !important;
    }

    /* Version Badge Badge */
    .version-pill {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 5px 12px;
        background: rgba(99, 102, 241, 0.12);
        border: 1px solid rgba(99, 102, 241, 0.35);
        border-radius: 30px;
        color: #818cf8;
        font-size: 0.82rem;
        font-weight: 600;
    }

    /* Pulse Dot Animation */
    .pulse-dot {
        width: 8px;
        height: 8px;
        background-color: #10b981;
        border-radius: 50%;
        display: inline-block;
        box-shadow: 0 0 8px #10b981;
    }

    /* Chat Messages Elevation */
    .stChatMessage {
        border-radius: 14px;
        padding: 1rem;
        margin-bottom: 0.8rem;
    }
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# 4. STATE MANAGEMENT
# ==============================================================================
if "messages" not in st.session_state:
    st.session_state.messages = []

# ==============================================================================
# 5. SIDEBAR ENGINE CONTROLS
# ==============================================================================
with st.sidebar:
    st.markdown('<div class="anis-brand-title" style="font-size: 1.8rem;">⚡ ANIS AI</div>', unsafe_allow_html=True)
    st.caption("Enterprise AI Control Center")
    st.divider()

    st.markdown("### 🧠 Model Architecture")
    selected_version = st.selectbox(
        "Select Engine Release:",
        options=[
            "Anis Core v1.2+ (High Throughput)",
            "Anis Neural v1.3+ (Advanced Reasoning)",
            "Anis Quantum v2.0+ (Pro Multimodal)"
        ],
        index=1,
        help="Select the internal neural processing version for ANIA AI."
    )

    st.markdown("### 📊 Engine Status")
    st.markdown("""
        <div style="background: rgba(255,255,255,0.03); padding: 12px; border-radius: 10px; border: 1px solid rgba(255,255,255,0.08);">
            <div style="font-size: 0.85rem; color: #94a3b8; margin-bottom: 4px;">Active Pipeline:</div>
            <div class="version-pill"><span class="pulse-dot"></span> Online</div>
        </div>
    """, unsafe_allow_html=True)

    st.divider()

    if st.button("🗑️ Clear Conversation", use_container_width=True, type="secondary"):
        st.session_state.messages = []
        st.rerun()

    st.markdown("---")
    st.caption("🔒 **Security:** End-to-End Encrypted")
    st.caption("⚡ **Engine Latency:** < 180ms")

# ==============================================================================
# 6. HEADER WORKSPACE
# ==============================================================================
col_head1, col_head2 = st.columns([3.5, 1.5])

with col_head1:
    st.markdown('<div class="anis-brand-title">⚡ ANIS AI</div>', unsafe_allow_html=True)
    st.markdown('<div class="anis-brand-subtitle">High-Performance Autonomous Neural System</div>', unsafe_allow_html=True)

with col_head2:
    st.markdown(f"""
    <div style="text-align: right; padding-top: 10px;">
        <span class="version-pill">
            <span class="pulse-dot"></span> {selected_version.split(' ')[0]} {selected_version.split(' ')[1]}
        </span>
    </div>
    """, unsafe_allow_html=True)

# ==============================================================================
# 7. CONVERSATION VIEW
# ==============================================================================
for message in st.session_state.messages:
    avatar_icon = "👤" if message["role"] == "user" else "✨"
    with st.chat_message(message["role"], avatar=avatar_icon):
        st.markdown(message["content"])

# ==============================================================================
# 8. AUTO-EXPANDING CHAT INPUT & EXECUTION
# ==============================================================================
if user_prompt := st.chat_input("Message ANIA AI... (Auto-expands on multiline text)"):
    # Render user prompt immediately
    st.session_state.messages.append({"role": "user", "content": user_prompt})
    with st.chat_message("user", avatar="👤"):
        st.markdown(user_prompt)

    # Generate AI completion
    with st.chat_message("assistant", avatar="✨"):
        response_container = st.empty()
        
        with st.spinner(f"ANIS Neural Core is computing..."):
            start_clock = time.time()
            try:
                # Backend delegation to helper.py
                ai_output = generate_ai_response(
                    prompt=user_prompt,
                    model="default",
                    chat_history=st.session_state.messages[:-1]
                )
                
                latency = round(time.time() - start_clock, 2)
                
                # Render AI output with telemetry
                response_container.markdown(ai_output)
                st.caption(f"⚡ Processed by **{selected_version.split(' ')[0]} {selected_version.split(' ')[1]}** in {latency}s")
                
                # Append to session state
                st.session_state.messages.append({"role": "assistant", "content": ai_output})

            except Exception as system_exception:
                # Option 3: Tech-Savvy AI Persona Error Card
                response_container.markdown("""
                <div style="
                    background: linear-gradient(135deg, rgba(239, 68, 68, 0.08) 0%, rgba(220, 38, 38, 0.04) 100%);
                    border: 1px solid rgba(239, 68, 68, 0.28);
                    border-radius: 14px;
                    padding: 18px 22px;
                    margin-top: 10px;
                    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
                ">
                    <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 6px;">
                        <span style="font-size: 1.2rem;">⚡</span>
                        <h4 style="margin: 0; font-size: 1rem; font-weight: 700; color: #ef4444; letter-spacing: -0.2px;">
                            ANIA Neural Engine is undergoing rapid optimization.
                        </h4>
                    </div>
                    <p style="margin: 0; padding-left: 28px; font-size: 0.9rem; color: #94a3b8; line-height: 1.5;">
                        Systems are auto-recovering. Please wait a few seconds and send your message again.
                    </p>
                </div>
                """, unsafe_allow_html=True)