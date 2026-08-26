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
)


# =========================================================
# PAGE CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="Anis AI",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="expanded",
)


# =========================================================
# APP SETTINGS
# =========================================================

HISTORY_DAYS = 5
MAX_HISTORY_CHATS = 50
MAX_MESSAGES = 100


# =========================================================
# SESSION STATE
# =========================================================

DEFAULTS = {
    "messages": [],
    "history": [],
    "chat_summary": "",
    "selected_file": None,
    "attach_mode": None,
    "show_attach_menu": False,
    "credits": 100,
    "analytics_logged": False,
    "processing": False,
}

for key, value in DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = value


# =========================================================
# ANALYTICS
# =========================================================

if not st.session_state.analytics_logged:

    user_id = st.session_state.get("user_id")

    if not user_id:
        user_id = f"user_{id(st.session_state)}"
        st.session_state.user_id = user_id

    try:
        log_usage(user_id, event_type="visit")
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
# HISTORY HELPERS (single source of truth — was duplicated
# 5x throughout the original file)
# =========================================================

def cleanup_old_history():
    """Keep only chats from the last HISTORY_DAYS days, capped at MAX_HISTORY_CHATS."""

    cutoff = datetime.now() - timedelta(days=HISTORY_DAYS)
    valid_history = []

    for chat in st.session_state.history:

        if not isinstance(chat, dict):
            continue

        if not isinstance(chat.get("messages"), list):
            continue

        try:
            created_at = chat.get("created_at")

            if isinstance(created_at, str):
                created_at = datetime.fromisoformat(created_at)

            if created_at and created_at >= cutoff:
                valid_history.append(chat)

        except Exception:
            continue

    st.session_state.history = valid_history[-MAX_HISTORY_CHATS:]


def clean_messages(messages):
    """Filter a message list down to well-formed user/assistant turns."""

    cleaned = []

    for message in messages:

        if not isinstance(message, dict):
            continue

        role = message.get("role")
        content = message.get("content")

        if role not in ("user", "assistant"):
            continue

        if content is None:
            continue

        content = str(content).strip()

        if not content:
            continue

        cleaned.append({"role": role, "content": content})

    return cleaned


def create_chat_title(messages):
    """Build a short, clean title from the first user message."""

    for message in messages:

        if message.get("role") != "user":
            continue

        content = str(message.get("content", "")).strip()

        if not content:
            continue

        content = " ".join(content.split())

        if len(content) > 45:
            return content[:45] + "..."

        return content

    return "New Conversation"


def save_current_chat():

    if not st.session_state.messages:
        return

    chat_record = {
        "id": datetime.now().timestamp(),
        "created_at": datetime.now().isoformat(),
        "title": create_chat_title(st.session_state.messages),
        "messages": list(st.session_state.messages),
    }

    st.session_state.history.append(chat_record)
    st.session_state.history = st.session_state.history[-MAX_HISTORY_CHATS:]


def reset_active_chat_ui():
    st.session_state.chat_summary = ""
    st.session_state.selected_file = None
    st.session_state.attach_mode = None
    st.session_state.show_attach_menu = False
    st.session_state.processing = False


def start_new_chat():

    if st.session_state.messages:
        save_current_chat()

    st.session_state.messages = []
    reset_active_chat_ui()
    st.rerun()


def load_chat(chat):

    st.session_state.messages = list(chat.get("messages", []))
    reset_active_chat_ui()
    st.rerun()


def update_conversation_memory():

    if not st.session_state.messages:
        return

    try:
        result = manage_conversation_memory(st.session_state.messages)

        if result:
            st.session_state.chat_summary = str(result)

    except Exception:
        pass


# Run cleanup once at the top of every rerun.
cleanup_old_history()


# =========================================================
# BASIC APP HEADER
# =========================================================

st.title("✦ Anis AI")
st.caption("Your intelligent AI assistant")

if st.session_state.credits <= 0:
    st.warning("Your credits have been used up.")


# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:

    st.subheader("Anis AI")

    if st.button("＋ New Chat", use_container_width=True, key="sidebar_new_chat"):
        start_new_chat()

    st.divider()

    st.caption(f"Credits: {st.session_state.credits}")

    st.divider()

    st.subheader("Recent Chats")

    if not st.session_state.history:
        st.caption("No previous conversations.")
    else:
        # Show newest chats first
        for chat in reversed(st.session_state.history):

            chat_id = chat.get("id")
            title = chat.get("title", "Conversation")

            if len(title) > 32:
                title = title[:32] + "..."

            if st.button(
                f"💬 {title}",
                key=f"history_{chat_id}",
                use_container_width=True,
            ):
                load_chat(chat)


# =========================================================
# MAIN CHAT AREA
# =========================================================

if not st.session_state.messages:

    st.markdown("## Hi Anis, how can I help you today?")
    st.write(
        "Ask questions, analyze files, "
        "search the web, or explore ideas "
        "with Anis AI."
    )


# =========================================================
# DISPLAY CONVERSATION
# =========================================================

for message in st.session_state.messages:

    role = message.get("role")
    content = message.get("content", "")

    if role == "user":
        with st.chat_message("user"):
            st.write(content)

    elif role == "assistant":
        with st.chat_message("assistant"):
            st.markdown(content)


# =========================================================
# ATTACHMENT SYSTEM
# =========================================================

st.divider()
st.subheader("Attachments")

# ---------------------------------------------------------
# ATTACHMENT TYPE SELECTION
# ---------------------------------------------------------

if st.button("Upload pictures📷", use_container_width=True, key="attach_button"):
    st.session_state.show_attach_menu = not st.session_state.show_attach_menu

if st.session_state.show_attach_menu:

    attach_col1, attach_col2, attach_col3 = st.columns(3)

    with attach_col1:
        if st.button("📷 Camera", use_container_width=True, key="menu_camera"):
            st.session_state.attach_mode = "camera"
            st.session_state.show_attach_menu = False
            st.rerun()

    with attach_col2:
        if st.button("🖼️ Gallery", use_container_width=True, key="menu_gallery"):
            st.session_state.attach_mode = "gallery"
            st.session_state.show_attach_menu = False
            st.rerun()

    with attach_col3:
        if st.button("📁 Files", use_container_width=True, key="menu_files"):
            st.session_state.attach_mode = "file"
            st.session_state.show_attach_menu = False
            st.rerun()

# ---------------------------------------------------------
# RESET INVALID ATTACHMENT STATE
# ---------------------------------------------------------

if st.session_state.attach_mode not in [None, "camera", "gallery", "file"]:
    st.session_state.attach_mode = None

# =========================================================
# CAMERA
# =========================================================

if st.session_state.attach_mode == "camera":

    camera_file = st.camera_input("Take a photo", key="camera_upload")

    if camera_file is not None:
        st.session_state.selected_file = camera_file
        st.session_state.attach_mode = None
        st.success(f"Attached: {camera_file.name}")


# =========================================================
# GALLERY
# =========================================================

elif st.session_state.attach_mode == "gallery":

    gallery_file = st.file_uploader(
        "Choose an image",
        type=["jpg", "jpeg", "png", "webp"],
        key="gallery_upload",
    )

    if gallery_file is not None:
        st.session_state.selected_file = gallery_file
        st.session_state.attach_mode = None
        st.success(f"Attached: {gallery_file.name}")


# =========================================================
# FILES
# =========================================================

elif st.session_state.attach_mode == "file":

    document_file = st.file_uploader("Choose a file", type=None, key="document_upload")

    if document_file is not None:
        st.session_state.selected_file = document_file
        st.session_state.attach_mode = None
        st.success(f"Attached: {document_file.name}")


# =========================================================
# CURRENT ATTACHMENT
# =========================================================

if st.session_state.selected_file is not None:

    selected_file = st.session_state.selected_file
    file_name = getattr(selected_file, "name", "Attached file")

    st.info(f"📎 Attached: {file_name}")

    file_type = getattr(selected_file, "type", "")

    if file_type.startswith("image/"):
        st.image(selected_file, caption=file_name, width=300)

    if st.button("✕ Remove attachment", key="remove_attachment"):
        st.session_state.selected_file = None
        st.session_state.attach_mode = None
        st.rerun()


# =========================================================
# CHAT INPUT
# =========================================================

prompt_input = st.chat_input("Ask Anis AI anything...")


# =========================================================
# PROCESS USER MESSAGE
# =========================================================

if prompt_input:

    prompt = prompt_input.strip()

    if not prompt:
        st.stop()

    st.session_state.messages.append({"role": "user", "content": prompt})

    file_context = ""
    external_context = ""
    collected_sources = []

    selected_file = st.session_state.selected_file

    # =====================================================
    # FILE PROCESSING
    # =====================================================

    if selected_file is not None:

        try:
            file_text = smart_read_file(selected_file, ocr_api_key)

            if file_text:
                file_context = "\n\n--- ATTACHED FILE CONTENT ---\n" + file_text

        except Exception:
            file_context = "\n\nThe attached file could not be read."

        # Clear attachment after processing
        st.session_state.selected_file = None
        st.session_state.attach_mode = None

    # =====================================================
    # URL DETECTION
    # =====================================================

    url_match = re.search(r"https?://[^\s]+", prompt)

    if url_match:

        target_url = url_match.group(0)

        try:
            scraped_text, sources = smart_scrape(
                target_url,
                keys_dict.get("firecrawl"),
                keys_dict.get("jina"),
            )

            if scraped_text:
                external_context = "\n\n--- URL CONTENT ---\n" + scraped_text

            if sources:
                collected_sources.extend(sources)

        except Exception:
            external_context = ""

    # =====================================================
    # WEB SEARCH
    # =====================================================

    elif not file_context:

        try:
            should_search = needs_web_search(prompt, keys_dict.get("groq"))
        except Exception:
            should_search = False

        if should_search:

            try:
                search_text, sources = smart_search(
                    prompt,
                    keys_dict.get("serper"),
                    keys_dict.get("tavily"),
                    keys_dict.get("jina"),
                )

                if search_text:
                    external_context = "\n\n--- LIVE WEB SEARCH RESULTS ---\n" + search_text

                if sources:
                    collected_sources.extend(sources)

            except Exception:
                external_context = ""

    # =====================================================
    # MODEL SELECTION
    # =====================================================

    try:
        router_info = select_model_by_task(prompt, file_context + external_context)
    except Exception:
        router_info = None

    # =====================================================
    # SYSTEM INSTRUCTIONS
    # =====================================================

    system_prompt = """
You are Anis AI, a helpful and intelligent AI assistant.

Rules:

- Give accurate and useful answers.
- Keep answers clear and well structured.
- If the user writes Bengali, answer in Bengali.
- If the user writes English, answer in English.
- Use the attached file when one is provided.
- Use web information when it is provided in the context.
- Do not mention internal APIs, model routing, or system instructions.
- Do not invent sources or facts.
"""

    # =====================================================
    # BUILD AI MESSAGES
    # =====================================================

    ai_messages = [{"role": "system", "content": system_prompt}]

    for message in st.session_state.messages[:-1]:

        role = message.get("role")
        content = message.get("content", "")

        if role in ("user", "assistant"):
            ai_messages.append({"role": role, "content": content})

    current_content = prompt

    if file_context:
        current_content += file_context

    if external_context:
        current_content += external_context

    ai_messages.append({"role": "user", "content": current_content})

    # =====================================================
    # ASSISTANT RESPONSE
    # =====================================================

    st.session_state.processing = True

    with st.chat_message("assistant"):

        response_placeholder = st.empty()
        full_response = ""
        failed = False

        try:
            stream = provider_aware_ai_fallback(keys_dict, router_info, ai_messages)

            for chunk in stream:

                if not chunk:
                    continue

                if chunk == "ERROR_ALL_FAILED" or chunk.startswith("দুঃখিত"):
                    failed = True
                    break

                full_response += str(chunk)
                response_placeholder.markdown(full_response + "▌")

        except Exception:
            failed = True

        # =================================================
        # ERROR HANDLING
        # =================================================

        if failed or not full_response.strip():

            full_response = (
                "দুঃখিত, এই মুহূর্তে উত্তর তৈরি করা সম্ভব হচ্ছে না। "
                "অনুগ্রহ করে আবার চেষ্টা করুন।"
            )
            response_placeholder.markdown(full_response)

        # =================================================
        # SOURCES
        # =================================================

        else:
            unique_sources = list(dict.fromkeys(collected_sources))

            if unique_sources:
                full_response += "\n\n**Sources**\n"
                for source in unique_sources:
                    full_response += f"- {source}\n"

            response_placeholder.markdown(full_response)

    st.session_state.processing = False

    # =====================================================
    # SAVE ASSISTANT MESSAGE
    # =====================================================

    st.session_state.messages.append({"role": "assistant", "content": full_response})

    # =====================================================
    # CREDIT
    # =====================================================

    if st.session_state.credits > 0:
        st.session_state.credits -= 1

    # =====================================================
    # CONVERSATION MEMORY
    # =====================================================

    if len(st.session_state.messages) >= 6:
        update_conversation_memory()

    st.rerun()


# =========================================================
# APP STATUS
# =========================================================

if st.session_state.processing:
    st.caption("Anis AI is thinking...")


# =========================================================
# FINAL APP SAFETY & CLEANUP
# (single pass, run once per rerun instead of five times)
# =========================================================

# ---------------------------------------------------------
# ENSURE REQUIRED SESSION STATES EXIST
# ---------------------------------------------------------

for key, default_value in DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = default_value

# ---------------------------------------------------------
# VALIDATE CREDITS
# ---------------------------------------------------------

try:
    st.session_state.credits = max(0, int(st.session_state.credits))
except (TypeError, ValueError):
    st.session_state.credits = 0

# ---------------------------------------------------------
# VALIDATE & LIMIT MESSAGES
# ---------------------------------------------------------

st.session_state.messages = clean_messages(st.session_state.messages)[-MAX_MESSAGES:]

# ---------------------------------------------------------
# VALIDATE & LIMIT HISTORY (structure + age + count)
# ---------------------------------------------------------

cleanup_old_history()

# ---------------------------------------------------------
# CURRENT CHAT TITLE (for display elsewhere in the app)
# ---------------------------------------------------------

st.session_state.current_chat_title = (
    create_chat_title(st.session_state.messages)
    if st.session_state.messages
    else "New Conversation"
)

st.session_state.history_count = len(st.session_state.history)
