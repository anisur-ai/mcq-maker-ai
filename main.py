import streamlit as st
import re

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

# -------------------------------
# Streamlit Page Configuration
# -------------------------------

st.set_page_config(
    page_title="Anis AI - Personal AI Assistant & Study Partner",
    page_icon="🤖",
    layout="centered",
    initial_sidebar_state="collapsed",
)
# -------------------------------
# Usage Analytics
# -------------------------------

if "analytics_logged" not in st.session_state:
    user_id = st.session_state.get("user_id")

    if not user_id:
        user_id = f"user_{id(st.session_state)}"
        st.session_state.user_id = user_id

    log_usage(user_id, event_type="visit")
    st.session_state.analytics_logged = True
    
# -------------------------------
# Hide Sidebar & Clean UI
# -------------------------------

st.markdown("""
<style>

[data-testid="collapsedControl"]{
display:none;
}

.stChatMessage{
background:transparent !important;
}

.block-container{
padding-top:2rem;
padding-bottom:2rem;
max-width:850px;
}

footer{
visibility:hidden;
}

</style>
""", unsafe_allow_html=True)

# -------------------------------
# API Keys
# -------------------------------

keys_dict = {
    "groq": st.secrets.get("GROQ_API_KEY"),
    "gemini": st.secrets.get("GEMINI_API_KEY"),
    "mistral": st.secrets.get("MISTRAL_API_KEY"),
    "openrouter": st.secrets.get("OPENROUTER_API_KEY"),
    "tavily": st.secrets.get("TAVILY_API_KEY"),
    "firecrawl": st.secrets.get("FIRECRAWL_API_KEY"),
    "jina": st.secrets.get("JINA_API_KEY"),
}

ocr_api_key = st.secrets.get("OCR_API_KEY")

# -------------------------------
# Header
# -------------------------------

st.markdown(
"""
<h1 style="text-align:center;">
Anis AI
</h1>
""",
unsafe_allow_html=True,
)

st.markdown(
"""
<p style="text-align:center;color:gray;">
How can I help you today?
</p>
""",
unsafe_allow_html=True,
)

# -------------------------------
# Session State
# -------------------------------

if "messages" not in st.session_state:
    st.session_state.messages = []

if "chat_summary" not in st.session_state:
    st.session_state.chat_summary = ""

# -------------------------------
# Show Previous Chat
# -------------------------------

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# -------------------------------
# File Uploader
# -------------------------------

uploaded_file = st.file_uploader(
    "Attach File",
    type=[
        "jpg",
        "jpeg",
        "png",
        "webp",
        "pdf",
        "txt",
        "docx",
    ],
    label_visibility="collapsed",
)

# -------------------------------
# Chat Input
# -------------------------------

if prompt := st.chat_input("Message Anis AI..."):

    st.session_state.messages.append(
        {
            "role": "user",
            "content": prompt,
        }
    )

    with st.chat_message("user"):
        st.markdown(prompt)

    collected_sources = []

    file_context = ""

    external_context = ""

    # -------------------------------
    # Read Attached File
    # -------------------------------

    if uploaded_file is not None:

        file_context = smart_read_file(
            uploaded_file,
            ocr_api_key
        )

        if file_context:
            file_context = (
                "\n\n--- ATTACHED FILE CONTENT ---\n"
                + file_context
            )

    # -------------------------------
    # URL Detection
    # -------------------------------

    url_match = re.search(
        r"https?://[^\s]+",
        prompt
    )

    # -------------------------------
    # External Context
    # -------------------------------

    if url_match:

        target_url = url_match.group(0)

        scraped_text, collected_sources = smart_scrape(
            target_url,
            keys_dict.get("firecrawl"),
            keys_dict.get("jina")
        )

        external_context = (
            "\n\n--- URL CONTENT ---\n"
            + scraped_text
        )

    else:

        should_search = needs_web_search(
            prompt,
            keys_dict.get("groq")
        )

        if should_search:

            search_text, collected_sources = smart_search(
                prompt,
                keys_dict.get("tavily"),
                keys_dict.get("jina")
            )

            if search_text:

                external_context = f"\n\n--- LIVE WEB SEARCH RESULTS ---\n{search_text}"
        
            
    # -------------------------------
    # Model Router
    # -------------------------------

    router_info = select_model_by_task(
        prompt,
        file_context + external_context
    )

        # -------------------------------
    # Conversation Memory
    # -------------------------------

    managed_messages = st.session_state.messages
    st.session_state.chat_summary = ""

    #     # -------------------------------
    # System Prompt
    # -------------------------------

    system_prompt = (
        "You are Anis AI, a professional autonomous AI assistant.\n\n"
        "Rules:\n"
        "- Think carefully before answering.\n"
        "- Never expose internal reasoning.\n"
        "- Never mention routing, fallback, providers or internal systems.\n"
        "- Automatically detect the user's language.\n"
        "- Reply in Bengali if the user writes in Bengali.\n"
        "- Read attached files automatically.\n"
        "- Read URLs automatically.\n"
        "- Use live web search only when necessary.\n"
        "- Give accurate and concise answers.\n"
        "- If external information was used, add a Sources section.\n"
        "- If no external information was used, do not add Sources.\n"
    )

    ai_messages = []
    ai_messages = [
        {
            "role": "system",
            "content": system_prompt,
        }
    ]

    for msg in managed_messages:
        ai_messages.append(msg)

    final_prompt = (
        prompt
        + file_context
        + external_context
    )

    ai_messages.append(
        {
            "role": "user",
            "content": final_prompt,
        }
        )

    # -------------------------------
    # Assistant Response
    # -------------------------------

    with st.chat_message("assistant"):

        response_placeholder = st.empty()

        full_response = ""

        has_error = False

        try:

            stream = provider_aware_ai_fallback(
                keys_dict,
                router_info,
                ai_messages,
            )

            for chunk in stream:

                if (
                    chunk == "ERROR_ALL_FAILED"
                    or chunk.startswith("দুঃখিত")
                ):
                    has_error = True
                    break

                full_response += chunk

                response_placeholder.markdown(
                    full_response + "▌"
                )

            if has_error or not full_response:

                error_message = (
                    "দুঃখিত কিছুক্ষণ অপেক্ষা করুন "
                    "টেকনিক্যাল সমস্যা হয়েছে ঠিক করা হচ্ছে"
                )

                response_placeholder.markdown(
                    error_message
                )

                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": error_message,
                    }
                )

            else:

                if collected_sources:

                    full_response += "\n\n**Sources**\n"

                    for source in sorted(
                        set(collected_sources)
                    ):
                        full_response += f"- {source}\n"

                response_placeholder.markdown(
                    full_response
                )

                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": full_response,
                    }
                )

        except Exception:

            error_message = (
                "দুঃখিত কিছুক্ষণ অপেক্ষা করুন "
                "টেকনিক্যাল সমস্যা হয়েছে ঠিক করা হচ্ছে"
            )

            response_placeholder.markdown(
                error_message
            )

            st.session_state.messages.append(
    {
        "role": "assistant",
        "content": error_message,
    }
            )            
