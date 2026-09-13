"""
================================================================================
                    ANIS AI - NEXT-GEN ENTERPRISE FRONTEND
================================================================================
Architecture: Autonomous Multi-LLM Cascade + Live Web Search + Multimodal
UI Styling: ChatGPT 4o & Google Gemini Advanced Hybrid Design
Compatible with: helpers.py
================================================================================
"""

import streamlit as st
import time
from helpers import (
    run_text_ai_chain,
    classify_task,
    run_web_search,
    call_gemini,
    call_groq,
    call_cerebras,
    call_mistral,
    call_openrouter,
)

# ==============================================================================
# 1. PAGE CONFIGURATION & METADATA
# ==============================================================================
st.set_page_config(
    page_title="Anis AI — Intelligence Redefined",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ==============================================================================
# 2. ULTRA-MODERN CSS INJECTION (ChatGPT & Gemini Aesthetic)
# ==============================================================================
CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap');

:root {
    --bg-primary: #090a0f;
    --bg-secondary: #12141c;
    --bg-card: rgba(22, 25, 37, 0.7);
    --border-subtle: rgba(255, 255, 255, 0.08);
    --accent-gradient: linear-gradient(135deg, #6366f1 0%, #a855f7 50%, #ec4899 100%);
    --accent-blue: #3b82f6;
    --text-primary: #f3f4f6;
    --text-muted: #9ca3af;
}

html, body, [class*="css"] {
    font-family: 'Outfit', sans-serif;
    background-color: var(--bg-primary) !important;
    color: var(--text-primary) !important;
}

#MainMenu {visibility: hidden;}
header {visibility: hidden;}
footer {visibility: hidden;}

/* Custom Top Navigation */
.top-nav {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 10px 20px;
    background: rgba(18, 20, 28, 0.85);
    backdrop-filter: blur(20px);
    border-bottom: 1px solid var(--border-subtle);
    border-radius: 0 0 16px 16px;
    margin-bottom: 20px;
}

.brand-badge {
    background: rgba(99, 102, 241, 0.15);
    border: 1px solid rgba(99, 102, 241, 0.3);
    color: #818cf8;
    font-size: 0.72rem;
    padding: 2px 8px;
    border-radius: 12px;
    font-weight: 600;
    letter-spacing: 0.5px;
}

/* Hero Section */
.hero-container {
    text-align: center;
    padding: 40px 20px 20px 20px;
    max-width: 820px;
    margin: 0 auto;
}

.hero-title {
    font-size: 2.8rem;
    font-weight: 700;
    line-height: 1.2;
    margin-bottom: 10px;
    background: linear-gradient(180deg, #FFFFFF 0%, #A5B4FC 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

.hero-subtitle {
    font-size: 1.05rem;
    color: var(--text-muted);
    margin-bottom: 30px;
}

/* Provider Chip Badge */
.provider-badge {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    font-size: 0.72rem;
    padding: 3px 10px;
    border-radius: 20px;
    background: rgba(99, 102, 241, 0.12);
    border: 1px solid rgba(99, 102, 241, 0.25);
    color: #a5b4fc;
    margin-bottom: 12px;
    font-weight: 600;
    letter-spacing: 0.6px;
    text-transform: uppercase;
}

/* Footer Disclaimer */
.footer-disclaimer {
    text-align: center;
    font-size: 0.76rem;
    color: #6b7280;
    margin-top: 15px;
    padding-bottom: 8px;
}

.footer-disclaimer b {
    color: #9ca3af;
}

/* Chat Input Bar */
.stChatInput textarea {
    background-color: #141722 !important;
    border: 1px solid rgba(255, 255, 255, 0.12) !important;
    border-radius: 20px !important;
    color: #f3f4f6 !important;
    font-size: 0.95rem !important;
}

.stChatInput textarea:focus {
    border-color: #818cf8 !important;
    box-shadow: 0 0 16px rgba(129, 140, 248, 0.25) !important;
}
</style>
"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# ==============================================================================
# 3. SESSION STATE INITIALIZATION
# ==============================================================================
if "messages" not in st.session_state:
    st.session_state.messages = []

if "model_engine" not in st.session_state:
    st.session_state.model_engine = "⚡ Anis Auto-Cascade Pro (Autonomous)"

if "web_search_enabled" not in st.session_state:
    st.session_state.web_search_enabled = False

# ==============================================================================
# 4. TOP NAVIGATION & MODEL SELECTOR (BRANDED ANIS ENGINES)
# ==============================================================================
col_brand, col_model, col_switch = st.columns([1.6, 2.4, 1.2])

with col_brand:
    st.markdown("""
        <div style="display: flex; align-items: center; gap: 8px; padding-top: 5px;">
            <span style="font-size: 1.5rem;">✨</span>
            <span style="font-size: 1.35rem; font-weight: 700; background: linear-gradient(135deg, #6366f1, #ec4899); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">Anis AI</span>
            <span class="brand-badge">2.5 ULTRA</span>
        </div>
    """, unsafe_allow_html=True)

with col_model:
    selected_mode = st.selectbox(
        label="Select Anis AI Model Architecture",
        options=[
            "⚡ Anis Auto-Cascade Pro (Autonomous)",
            "🧠 Anis 2.0 Flash (Multimodal & Fast)",
            "🚀 Anis 3.3 Ultra Speed (Ultra-Low Latency)",
            "⚡ Anis 3.3 Versatile (High Throughput)",
            "🛡️ Anis Small Core (Reasoning & Code)",
            "🌐 Anis Meta-Llama 3.3 (Extended Context)",
        ],
        index=0,
        label_visibility="collapsed"
    )
    st.session_state.model_engine = selected_mode

with col_switch:
    st.session_state.web_search_enabled = st.toggle(
        "🌐 Live Search",
        value=st.session_state.web_search_enabled
    )

# ==============================================================================
# 5. SIDEBAR (MULTIMODAL ATTACHMENTS & CONTROLS)
# ==============================================================================
with st.sidebar:
    st.markdown("### 🎛️ Anis AI Control Panel")
    st.markdown("---")

    st.markdown("#### 📎 Attachment & Multimodal")

    uploaded_file = st.file_uploader(
        "Upload image or document file",
        type=["png", "jpg", "jpeg", "txt", "py", "json", "pdf"],
        help="Upload files or screenshots for code review, data extraction, or visual analysis."
    )

    if uploaded_file:
        st.success(f"Attached: {uploaded_file.name}")

        if uploaded_file.type.startswith("image"):
            st.image(
                uploaded_file,
                use_container_width=True
            )

    st.markdown("---")

    st.markdown("#### 💬 Session Management")

    if st.button(
        "🗑️ Clear Chat History",
        use_container_width=True
    ):
        st.session_state.messages = []
        st.rerun()

    st.markdown("---")

    st.markdown("""
        <div style="font-size: 0.8rem; color: #6b7280; line-height: 1.5;">
            <b>System Engine Specs:</b><br>
            • Multi-LLM Autonomous Cascade<br>
            • Ultra-Low Latency Sub-second Routing<br>
            • Real-time Web Grounding Engine
        </div>
    """, unsafe_allow_html=True)
# ==============================================================================
# 6. HERO SECTION & PROMPT STARTERS (EMPTY CHAT STATE)
# ==============================================================================

if len(st.session_state.messages) == 0:
    st.markdown("""
        <div class="hero-container">
            <div class="hero-title">How can Anis AI assist you today?</div>
            <div class="hero-subtitle">
                Empowered by an autonomous cascade architecture for
                ultra-fast generation, deep reasoning, and live search.
            </div>
        </div>
    """, unsafe_allow_html=True)

    # Interactive Prompt Cards
    c1, c2, c3, c4 = st.columns(4)

    with c1:
        if st.button(
            "💻 Python Microservice\nGenerate a production-ready FastAPI app"
        ):
            st.session_state.messages.append({
                "role": "user",
                "content": (
                    "Write a clean, production-ready FastAPI REST API "
                    "with authentication and CRUD endpoints in Python."
                )
            })
            st.rerun()

    with c2:
        if st.button(
            "🌐 Global Tech News\nGet today's top artificial intelligence breakthroughs"
        ):
            st.session_state.messages.append({
                "role": "user",
                "content": (
                    "What are the most recent major updates and breakthroughs "
                    "in artificial intelligence today?"
                )
            })
            st.session_state.web_search_enabled = True
            st.rerun()

    with c3:
        if st.button(
            "🧠 Deep Logical Analysis\nExplore quantum computing in cryptography"
        ):
            st.session_state.messages.append({
                "role": "user",
                "content": (
                    "Explain how Shor's algorithm in quantum computing poses "
                    "a challenge to RSA cryptography, and describe "
                    "post-quantum mitigation strategies."
                )
            })
            st.rerun()

    with c4:
        if st.button(
            "✍️ Executive Pitch\nDraft an executive summary proposal"
        ):
            st.session_state.messages.append({
                "role": "user",
                "content": (
                    "Draft a compelling executive pitch for deploying "
                    "AI-driven automation inside enterprise workflows."
                )
            })
            st.rerun()


# ==============================================================================
# 7. CHAT HISTORY DISPLAY
# ==============================================================================

chat_container = st.container()

with chat_container:

    for msg in st.session_state.messages:

        if msg["role"] == "user":

            st.chat_message(
                "user",
                avatar="👤"
            ).write(msg["content"])

        else:

            with st.chat_message(
                "assistant",
                avatar="✨"
            ):

                provider_display = msg.get(
                    "provider",
                    "Anis AI Engine"
                )

                # Safety protection:
                # Never allow None to reach string formatting/display.
                if not provider_display:
                    provider_display = "Anis AI Engine"

                st.markdown(
                    f'<span class="provider-badge">⚡ '
                    f'{str(provider_display)}</span>',
                    unsafe_allow_html=True
                )

                st.markdown(
                    msg.get("content", "")
                )


# ==============================================================================
# 8. INPUT PROCESSING & INFERENCE PIPELINE
# ==============================================================================

user_prompt = st.chat_input(
    "Ask Anis AI anything..."
)

if user_prompt:

    # --------------------------------------------------------------------------
    # 8.1 RENDER USER MESSAGE
    # --------------------------------------------------------------------------

    st.session_state.messages.append({
        "role": "user",
        "content": user_prompt
    })

    st.chat_message(
        "user",
        avatar="👤"
    ).write(user_prompt)


    # --------------------------------------------------------------------------
    # 8.2 ASSISTANT INFERENCE EXECUTION
    # --------------------------------------------------------------------------

    with st.chat_message(
        "assistant",
        avatar="✨"
    ):

        response_placeholder = st.empty()
        status_placeholder = st.empty()

        status_placeholder.markdown(
            "<small style='color: #818cf8;'>"
            "⚡ Anis AI is synthesizing response..."
            "</small>",
            unsafe_allow_html=True
        )

        final_prompt = user_prompt

        selected_engine = st.session_state.model_engine

        engine_label = "Anis Auto-Cascade Pro"

        task_type = classify_task(
            user_prompt
        )


        # ----------------------------------------------------------------------
        # 8.3 LIVE WEB SEARCH GROUNDING
        # ----------------------------------------------------------------------

        if (
            st.session_state.web_search_enabled
            or task_type == "search"
        ):

            status_placeholder.markdown(
                "<small style='color: #ec4899;'>"
                "🌐 Grounding with real-time web results..."
                "</small>",
                unsafe_allow_html=True
            )

            search_data = run_web_search(
                user_prompt
            )

            if search_data:

                final_prompt = (
                    f"{user_prompt}\n\n"
                    f"[Live Web Search Context]:\n"
                    f"{search_data}\n\n"
                    "Please generate an accurate, structured response "
                    "citing the context above."
                )


        # ----------------------------------------------------------------------
        # 8.4 RESULT INITIALIZATION
        # ----------------------------------------------------------------------

        result_text = None

        # This variable is also initialized safely so that a provider
        # function returning None cannot break the UI.
        used_provider = None

        # ----------------------------------------------------------------------
        # 8.5 AI PROVIDER ROUTING
        # ----------------------------------------------------------------------

        try:

            # ------------------------------------------------------------------
            # Gemini
            # ------------------------------------------------------------------

            if "Anis 2.0 Flash" in selected_engine:

                result_text = call_gemini(
                    final_prompt
                )

                engine_label = "Anis 2.0 Flash Engine"


            # ------------------------------------------------------------------
            # Cerebras
            # ------------------------------------------------------------------

            elif "Anis 3.3 Ultra Speed" in selected_engine:

                result_text = call_cerebras(
                    final_prompt
                )

                engine_label = "Anis 3.3 Ultra Speed Engine"


            # ------------------------------------------------------------------
            # Groq
            # ------------------------------------------------------------------

            elif "Anis 3.3 Versatile" in selected_engine:

                result_text = call_groq(
                    final_prompt
                )

                engine_label = "Anis 3.3 Versatile Engine"


            # ------------------------------------------------------------------
            # Mistral
            # ------------------------------------------------------------------

            elif "Anis Small Core" in selected_engine:

                result_text = call_mistral(
                    final_prompt
                )

                engine_label = "Anis Small Core Engine"


            # ------------------------------------------------------------------
            # OpenRouter
            # ------------------------------------------------------------------

            elif "Anis Meta-Llama 3.3" in selected_engine:

                result_text = call_openrouter(
                    final_prompt
                )

                engine_label = "Anis Meta-Llama 3.3 Engine"


            # ------------------------------------------------------------------
            # DEFAULT AUTONOMOUS CASCADE
            # ------------------------------------------------------------------

            else:

                cascade_res = run_text_ai_chain(
                    final_prompt,
                    task_type=task_type
                )

                # Never assume the helper returned a valid dictionary.
                if not isinstance(cascade_res, dict):
                    cascade_res = {}

                result_text = cascade_res.get(
                    "answer"
                )

                used_provider = cascade_res.get(
                    "provider_used"
                )

                # IMPORTANT:
                # provider_used can be None.
                # Do NOT call .capitalize() directly on it.
                if not used_provider:
                    used_provider = "Cascade Engine"

                used_provider = str(
                    used_provider
                ).strip()

                if not used_provider:
                    used_provider = "Cascade Engine"

                engine_label = (
                    f"Anis Auto-Cascade "
                    f"({used_provider.capitalize()})"
                )


            # ------------------------------------------------------------------
            # 8.6 CLEAN STATUS
            # ------------------------------------------------------------------

            status_placeholder.empty()
# ------------------------------------------------------------------
            # 8.7 RESULT VALIDATION & RESPONSE RENDERING
            # ------------------------------------------------------------------

            if result_text is not None:

                # Convert non-string responses safely.
                if not isinstance(result_text, str):
                    result_text = str(result_text)

                result_text = result_text.strip()


            # ------------------------------------------------------------------
            # 8.8 SUCCESS RESPONSE
            # ------------------------------------------------------------------

            if result_text:

                formatted_response = (
                    f'<span class="provider-badge">⚡ '
                    f'{str(engine_label).upper()}</span>\n\n'
                    f'{result_text}'
                )

                response_placeholder.markdown(
                    formatted_response,
                    unsafe_allow_html=True
                )

                st.session_state.messages.append({
                    "role": "assistant",
                    "content": result_text,
                    "provider": engine_label
                })


            # ------------------------------------------------------------------
            # 8.9 EMPTY RESPONSE FALLBACK
            # ------------------------------------------------------------------

            else:

                error_msg = (
                    "⚠️ **Anis AI is currently experiencing high demand.**\n\n"
                    "The selected AI provider did not return a response. "
                    "Please wait a brief moment and try your question again."
                )

                response_placeholder.warning(
                    error_msg
                )


        # ----------------------------------------------------------------------
        # 8.10 UNEXPECTED ERROR HANDLING
        # ----------------------------------------------------------------------

        except Exception as e:

            status_placeholder.empty()

            # Keep the application alive even when an individual provider
            # or helper function raises an exception.
            error_details = str(e).strip()

            if not error_details:
                error_details = "Unknown provider error."

            error_fallback = (
                "⚠️ **Anis AI temporary service interruption.**\n\n"
                f"Details: `{error_details}`\n\n"
                "Please hold on for a moment while the system refreshes "
                "and retry your prompt."
            )

            response_placeholder.error(
                error_fallback
            )


# ==============================================================================
# 9. FOOTER DISCLAIMER
# ==============================================================================

st.markdown("""
    <div class="footer-disclaimer">
        <b>Anis AI</b> can make mistakes. Please verify critical facts,
        financial, medical, or legal information from authoritative sources.
    </div>
""", unsafe_allow_html=True)
