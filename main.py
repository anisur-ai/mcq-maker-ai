import streamlit as st
import re

from helpers import smart_read_file
from helpers import needs_web_search
from helpers import smart_search
from helpers import smart_scrape
from helpers import select_model_by_task
from helpers import manage_conversation_memory
from helpers import provider_aware_ai_fallback

st.set_page_config(
    page_title="Anis AI",
    page_icon="🤖",
    layout="centered",
    initial_sidebar_state="collapsed"
)

st.markdown("""
    <style>
    [data-testid="collapsedControl"] {display: none;}
    .stChatMessage {background-color: transparent !important;}
    </style>
""", unsafe_allow_html=True)

keys_dict = {
    "groq": st.secrets.get("GROQ_API_KEY"),
    "gemini": st.secrets.get("GEMINI_API_KEY"),
    "mistral": st.secrets.get("MISTRAL_API_KEY"),
    "openrouter": st.secrets.get("OPENROUTER_API_KEY"),
    "tavily": st.secrets.get("TAVILY_API_KEY"),
    "firecrawl": st.secrets.get("FIRECRAWL_API_KEY"),
    "jina": st.secrets.get("JINA_API_KEY")
}
ocr_api_key = st.secrets.get("OCR_API_KEY")

st.markdown("<h1 style='text-align: center; color: #1f2937; margin-bottom: 0px;'>Anis AI</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #6b7280; font-size: 16px; margin-top: 5px;'>How can I help you today?</p>", unsafe_allow_html=True)
st.write("")

if "messages" not in st.session_state:
    st.session_state.messages = []
if "chat_summary" not in st.session_state:
    st.session_state.chat_summary = ""

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

uploaded_file = st.file_uploader("Attach file", type=["jpg", "jpeg", "png", "pdf", "txt", "docx"], label_visibility="collapsed")

if prompt := st.chat_input("Message Anis AI..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    collected_sources = []
    file_context = ""
    external_context = ""

    if uploaded_file is not None:
        file_context = smart_read_file(uploaded_file, ocr_api_key)
        if file_context:
            file_context = f"\n\n--- ATTACHED FILE CONTENT ---\n{file_context}"

    url_match = re.search(r'https?://[^\s]+', prompt)
    
    if url_match:
        target_url = url_match.group(0)
        scraped_text, collected_sources = smart_scrape(target_url, keys_dict.get("firecrawl"), keys_dict.get("jina"))
        external_context = f"\n\n--- URL CONTENT ---\n{scraped_text}"
    else:
        should_search = needs_web_search(prompt, keys_dict.get("groq"))
        if should_search:
            search_text, collected_sources = smart_search(prompt, keys_dict.get("tavily"), keys_dict.get("jina"))
            if search_text:
                external_context = f"\n\n--- LIVE WEB SEARCH RESULTS ---\n{search_text}"

    router_info = select_model_by_task(prompt, file_context + external_context)

    st.session_state.chat_summary, managed_messages = manage_conversation_memory(
        st.session_state.messages, 
        keys_dict.get("groq"), 
        st.session_state.chat_summary
    )

    system_prompt = """
You are Anis AI, a world-class, professional, and autonomous AI assistant.
- Decide and execute everything automatically and internally.
- Never expose tools, internal steps, routing logic, or fallback mechanisms to the user.
- Think step by step internally.
- Answer naturally, clearly, and concisely unless asked for detailed explanations.
- Detect language automatically and always prefer Bengali if the user writes in Bengali.
- If external information (web search or URLs) was used, you MUST cite the sources clearly at the very end under a 'Sources' heading with clean URLs. If no external search was performed, do NOT include a Sources section.
"""

    ai_messages = [{"role": "system", "content": system_prompt}]
    for m in managed_messages[:-1]:
        ai_messages.append({"role": m["role"], "content": m["content"]})
    
    final_user_input = prompt + file_context + external_context
    ai_messages.append({"role": "user", "content": final_user_input})

    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        full_response = ""
        has_error = False

        try:
            stream_gen = provider_aware_ai_fallback(keys_dict, router_info, ai_messages)
            for chunk in stream_gen:
                if chunk.startswith("দুঃখিত") or chunk == "ERROR_ALL_FAILED":
                    has_error = True
                    full_response = "দুঃখিত কিছুক্ষণ অপেক্ষা করুন টেকনিক্যাল সমস্যা হয়েছে ঠিক করা হচ্ছে"
                    break
                full_response += chunk
                response_placeholder.markdown(full_response + "▌")

            if has_error or not full_response:
                error_msg = "দুঃখিত কিছুক্ষণ অপেক্ষা করুন টেকনিক্যাল সমস্যা হয়েছে ঠিক করা হচ্ছে"
                response_placeholder.markdown(error_msg)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})
            else:
                if collected_sources:
                    full_response += "\n\n**Sources**\n"
                    for src in set(collected_sources):
                        full_response += f"- {src}\n"

                response_placeholder.markdown(full_response)
                st.session_state.messages.append({"role": "assistant", "content": full_response})

        except Exception:
            error_msg = "দুঃখিত কিছুক্ষণ অপেক্ষা করুন টেকনিক্যাল সমস্যা হয়েছে ঠিক করা হচ্ছে"
            response_placeholder.markdown(error_msg)
            st.session_state.messages.append({"role": "assistant", "content": error_msg})
