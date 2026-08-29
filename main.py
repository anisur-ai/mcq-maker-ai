import os
import re
import streamlit as st
import streamlit.components.v1 as components

# Safe import for dotenv: Environment variable loader
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Import all necessary functions directly from helpers.py
from helpers import (
    smart_read_file,
    needs_web_search,
    smart_search,
    smart_scrape,
    select_model_by_task,
    build_ai_messages,
    format_sources,
    provider_aware_ai_fallback,
)

# =====================================================
# PAGE CONFIGURATION (DARK & FULLSCREEN)
# =====================================================
st.set_page_config(
    page_title="Anis AI",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =====================================================
# 3D ANIMATED CANVAS BACKGROUND INJECTION (JS/CANVAS)
# =====================================================
THREE_D_BACKGROUND = """
<div id="canvas-container" style="position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; z-index: -1; pointer-events: none; overflow: hidden; background: #08090d;">
    <canvas id="bg3d"></canvas>
</div>
<script>
(function() {
    const canvas = document.getElementById('bg3d');
    const ctx = canvas.getContext('2d');
    let width, height;
    let particles = [];
    const numParticles = 65;
    let angleX = 0.001;
    let angleY = 0.002;

    function resize() {
        width = window.innerWidth;
        height = window.innerHeight;
        canvas.width = width;
        canvas.height = height;
    }
    window.addEventListener('resize', resize);
    resize();

    // 3D Particle Generator (Spherical Distribution)
    for (let i = 0; i < numParticles; i++) {
        let theta = Math.random() * Math.PI * 2;
        let phi = Math.acos((Math.random() * 2) - 1);
        let radius = 280 + Math.random() * 140;

        particles.push({
            x: radius * Math.sin(phi) * Math.cos(theta),
            y: radius * Math.sin(phi) * Math.sin(theta),
            z: radius * Math.cos(phi),
            size: Math.random() * 2.5 + 1.2,
            color: ['#4285f4', '#9b72cf', '#d96570', '#38bdf8'][Math.floor(Math.random() * 4)]
        });
    }

    function rotateX(p, angle) {
        let cos = Math.cos(angle);
        let sin = Math.sin(angle);
        let y = p.y * cos - p.z * sin;
        let z = p.y * sin + p.z * cos;
        p.y = y;
        p.z = z;
    }

    function rotateY(p, angle) {
        let cos = Math.cos(angle);
        let sin = Math.sin(angle);
        let x = p.x * cos + p.z * sin;
        let z = -p.x * sin + p.z * cos;
        p.x = x;
        p.z = z;
    }

    function draw() {
        ctx.clearRect(0, 0, width, height);

        let cx = width / 2;
        let cy = height / 2;
        let fov = 450;

        let projected = [];

        for (let i = 0; i < particles.length; i++) {
            let p = particles[i];
            rotateX(p, angleX);
            rotateY(p, angleY);

            let scale = fov / (fov + p.z + 300);
            let px = p.x * scale + cx;
            let py = p.y * scale + cy;

            projected.push({ x: px, y: py, scale: scale, p: p });
        }

        // Draw 3D Connecting Lines
        for (let i = 0; i < projected.length; i++) {
            for (let j = i + 1; j < projected.length; j++) {
                let p1 = projected[i];
                let p2 = projected[j];
                let dx = p1.x - p2.x;
                let dy = p1.y - p2.y;
                let dist = Math.sqrt(dx * dx + dy * dy);

                if (dist < 130) {
                    ctx.beginPath();
                    ctx.moveTo(p1.x, p1.y);
                    ctx.lineTo(p2.x, p2.y);
                    let alpha = (1 - dist / 130) * 0.15 * p1.scale;
                    ctx.strokeStyle = `rgba(155, 114, 207, ${alpha})`;
                    ctx.lineWidth = 0.9;
                    ctx.stroke();
                }
            }
        }

        // Draw Nodes
        for (let i = 0; i < projected.length; i++) {
            let item = projected[i];
            ctx.beginPath();
            ctx.arc(item.x, item.y, item.p.size * item.scale, 0, Math.PI * 2);
            ctx.fillStyle = item.p.color;
            ctx.shadowBlur = 12;
            ctx.shadowColor = item.p.color;
            ctx.globalAlpha = Math.min(Math.max(item.scale * 0.9, 0.2), 1);
            ctx.fill();
            ctx.globalAlpha = 1.0;
        }

        requestAnimationFrame(draw);
    }
    draw();
})();
</script>
"""
components.html(THREE_D_BACKGROUND, height=0, width=0)

# =====================================================
# CUSTOM CSS: ULTRA MODERN 3D DARK THEME
# =====================================================
ANIS_AI_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
    color: #e6edf3;
}

/* Make App Body Transparent so 3D Canvas shines through */
.stApp {
    background: transparent !important;
}

/* Sidebar with 3D Frosted Glass Effect */
[data-testid="stSidebar"] {
    background: rgba(12, 14, 20, 0.75) !important;
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    border-right: 1px solid rgba(255, 255, 255, 0.08);
    box-shadow: 10px 0 35px rgba(0, 0, 0, 0.6);
}

[data-testid="stSidebar"] hr {
    border-color: rgba(255, 255, 255, 0.08);
}

header[data-testid="stHeader"] {
    background: transparent;
}

/* Anis AI 3D Heading */
.anis-title {
    font-size: 3.5rem;
    font-weight: 800;
    letter-spacing: -0.03em;
    background: linear-gradient(135deg, #60a5fa 0%, #c084fc 45%, #f472b6 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 0.2rem;
    line-height: 1.2;
    filter: drop-shadow(0 6px 20px rgba(96, 165, 250, 0.3));
}

.anis-subtitle {
    font-size: 1.3rem;
    font-weight: 400;
    color: #94a3b8;
    margin-bottom: 2rem;
}

/* Chat Messages */
[data-testid="stChatMessage"] {
    background-color: transparent;
    border: none;
    padding: 0.9rem 0;
}

/* User Message Pill */
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) {
    background: linear-gradient(135deg, rgba(30, 36, 51, 0.85) 0%, rgba(23, 27, 38, 0.85) 100%);
    border: 1px solid rgba(255, 255, 255, 0.1);
    backdrop-filter: blur(10px);
    border-radius: 20px 20px 4px 20px;
    padding: 14px 22px;
    margin: 8px 0 16px auto;
    max-width: 80%;
    width: fit-content;
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
}

/* Assistant Message */
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarAssistant"]) {
    background: transparent;
    padding-left: 0;
}

/* Chat Input Bar */
[data-testid="stChatInput"] {
    background: rgba(18, 20, 29, 0.85) !important;
    border: 1px solid rgba(255, 255, 255, 0.12) !important;
    border-radius: 26px !important;
    backdrop-filter: blur(16px);
    box-shadow: 0 10px 40px rgba(0, 0, 0, 0.6) !important;
}

[data-testid="stChatInput"]:focus-within {
    border-color: #60a5fa !important;
    box-shadow: 0 10px 40px rgba(96, 165, 250, 0.3) !important;
}

[data-testid="stChatInput"] textarea {
    color: #f1f5f9;
}

/* History items in Sidebar */
.history-item {
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(255, 255, 255, 0.05);
    border-radius: 10px;
    padding: 9px 12px;
    margin-bottom: 7px;
    font-size: 0.88rem;
    color: #cbd5e1;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    transition: all 0.2s ease;
}
.history-item:hover {
    background: rgba(255, 255, 255, 0.08);
    border-color: rgba(96, 165, 250, 0.35);
    transform: translateX(3px);
}

/* Buttons */
.stButton > button {
    background: linear-gradient(135deg, rgba(30, 34, 48, 0.8) 0%, rgba(21, 24, 33, 0.8) 100%);
    color: #e2e8f0;
    border: 1px solid rgba(255, 255, 255, 0.12);
    border-radius: 14px;
    font-weight: 500;
    transition: all 0.3s ease;
    backdrop-filter: blur(8px);
}

.stButton > button:hover {
    border-color: #60a5fa;
    color: #ffffff;
    box-shadow: 0 6px 22px rgba(96, 165, 250, 0.25);
    transform: translateY(-1px);
}
</style>
"""
st.markdown(ANIS_AI_CSS, unsafe_allow_html=True)

# =====================================================
# CONSTANTS & UTILITIES
# =====================================================
DEFAULT_SYSTEM_PROMPT = (
    "You are Anis AI, a helpful, highly knowledgeable, polite, and advanced AI assistant. "
    "Format all answers with clean Markdown, bullet points, and code blocks where appropriate. "
    "Use any provided document context or web search results precisely."
)

URL_REGEX = r"https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+[^\s]*"

def get_key(key_name: str) -> str:
    """Fetch API keys securely from Session State, Streamlit Secrets, or OS Environment."""
    if st.session_state.get(key_name):
        return st.session_state[key_name].strip()
    try:
        if key_name in st.secrets:
            return str(st.secrets[key_name]).strip()
    except Exception:
        pass
    return os.getenv(key_name, "").strip()


# Load API Keys Silently
keys_dict = {
    "gemini": get_key("GEMINI_API_KEY"),
    "groq": get_key("GROQ_API_KEY"),
    "mistral": get_key("MISTRAL_API_KEY"),
    "openrouter": get_key("OPENROUTER_API_KEY"),
}

serper_key = get_key("SERPER_API_KEY")
tavily_key = get_key("TAVILY_API_KEY")
jina_key = get_key("JINA_API_KEY")
firecrawl_key = get_key("FIRECRAWL_API_KEY")
ocr_key = get_key("OCR_API_KEY")


# =====================================================
# SESSION STATE INITIALIZATION
# =====================================================
if "messages" not in st.session_state:
    st.session_state.messages = []


# =====================================================
# SIDEBAR: CHAT HISTORY (CLEAN ENGLISH UI)
# =====================================================
with st.sidebar:
    st.markdown("### 💬 **Chat History**")
    
    if st.button("➕ New Chat", use_container_width=True):
        st.session_state.messages = []
        st.session_state.pop("attached_file", None)
        st.rerun()

    st.markdown("---")

    # Display past conversation queries
    user_queries = [m["content"] for m in st.session_state.messages if m["role"] == "user"]
    if user_queries:
        for query in reversed(user_queries[-15:]):
            st.markdown(f'<div class="history-item">💭 {query}</div>', unsafe_allow_html=True)
    else:
        st.caption("No conversations yet.")

    st.markdown("---")
    force_web_search = st.checkbox("🌐 Always Search Live Web", value=False)


# =====================================================
# ANIS AI HERO SCREEN (ON FRESH START)
# =====================================================
if not st.session_state.messages:
    st.markdown('<div class="anis-title">Anis AI</div>', unsafe_allow_html=True)
    st.markdown('<div class="anis-subtitle">Hello, Explorer! How can I help you today?</div>', unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if st.button("📝 Create Quiz\nGenerate questions with answers", use_container_width=True):
            st.session_state.temp_prompt = "Create a 5-question multiple choice quiz on artificial intelligence with answer keys and explanations."
    with col2:
        if st.button("🔍 Live Search\nGet real-time updates from web", use_container_width=True):
            st.session_state.temp_prompt = "What are the latest scientific discoveries and tech news today?"
    with col3:
        if st.button("💻 Debug & Code\nAnalyze and write Python code", use_container_width=True):
            st.session_state.temp_prompt = "Write a high-performance Python script to parse large JSON files concurrently."
    with col4:
        if st.button("📄 Document QA\nExtract key insights from files", use_container_width=True):
            st.session_state.temp_prompt = "Summarize the key points of the uploaded file in clear bullet points."


# =====================================================
# RENDER CHAT HISTORY
# =====================================================
for msg in st.session_state.messages:
    if msg["role"] == "user":
        with st.chat_message("user", avatar="👤"):
            st.markdown(msg["content"])
    elif msg["role"] == "assistant":
        with st.chat_message("assistant", avatar="✨"):
            st.markdown(msg["content"])


# =====================================================
# ATTACHMENT BAR (PLUS POPOVER NEXT TO CHAT)
# =====================================================
action_col1, action_col2 = st.columns([1.2, 8.8])

uploaded_file = None
quick_send_trigger = False

with action_col1:
    with st.popover("➕ Attach", use_container_width=True):
        st.markdown("**Upload Document or Image**")
        uploaded_file = st.file_uploader(
            "Upload file",
            type=["pdf", "docx", "txt", "png", "jpg", "jpeg", "webp"],
            label_visibility="collapsed",
            key="file_uploader",
        )
        if uploaded_file is not None:
            st.success(f"📎 {uploaded_file.name}")
            if st.button("🚀 Analyze / Send File", use_container_width=True):
                quick_send_trigger = True

with action_col2:
    if uploaded_file is not None:
        st.caption(f"📎 Ready to send: **{uploaded_file.name}** (Type prompt below or click 'Analyze / Send File')")


# =====================================================
# PROCESS USER INTERACTION
# =====================================================
temp_prompt = st.session_state.pop("temp_prompt", None)
typed_prompt = st.chat_input("Ask Anis AI or type a prompt...")

# Determine active prompt
user_prompt = None
if quick_send_trigger:
    user_prompt = f"Please analyze and explain the uploaded file: {uploaded_file.name}"
elif typed_prompt:
    user_prompt = typed_prompt
elif temp_prompt:
    user_prompt = temp_prompt


if user_prompt:
    # 1. Show user message
    st.chat_message("user", avatar="👤").markdown(user_prompt)
    st.session_state.messages.append({"role": "user", "content": user_prompt})

    # 2. Extract Document / Image Data
    file_context = ""
    if uploaded_file is not None:
        with st.spinner("✨ Anis AI is reading your file/image..."):
            file_context = smart_read_file(uploaded_file, ocr_api_key=ocr_key)

    # 3. Web Search & Scraping
    external_context = ""
    sources_list = []
    urls_in_prompt = re.findall(URL_REGEX, user_prompt)

    with st.spinner("✨ Anis AI is researching..."):
        if urls_in_prompt:
            target_url = urls_in_prompt[0]
            scraped_content, scraped_sources = smart_scrape(
                url=target_url,
                firecrawl_key=firecrawl_key,
                jina_key=jina_key,
            )
            external_context += scraped_content
            sources_list.extend(scraped_sources)

        elif force_web_search or needs_web_search(user_prompt, groq_api_key=keys_dict.get("groq")):
            search_content, search_sources = smart_search(
                query=user_prompt,
                serper_key=serper_key,
                tavily_key=tavily_key,
                jina_key=jina_key,
            )
            external_context += search_content
            sources_list.extend(search_sources)

    # 4. Automatic Model Selection (Internal Routing)
    combined_context = f"{file_context}\n{external_context}"
    router_info = select_model_by_task(user_prompt, context_text=combined_context)

    # 5. Build AI Message Payload
    formatted_ai_messages = build_ai_messages(
        system_prompt=DEFAULT_SYSTEM_PROMPT,
        managed_messages=st.session_state.messages[:-1],
        user_prompt=user_prompt,
        file_context=file_context,
        external_context=external_context,
    )

    # 6. Stream Assistant Response (NO API BADGE)
    with st.chat_message("assistant", avatar="✨"):
        response_container = st.empty()
        full_response = ""

        stream_generator = provider_aware_ai_fallback(
            keys_dict=keys_dict,
            router_info=router_info,
            messages=formatted_ai_messages,
        )

        has_failed = False
        for chunk in stream_generator:
            if chunk == "ERROR_ALL_FAILED":
                has_failed = True
                break
            full_response += chunk
            response_container.markdown(full_response + " ▌")

        # Fallback polite error message
        if has_failed:
            polite_message = "Sorry, please wait a moment. The problem is being fixed."
            response_container.info(f"✨ {polite_message}")
            full_response = polite_message
        else:
            if sources_list:
                full_response += format_sources(sources_list)
            response_container.markdown(full_response)

    # 7. Save Assistant Message to History & Refresh Sidebar
    st.session_state.messages.append({"role": "assistant", "content": full_response})
    st.rerun()
