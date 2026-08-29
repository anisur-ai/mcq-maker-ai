import os
import re
import uuid
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
# PAGE CONFIGURATION
# =====================================================
st.set_page_config(
    page_title="Anis AI",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =====================================================
# REAL 3D ANIMATED CANVAS (DOM INJECTION)
# =====================================================
REAL_3D_BG_INJECTOR = """
<script>
(function() {
    const parentDoc = window.parent.document;
    if (parentDoc.getElementById('anis-3d-canvas')) return;

    const canvas = parentDoc.createElement('canvas');
    canvas.id = 'anis-3d-canvas';
    canvas.style.position = 'fixed';
    canvas.style.top = '0';
    canvas.style.left = '0';
    canvas.style.width = '100vw';
    canvas.style.height = '100vh';
    canvas.style.zIndex = '0';
    canvas.style.pointerEvents = 'none';
    canvas.style.opacity = '0.75';
    parentDoc.body.prepend(canvas);

    const ctx = canvas.getContext('2d');
    let width, height;
    let particles = [];
    const numParticles = 70;
    let angleX = 0.0015;
    let angleY = 0.0025;

    function resize() {
        width = window.parent.innerWidth;
        height = window.parent.innerHeight;
        canvas.width = width;
        canvas.height = height;
    }
    window.parent.addEventListener('resize', resize);
    resize();

    // 3D Particles in a sphere cluster
    for (let i = 0; i < numParticles; i++) {
        let theta = Math.random() * Math.PI * 2;
        let phi = Math.acos((Math.random() * 2) - 1);
        let radius = 260 + Math.random() * 160;

        particles.push({
            x: radius * Math.sin(phi) * Math.cos(theta),
            y: radius * Math.sin(phi) * Math.sin(theta),
            z: radius * Math.cos(phi),
            size: Math.random() * 2.6 + 1.2,
            color: ['#4285f4', '#a855f7', '#ec4899', '#38bdf8'][Math.floor(Math.random() * 4)]
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
        let fov = 420;
        let projected = [];

        for (let i = 0; i < particles.length; i++) {
            let p = particles[i];
            rotateX(p, angleX);
            rotateY(p, angleY);

            let scale = fov / (fov + p.z + 320);
            let px = p.x * scale + cx;
            let py = p.y * scale + cy;
            projected.push({ x: px, y: py, scale: scale, p: p });
        }

        // Connect 3D vertices
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
                    let alpha = (1 - dist / 130) * 0.2 * p1.scale;
                    ctx.strokeStyle = `rgba(168, 85, 247, ${alpha})`;
                    ctx.lineWidth = 0.9;
                    ctx.stroke();
                }
            }
        }

        // Draw 3D nodes
        for (let i = 0; i < projected.length; i++) {
            let item = projected[i];
            ctx.beginPath();
            ctx.arc(item.x, item.y, item.p.size * item.scale, 0, Math.PI * 2);
            ctx.fillStyle = item.p.color;
            ctx.shadowBlur = 10;
            ctx.shadowColor = item.p.color;
            ctx.globalAlpha = Math.min(Math.max(item.scale * 0.9, 0.25), 1);
            ctx.fill();
            ctx.globalAlpha = 1.0;
        }

        window.requestAnimationFrame(draw);
    }
    draw();
})();
</script>
"""
components.html(REAL_3D_BG_INJECTOR, height=0, width=0)

# =====================================================
# MODERN 3D OBSIDIAN CSS THEME
# =====================================================
ANIS_AI_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
    color: #e6edf3;
}

/* Ensure background transparency for 3D canvas */
.stApp {
    background: #090a0f !important;
    color: #e6edf3;
}

/* 3D Glassmorphic Sidebar */
[data-testid="stSidebar"] {
    background: rgba(13, 15, 22, 0.85) !important;
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    border-right: 1px solid rgba(255, 255, 255, 0.08);
    box-shadow: 10px 0 35px rgba(0, 0, 0, 0.6);
    z-index: 10;
}

[data-testid="stSidebar"] hr {
    border-color: rgba(255, 255, 255, 0.08);
}

header[data-testid="stHeader"] {
    background: transparent !important;
}

/* Anis AI Header */
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

/* User Message Bubble */
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) {
    background: linear-gradient(135deg, rgba(30, 36, 51, 0.9) 0%, rgba(23, 27, 38, 0.9) 100%);
    border: 1px solid rgba(255, 255, 255, 0.1);
    backdrop-filter: blur(12px);
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

/* Chat Input Bar Styling with Attachment */
[data-testid="stChatInput"] {
    background: rgba(18, 20, 29, 0.9) !important;
    border: 1px solid rgba(255, 255, 255, 0.14) !important;
    border-radius: 26px !important;
    backdrop-filter: blur(16px);
    box-shadow: 0 10px 40px rgba(0, 0, 0, 0.6) !important;
}

[data-testid="stChatInput"]:focus-within {
    border-color: #60a5fa !important;
    box-shadow: 0 10px 40px rgba(96, 165, 250, 0.3) !important;
}

/* Sidebar History Buttons */
[data-testid="stSidebar"] .stButton > button {
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(255, 255, 255, 0.06);
    color: #cbd5e1;
    border-radius: 12px;
    padding: 8px 14px;
    font-size: 0.88rem;
    text-align: left;
    display: block;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    transition: all 0.2s ease;
}

[data-testid="stSidebar"] .stButton > button:hover {
    background: rgba(255, 255, 255, 0.08);
    border-color: #60a5fa;
    color: #ffffff;
    transform: translateX(3px);
}
</style>
"""
st.markdown(ANIS_AI_CSS, unsafe_allow_html=True)

# =====================================================
# CONSTANTS & UTILITIES
# =====================================================
DEFAULT_SYSTEM_PROMPT = (
    "You are Anis AI, an advanced, polite, and highly capable AI assistant. "
    "Format all answers with clean Markdown, bullet points, and code blocks where appropriate. "
    "Use any provided document context or web search results precisely."
)

URL_REGEX = r"https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+[^\s]*"

def get_key(key_name: str) -> str:
    """Fetch API keys securely from Session State, Secrets, or OS Environment."""
    if st.session_state.get(key_name):
        return st.session_state[key_name].strip()
    try:
        if key_name in st.secrets:
            return str(st.secrets[key_name]).strip()
    except Exception:
        pass
    return os.getenv(key_name, "").strip()


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
# MULTI-SESSION CHAT HISTORY STATE
# =====================================================
if "sessions" not in st.session_state:
    initial_id = str(uuid.uuid4())
    st.session_state.sessions = {
        initial_id: {
            "title": "New Chat",
            "messages": []
        }
    }
    st.session_state.current_session_id = initial_id

if "current_session_id" not in st.session_state or st.session_state.current_session_id not in st.session_state.sessions:
    st.session_state.current_session_id = list(st.session_state.sessions.keys())[0]

current_chat = st.session_state.sessions[st.session_state.current_session_id]
messages = current_chat["messages"]


# =====================================================
# SIDEBAR: CLICKABLE CHAT HISTORY (INTERACTIVE)
# =====================================================
with st.sidebar:
    st.markdown("### 💬 **Chat History**")
    
    if st.button("➕ New Chat", use_container_width=True):
        new_id = str(uuid.uuid4())
        st.session_state.sessions[new_id] = {
            "title": "New Chat",
            "messages": []
        }
        st.session_state.current_session_id = new_id
        st.rerun()

    st.markdown("---")

    # Render each saved conversation as a clickable item
    for sess_id, sess_data in list(reversed(list(st.session_state.sessions.items()))):
        title = sess_data["title"]
        is_active = (sess_id == st.session_state.current_session_id)
        btn_label = f"✨ {title}" if is_active else f"💭 {title}"

        if st.button(btn_label, key=f"sess_{sess_id}", use_container_width=True):
            st.session_state.current_session_id = sess_id
            st.rerun()

    st.markdown("---")
    force_web_search = st.checkbox("🌐 Always Search Live Web", value=False)


# =====================================================
# ANIS AI HERO SCREEN (WHEN CHAT IS EMPTY)
# =====================================================
if not messages:
    st.markdown('<div class="anis-title">Anis AI</div>', unsafe_allow_html=True)
    st.markdown('<div class="anis-subtitle">Hello, Explorer! How can I assist you today?</div>', unsafe_allow_html=True)

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
# RENDER CHAT MESSAGES
# =====================================================
for msg in messages:
    if msg["role"] == "user":
        with st.chat_message("user", avatar="👤"):
            st.markdown(msg["content"])
    elif msg["role"] == "assistant":
        with st.chat_message("assistant", avatar="✨"):
            st.markdown(msg["content"])


# =====================================================
# CHAT INPUT WITH BUILT-IN FILE/IMAGE ATTACHMENT (+)
# =====================================================
temp_prompt = st.session_state.pop("temp_prompt", None)

try:
    # Streamlit native input with attached '+' upload button
    user_input = st.chat_input(
        "Ask Anis AI or attach file...",
        accept_file=True,
        file_type=["png", "jpg", "jpeg", "webp", "pdf", "docx", "txt"],
    )
except TypeError:
    # Fallback for earlier versions of Streamlit
    user_input = st.chat_input("Ask Anis AI or type a prompt...")

# Extract Text & File from input
prompt_text = None
attached_file = None

if user_input:
    if hasattr(user_input, "text") or isinstance(user_input, dict):
        prompt_text = getattr(user_input, "text", "") or user_input.get("text", "")
        files = getattr(user_input, "files", []) or user_input.get("files", [])
        if files:
            attached_file = files[0]
    elif isinstance(user_input, str):
        prompt_text = user_input

if not prompt_text and temp_prompt:
    prompt_text = temp_prompt

# If only a file was attached without typing text
if attached_file and not prompt_text:
    prompt_text = f"Please analyze and explain the uploaded file: {attached_file.name}"


# =====================================================
# PROCESS USER INTERACTION
# =====================================================
if prompt_text:
    # Update Session Title if it is the first prompt
    if len(messages) == 0:
        current_chat["title"] = prompt_text[:32] + ("..." if len(prompt_text) > 32 else "")

    # 1. Show user message
    st.chat_message("user", avatar="👤").markdown(prompt_text)
    messages.append({"role": "user", "content": prompt_text})

    # 2. Extract Document/Image Data
    file_context = ""
    if attached_file is not None:
        with st.spinner("✨ Anis AI is reading and analyzing your file/image..."):
            file_context = smart_read_file(attached_file, ocr_api_key=ocr_key)

    # 3. Web Search & Scraping
    external_context = ""
    sources_list = []
    urls_in_prompt = re.findall(URL_REGEX, prompt_text)

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

        elif force_web_search or needs_web_search(prompt_text, groq_api_key=keys_dict.get("groq")):
            search_content, search_sources = smart_search(
                query=prompt_text,
                serper_key=serper_key,
                tavily_key=tavily_key,
                jina_key=jina_key,
            )
            external_context += search_content
            sources_list.extend(search_sources)

    # 4. Automatic Model Routing (Internal)
    combined_context = f"{file_context}\n{external_context}"
    router_info = select_model_by_task(prompt_text, context_text=combined_context)

    # 5. Build AI Message Payload
    formatted_ai_messages = build_ai_messages(
        system_prompt=DEFAULT_SYSTEM_PROMPT,
        managed_messages=messages[:-1],
        user_prompt=prompt_text,
        file_context=file_context,
        external_context=external_context,
    )

    # 6. Stream Assistant Response (Clean Response, NO API BADGE)
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

        # Polite fallback handler
        if has_failed:
            polite_message = "Sorry, please wait a moment. The problem is being fixed."
            response_container.info(f"✨ {polite_message}")
            full_response = polite_message
        else:
            if sources_list:
                full_response += format_sources(sources_list)
            response_container.markdown(full_response)

    # 7. Save Assistant Message to Active Session & Refresh
    messages.append({"role": "assistant", "content": full_response})
    st.rerun()
