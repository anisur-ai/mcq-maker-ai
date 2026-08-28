       
# ---------- MOBILE SIDEBAR CSS ----------


    if 
    if st.button(
        "👤                          📚
                    </
            st.rerun()


        if st.button(
            "🖼️ Create Image",
            use_container_width=True,
            key="home_image",
        ):

            st.session_state.active_mode = "image"

            st.session_state.messages.append(
                {
                    "role": "user",
                    "content": "I want to create an image."
                }
            )

            st.rerun()
            # =========================================================
# PART 4 — ANIS AI MOBILE CHAT INPUT
# =========================================================

st.markdown(
    """
    <style>

    /* =====================================================
       CHAT INPUT AREA
       ===================================================== */

    .anis-chat-wrapper {
        position: fixed;

        left: 50%;
        bottom: 10px;

        transform: translateX(-50%);

        width: min(
            calc(100vw - 20px),
            700px
        );

        z-index: 9999;

        padding-bottom: env(
            safe-area-inset-bottom,
            0px
        );
    }


    /* =====================================================
       MAIN INPUT BOX
       ===================================================== */

    .anis-chat-box {
        width: 100%;

        min-height: 54px;

        background: #1b1b1b;

        border: 1px solid #303030;

        border-radius: 27px;

        display: flex;

        align-items: flex-end;

        gap: 7px;

        padding: 7px;

        box-sizing: border-box;

        box-shadow:
            0 8px 30px rgba(0,0,0,.35);
    }


    /* =====================================================
       PLUS BUTTON
       ===================================================== */

    .anis-plus {
        width: 40px;
        height: 40px;

        flex: 0 0 40px;

        border-radius: 50%;

        border: none;

        background: #303030;

        color: #ffffff;

        font-size: 23px;

        display: flex;

        align-items: center;

        justify-content: center;

        cursor: pointer;
    }


    /* =====================================================
       TEXT INPUT
       ===================================================== */

    .anis-textarea {
        flex: 1;

        min-width: 0;

        min-height: 40px;

        max-height: 150px;

        resize: none;

        overflow-y: auto;

        border: none;

        outline: none;

        background: transparent;

        color: #ffffff;

        font-size: 16px;

        line-height: 22px;

        padding: 9px 5px;

        box-sizing: border-box;
    }


    .anis-textarea::placeholder {
        color: #858585;
    }


    /* =====================================================
       SEND BUTTON
       ===================================================== */

    .anis-send {
        width: 40px;
        height: 40px;

        flex: 0 0 40px;

        border-radius: 50%;

        border: none;

        background: #ffffff;

        color: #000000;

        font-size: 20px;

        font-weight: 700;

        display: flex;

        align-items: center;

        justify-content: center;

        cursor: pointer;
    }


    /* =====================================================
       ATTACHMENT PREVIEW
       ===================================================== */

    .anis-attachment-preview {
        margin-bottom: 8px;

        padding: 8px;

        width: fit-content;

        max-width: 100%;

        background: #1b1b1b;

        border: 1px solid #303030;

        border-radius: 16px;
    }


    .anis-attachment-preview img {
        display: block;

        width: 80px;
        height: 80px;

        object-fit: cover;

        border-radius: 11px;
    }


    /* =====================================================
       MOBILE
       ===================================================== */

    @media (max-width: 600px) {

        .anis-chat-wrapper {

            width: calc(100vw - 16px);

            bottom: 7px;
        }

        .anis-chat-box {

            min-height: 52px;

            border-radius: 25px;

            padding: 6px;
        }

        .anis-plus,
        .anis-send {

            width: 39px;
            height: 39px;

            flex-basis: 39px;
        }

        .anis-textarea {

            font-size: 16px;
        }
    }


    /* =====================================================
       VERY SMALL PHONES
       ===================================================== */

    @media (max-width: 360px) {

        .anis-chat-wrapper {

            width: calc(100vw - 12px);
        }

        .anis-plus,
        .anis-send {

            width: 37px;
            height: 37px;

            flex-basis: 37px;
        }
    }

    </style>
    """,
    unsafe_allow_html=True
)


# =========================================================
# IMAGE UPLOAD STATE
# =========================================================

if "attached_image" not in st.session_state:
    st.session_state.attached_image = None


# =========================================================
# CHAT INPUT
# =========================================================

chat_col1, chat_col2 = st.columns(
    [1, 6],
    gap="small"
)


# =========================================================
# PLUS / IMAGE BUTTON
# =========================================================

with chat_col1:

    uploaded_image = st.file_uploader(
        "＋",
        type=["png", "jpg", "jpeg", "webp"],
        key="anis_image_upload",
        label_visibility="collapsed"
    )


# =========================================================
# TEXT INPUT
# =========================================================

with chat_col2:

    user_input = st.chat_input(
        "Ask Anis AI..."
    )


# =========================================================
# SAVE IMAGE
# =========================================================

if uploaded_image is not None:

    st.session_state.attached_image = uploaded_image


# =========================================================
# IMAGE PREVIEW
# =========================================================

if st.session_state.attached_image is not None:

    preview_col1, preview_col2 = st.columns(
        [1, 5]
    )

    with preview_col1:

        st.image(
            st.session_state.attached_image,
            width=80
        )

    with preview_col2:

        if st.button(
            "✕ Remove image",
            key="remove_anis_image"
        ):

            st.session_state.attached_image = None
            st.rerun()


# =========================================================
# SEND MESSAGE
# =========================================================

if user_input:

    # Save message
    st.session_state.messages.append(
        {
            "role": "user",
            "content": user_input,
            "image": (
                st.session_state.attached_image
                if st.session_state.attached_image
                else None
            )
        }
    )

    # Clear attachment after sending
    st.session_state.attached_image = None

    # Existing AI processing will handle
    # the message in the next section.
    # =========================================================
# PART 5 — CONNECT ANIS AI INPUT TO EXISTING AI ENGINE
# =========================================================

# ---------------------------------------------------------
# PENDING MESSAGE STATE
# ---------------------------------------------------------

if "pending_user_message" not in st.session_state:
    st.session_state.pending_user_message = None


# ---------------------------------------------------------
# PROCESS NEW MESSAGE
# ---------------------------------------------------------

if st.session_state.pending_user_message is not None:

    pending = st.session_state.pending_user_message

    # Clear pending state first
    st.session_state.pending_user_message = None

    user_text = pending.get("content", "").strip()
    attached_image = pending.get("image")


    # -----------------------------------------------------
    # SAFETY CHECK
    # -----------------------------------------------------

    if not user_text and attached_image is None:
        st.stop()


    # -----------------------------------------------------
    # ADD USER MESSAGE
    # -----------------------------------------------------

    user_message = {
        "role": "user",
        "content": user_text
    }

    if attached_image is not None:
        user_message["image"] = attached_image

    st.session_state.messages.append(
        user_message
    )


    # -----------------------------------------------------
    # CONVERSATION MEMORY
    # -----------------------------------------------------

    try:

        conversation_context = manage_conversation_memory(
            st.session_state.messages
        )

    except Exception:

        conversation_context = st.session_state.messages


    # -----------------------------------------------------
    # DETERMINE WHETHER WEB SEARCH IS REQUIRED
    # -----------------------------------------------------

    try:

        should_search = needs_web_search(
            user_text
        )

    except Exception:

        should_search = False


    # -----------------------------------------------------
    # WEB SEARCH
    # -----------------------------------------------------

    search_results = None

    if should_search:

        try:

            search_results = smart_search(
                user_text
            )

        except Exception as e:

            search_results = None


    # -----------------------------------------------------
    # SELECT MODEL
    # -----------------------------------------------------

    try:

        selected_model = select_model_by_task(
            user_text
        )

    except Exception:

        selected_model = None


    # -----------------------------------------------------
    # PREPARE AI INPUT
    # -----------------------------------------------------

    ai_prompt = user_text

    if search_results:

        ai_prompt += (
            "\n\nRelevant web information:\n"
            + str(search_results)
        )


    # -----------------------------------------------------
    # AI FALLBACK SYSTEM
    # -----------------------------------------------------

    try:

        ai_response = provider_aware_ai_fallback(
            prompt=ai_prompt,
            model=selected_model,
            conversation=conversation_context
        )

    except TypeError:

        # Compatibility fallback for the existing
        # helper function signature
        try:

            ai_response = provider_aware_ai_fallback(
                ai_prompt
            )

        except Exception as e:

            ai_response = (
                "Sorry, Anis AI could not process "
                "your request right now."
            )

    except Exception as e:

        ai_response = (
            "Sorry, Anis AI could not process "
            "your request right now."
        )


    # -----------------------------------------------------
    # NORMALIZE RESPONSE
    # -----------------------------------------------------

    if ai_response is None:

        ai_response = (
            "Sorry, I could not generate a response."
        )

    elif not isinstance(ai_response, str):

        ai_response = str(ai_response)


    # -----------------------------------------------------
    # SAVE AI RESPONSE
    # -----------------------------------------------------

    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": ai_response
        }
    )


    # -----------------------------------------------------
    # LOG USAGE
    # -----------------------------------------------------

    try:

        log_usage(
            "chat"
        )

    except Exception:

        pass


    # -----------------------------------------------------
    # RERUN
    # -----------------------------------------------------

    st.rerun()
    # =========================================================
# PART 6 — ANIS AI MODES
# =========================================================

active_mode = st.session_state.get(
    "active_mode",
    None
)


# =========================================================
# DEFAULT MODE
# =========================================================

mode_instruction = """
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


# =========================================================
# MCQ MODE
# =========================================================

if active_mode == "mcq":

    mode_instruction = """
You are Anis AI's MCQ Generator.

Your job is to create high-quality educational questions.

When the user asks for MCQs:

- Understand the supplied topic, text, chapter or image.
- Create clear multiple-choice questions.
- Provide 4 options for each question.
- Give exactly one correct answer.
- Avoid ambiguous questions.
- Avoid duplicate questions.
- Keep questions appropriate for the student's level.
- If the user specifies a number, generate that number.
- If no number is specified, generate 10 MCQs.
- After the questions, provide a clearly separated Answer Key.
- If the user writes Bengali, respond in Bengali.
- If the user writes English, respond in English.

Format:

## MCQs

1. Question
   A) Option
   B) Option
   C) Option
   D) Option

2. Question
   A) Option
   B) Option
   C) Option
   D) Option

## Answer Key

1. A
2. C

Use attached study material when provided.
"""


# =========================================================
# ANALYZE MODE
# =========================================================

elif active_mode == "analyze":

    mode_instruction = """
You are Anis AI's Analysis Assistant.

Analyze the user's supplied text, question, image content,
document content or study material.

Your response should:

- Identify the important information.
- Explain the meaning clearly.
- Break difficult information into simple points.
- Identify important facts.
- Point out relationships or patterns when relevant.
- Mention uncertainty when the information is insufficient.
- Do not invent information.
- If the user writes Bengali, answer in Bengali.
- If the user writes English, answer in English.

Use headings and bullet points when helpful.
"""


# =========================================================
# HELP ME LEARN MODE
# =========================================================

elif active_mode == "learn":

    mode_instruction = """
You are Anis AI's personal learning assistant.

Help the student understand subjects clearly.

Rules:

- Explain difficult topics in simple language.
- Start from the basics when necessary.
- Use examples.
- Break large topics into small sections.
- Highlight important points.
- Ask a short practice question when appropriate.
- Do not make explanations unnecessarily complicated.
- If the user writes Bengali, answer in Bengali.
- If the user writes English, answer in English.
- Use attached study material when provided.
"""


# =========================================================
# IMAGE MODE
# =========================================================

elif active_mode == "image":

    mode_instruction = """
You are Anis AI.

The user has selected the image creation option.

Understand the user's image request and provide a clear,
useful response.

If the current application does not have an image-generation
API connected, clearly explain that image generation is not
currently connected rather than pretending an image was created.
"""


# =========================================================
# FINAL SYSTEM PROMPT
# =========================================================

system_prompt = mode_instruction
# =========================================================
# RESET SPECIAL MODE
# =========================================================

if st.session_state.get("active_mode") is not None:
    st.session_state.active_mode = None
    # =========================================================
# PART 7 — ANIS AI CHAT HISTORY
# =========================================================

def save_current_chat():

    messages = st.session_state.get("messages", [])

    if not messages:
        return

    # Remove invalid messages
    valid_messages = []

    for message in messages:

        if not isinstance(message, dict):
            continue

        role = message.get("role")
        content = message.get("content", "")

        if role not in ("user", "assistant"):
            continue

        if not str(content).strip():
            continue

        valid_messages.append({
            "role": role,
            "content": str(content)
        })

    if not valid_messages:
        return


    # Create title
    title = create_chat_title(valid_messages)


    # Create chat record
    chat_record = {
        "id": datetime.now().timestamp(),
        "created_at": datetime.now().isoformat(),
        "title": title,
        "messages": valid_messages,
    }


    # Add to history
    st.session_state.history.append(
        chat_record
    )


    # Keep only latest chats
    st.session_state.history = (
        st.session_state.history[-MAX_HISTORY_CHATS:]
    )


# =========================================================
# START NEW CHAT
# =========================================================

def start_new_chat():

    # Save current conversation first
    if st.session_state.get("messages"):

        save_current_chat()


    # Clear current conversation
    st.session_state.messages = []

    # Reset chat-related states
    st.session_state.chat_summary = ""
    st.session_state.selected_file = None
    st.session_state.attach_mode = None
    st.session_state.show_attach_menu = False
    st.session_state.processing = False

    # Reset special mode
    st.session_state.active_mode = None

    # Clear pending message
    if "pending_user_message" in st.session_state:
        st.session_state.pending_user_message = None

    # Clear attached image
    if "attached_image" in st.session_state:
        st.session_state.attached_image = None

    st.rerun()


# =========================================================
# LOAD OLD CHAT
# =========================================================

def load_chat(chat):

    if not isinstance(chat, dict):
        return

    messages = chat.get(
        "messages",
        []
    )

    if not isinstance(messages, list):
        messages = []


    # Load messages
    st.session_state.messages = list(
        messages
    )


    # Reset temporary states
    st.session_state.chat_summary = ""

    st.session_state.selected_file = None

    st.session_state.attach_mode = None

    st.session_state.show_attach_menu = False

    st.session_state.processing = False

    st.session_state.active_mode = None


    if "attached_image" in st.session_state:
        st.session_state.attached_image = None


    if "pending_user_message" in st.session_state:
        st.session_state.pending_user_message = None


    st.rerun()


# =========================================================
# DELETE CHAT
# =========================================================

def delete_chat(chat_id):

    st.session_state.history = [
        chat
        for chat in st.session_state.history
        if chat.get("id") != chat_id
    ]

    st.rerun()


# =========================================================
# HISTORY CLEANUP
# =========================================================

cleanup_old_history()


# =========================================================
# HISTORY COUNT
# =========================================================

st.session_state.history_count = len(
    st.session_state.history
                  )
# =========================================================
# PART 8 — ANIS AI ACCOUNT
# =========================================================

if "user_account" not in st.session_state:
    st.session_state.user_account = {
        "logged_in": False,
        "email": None,
        "name": None,
        "picture": None,
    }


# =========================================================
# ACCOUNT HELPERS
# =========================================================

def set_user_account(
    email=None,
    name=None,
    picture=None
):
    """
    Store verified account information
    in the current Streamlit session.
    """

    st.session_state.user_account = {
        "logged_in": bool(email),
        "email": email,
        "name": name,
        "picture": picture,
    }


def clear_user_account():

    st.session_state.user_account = {
        "logged_in": False,
        "email": None,
        "name": None,
        "picture": None,
    }

    # Clear current temporary chat
    st.session_state.messages = []

    # Clear temporary attachments
    if "attached_image" in st.session_state:
        st.session_state.attached_image = None

    if "selected_file" in st.session_state:
        st.session_state.selected_file = None


# =========================================================
# ACCOUNT DISPLAY
# =========================================================

account = st.session_state.user_account

if account["logged_in"]:

    display_name = (
        account["name"]
        or account["email"]
        or "User"
    )

else:

    display_name = "Anis"


# =========================================================
# PROFILE INFORMATION
# =========================================================

st.markdown(
    f"""
    <div style="
        display:none;
    ">
        {display_name}
    </div>
    """,
    unsafe_allow_html=True
)
# =========================================================
# PART 9 — MOBILE CHAT INPUT + IMAGE UPLOAD
# =========================================================

# ---------------------------------------------------------
# MOBILE INPUT CSS
# ---------------------------------------------------------

st.markdown(
    """
    <style>

    /* Hide Streamlit's default chat input */
    div[data-testid="stChatInput"] {
        display: none !important;
    }

    /* Bottom area */
    .anis-mobile-input {
        position: fixed;
        left: 50%;
        bottom: 8px;
        transform: translateX(-50%);

        width: calc(100vw - 16px);
        max-width: 700px;

        z-index: 9999;
    }

    /* Main input box */
    .anis-input-card {
        background: #1b1b1b;
        border: 1px solid #303030;

        border-radius: 26px;

        padding: 6px;

        box-sizing: border-box;

        box-shadow:
            0 8px 30px rgba(0,0,0,.45);
    }

    /* Textarea */
    .anis-input-card textarea {
        background: transparent !important;
        color: white !important;

        border: none !important;
        outline: none !important;

        resize: none !important;

        font-size: 16px !important;
        line-height: 22px !important;
    }

    .anis-input-card textarea::placeholder {
        color: #858585 !important;
    }

    /* Buttons */
    .anis-input-card button {
        border-radius: 50% !important;
    }

    /* Attachment preview */
    .anis-preview {
        background: #181818;

        border: 1px solid #303030;

        border-radius: 15px;

        padding: 8px;

        margin-bottom: 7px;

        display: flex;
        align-items: center;
        gap: 10px;
    }

    .anis-preview img {
        width: 65px;
        height: 65px;

        object-fit: cover;

        border-radius: 10px;
    }

    .anis-preview-name {
        color: #eeeeee;
        font-size: 13px;
    }

    /* Mobile */
    @media (max-width: 600px) {

        .anis-mobile-input {
            width: calc(100vw - 12px);
            bottom: 5px;
        }

        .anis-input-card {
            border-radius: 25px;
        }
    }

    </style>
    """,
    unsafe_allow_html=True
)


# =========================================================
# ATTACHMENT STATE
# =========================================================

if "selected_file" not in st.session_state:
    st.session_state.selected_file = None


# =========================================================
# + BUTTON / ATTACHMENT MENU
# =========================================================

if "show_attach_menu" not in st.session_state:
    st.session_state.show_attach_menu = False


plus_clicked = st.button(
    "＋",
    key="anis_plus_button",
    help="Add image or file"
)


if plus_clicked:

    st.session_state.show_attach_menu = (
        not st.session_state.show_attach_menu
    )

    st.rerun()


# =========================================================
# ATTACHMENT OPTIONS
# =========================================================

if st.session_state.show_attach_menu:

    st.markdown(
        """
        <div style="
            position:fixed;
            bottom:78px;
            left:12px;
            z-index:10000;

            background:#181818;
            border:1px solid #303030;

            border-radius:18px;

            padding:8px;

            width:190px;

            box-shadow:0 10px 35px rgba(0,0,0,.5);
        ">

            <div style="
                color:#888;
                font-size:12px;
                padding:7px;
            ">
                Add to Anis AI
            </div>

        </div>
        """,
        unsafe_allow_html=True
    )

    image_file = st.file_uploader(
        "🖼️ Choose image",
        type=["jpg", "jpeg", "png", "webp"],
        key="anis_mobile_image",
    )

    document_file = st.file_uploader(
        "📁 Choose file",
        type=None,
        key="anis_mobile_file",
    )


    if image_file is not None:

        st.session_state.selected_file = image_file

        st.session_state.show_attach_menu = False

        st.rerun()


    if document_file is not None:

        st.session_state.selected_file = document_file

        st.session_state.show_attach_menu = False

        st.rerun()


# =========================================================
# CURRENT ATTACHMENT PREVIEW
# =========================================================

if st.session_state.selected_file is not None:

    selected_file = st.session_state.selected_file

    file_name = getattr(
        selected_file,
        "name",
        "Attached file"
    )

    file_type = getattr(
        selected_file,
        "type",
        ""
    )


    if file_type.startswith("image/"):

        st.markdown(
            f"""
            <div class="anis-preview">

                <div class="anis-preview-name">
                    🖼️ {file_name}
                </div>

            </div>
            """,
            unsafe_allow_html=True
        )

        st.image(
            selected_file,
            width=90
        )

    else:

        st.info(
            f"📎 {file_name}"
        )


    if st.button(
        "✕ Remove attachment",
        key="anis_remove_attachment"
    ):

        st.session_state.selected_file = None

        st.session_state.show_attach_menu = False

        st.rerun()


# =========================================================
# TEXT INPUT
# =========================================================

st.markdown(
    '<div class="anis-mobile-input">',
    unsafe_allow_html=True
)


user_prompt = st.text_area(
    "Ask Anis AI",
    placeholder="Ask Anis AI...",
    height=48,
    key="anis_mobile_text",
    label_visibility="collapsed"
)


# =========================================================
# AUTO-GROW TEXTAREA
# =========================================================

st.markdown(
    """
    <script>

    function resizeAnisInput() {

        const textareas =
            window.parent.document.querySelectorAll(
                'textarea[aria-label="Ask Anis AI"]'
            );

        textareas.forEach(function(area) {

            area.style.height = "auto";

            let height = area.scrollHeight;

            if (height < 48) {
                height = 48;
            }

            if (height > 150) {
                height = 150;
                area.style.overflowY = "auto";
            } else {
                area.style.overflowY = "hidden";
            }

            area.style.height = height + "px";
        });
    }


    setInterval(
        resizeAnisInput,
        150
    );

    </script>
    """,
    unsafe_allow_html=True
)


# =========================================================
# SEND
# =========================================================

send_clicked = st.button(
    "↑",
    key="anis_mobile_send",
)


st.markdown(
    '</div>',
    unsafe_allow_html=True
)


# =========================================================
# PROCESS INPUT
# =========================================================

if send_clicked:

    prompt_input = user_prompt.strip()

    if not prompt_input and st.session_state.selected_file is None:

        st.warning(
            "Please write a message or attach a file."
        )

        st.stop()


    # -----------------------------------------------------
    # USER MESSAGE
    # -----------------------------------------------------

    st.session_state.messages.append(
        {
            "role": "user",
            "content": prompt_input
        }
    )


    # -----------------------------------------------------
    # KEEP ATTACHMENT FOR EXISTING PROCESSOR
    # -----------------------------------------------------

    # The existing AI processing code below this section
    # will use st.session_state.selected_file.


    # -----------------------------------------------------
    # DO NOT CLEAR selected_file HERE
    # -----------------------------------------------------
    #
    # Existing processing already reads the file with:
    #
    # smart_read_file(selected_file, ocr_api_key)
    #
    # and clears it after processing.
    #
    # -----------------------------------------------------

    st.rerun()
    # =========================================================
# PART 10 — ACCOUNT BASED CHAT HISTORY
# =========================================================

if "account_email" not in st.session_state:
    st.session_state.account_email = None


# =========================================================
# GET CURRENT ACCOUNT
# =========================================================

def get_current_account():

    return st.session_state.get(
        "account_email"
    )


# =========================================================
# ACCOUNT HISTORY KEY
# =========================================================

def get_history_key():

    email = get_current_account()

    if email:
        return f"history_{email.lower().strip()}"

    return "history_guest"


# =========================================================
# LOAD ACCOUNT HISTORY
# =========================================================

def load_account_history():

    history_key = get_history_key()

    if history_key not in st.session_state:
        st.session_state[history_key] = []

    st.session_state.history = (
        st.session_state[history_key]
    )


# =========================================================
# SAVE ACCOUNT HISTORY
# =========================================================

def save_account_history():

    history_key = get_history_key()

    st.session_state[history_key] = list(
        st.session_state.history
    )


# =========================================================
# SAVE CURRENT CHAT
# =========================================================

def save_current_chat():

    if not st.session_state.messages:
        return


    chat_record = {
        "id": datetime.now().timestamp(),

        "created_at":
            datetime.now().isoformat(),

        "title":
            create_chat_title(
                st.session_state.messages
            ),

        "messages":
            list(
                st.session_state.messages
            ),
    }


    st.session_state.history.append(
        chat_record
    )


    st.session_state.history = (
        st.session_state.history[
            -MAX_HISTORY_CHATS:
        ]
    )


    # Save under current account
    save_account_history()


# =========================================================
# SWITCH ACCOUNT
# =========================================================

def switch_account(
    email,
    name=None
):

    # Save current chat before switching
    if st.session_state.get("messages"):

        save_current_chat()


    # Set account
    st.session_state.account_email = (
        email.lower().strip()
        if email
        else None
    )


    # Load that account's history
    load_account_history()


    # Reset current chat
    st.session_state.messages = []

    st.session_state.chat_summary = ""

    st.session_state.selected_file = None

    st.session_state.attach_mode = None

    st.session_state.show_attach_menu = False

    st.session_state.processing = False

    st.session_state.active_mode = None


# =========================================================
# ACCOUNT INFO
# =========================================================

current_email = get_current_account()


if current_email:

    account_label = current_email

else:

    account_label = "Guest"


# =========================================================
# HISTORY INITIALIZATION
# =========================================================

load_account_history()
# =========================================================
# PART 11 — ANIS AI CHAT SCREEN
# =========================================================

st.markdown(
    """
    <style>

    /* =====================================================
       CHAT SCREEN
       ===================================================== */

    .anis-chat-screen {
        width: 100%;
        max-width: 700px;

        margin: 0 auto;

        padding: 10px 4px 120px;

        box-sizing: border-box;
    }


    /* =====================================================
       USER MESSAGE
       ===================================================== */

    .anis-user-row {
        display: flex;

        justify-content: flex-end;

        width: 100%;

        margin: 10px 0;
    }


    .anis-user-message {
        max-width: 82%;

        padding: 11px 15px;

        background: #303030;

        color: #ffffff;

        border-radius: 20px 20px 5px 20px;

        font-size: 15px;

        line-height: 1.5;

        word-wrap: break-word;

        overflow-wrap: anywhere;
    }


    /* =====================================================
       AI MESSAGE
       ===================================================== */

    .anis-ai-row {
        display: flex;

        justify-content: flex-start;

        width: 100%;

        margin: 14px 0;
    }


    .anis-ai-message {
        max-width: 90%;

        color: #eeeeee;

        font-size: 15px;

        line-height: 1.6;

        word-wrap: break-word;

        overflow-wrap: anywhere;
    }


    /* =====================================================
       AI NAME
       ===================================================== */

    .anis-ai-name {
        font-size: 12px;

        color: #858585;

        margin-bottom: 5px;
    }


    /* =====================================================
       ATTACHED IMAGE
       ===================================================== */

    .anis-chat-image {
        max-width: 220px;

        border-radius: 15px;

        margin-top: 7px;
    }


    /* =====================================================
       MOBILE
       ===================================================== */

    @media (max-width: 600px) {

        .anis-chat-screen {
            padding-left: 8px;
            padding-right: 8px;
            padding-bottom: 115px;
        }

        .anis-user-message {
            max-width: 86%;

            font-size: 15px;
        }

        .anis-ai-message {
            max-width: 94%;

            font-size: 15px;
        }

        .anis-chat-image {
            max-width: 190px;
        }
    }


    /* =====================================================
       SMALL PHONE
       ===================================================== */

    @media (max-width: 360px) {

        .anis-chat-screen {
            padding-left: 5px;
            padding-right: 5px;
        }

        .anis-user-message {
            max-width: 90%;
        }

        .anis-ai-message {
            max-width: 96%;
        }
    }

    </style>
    """,
    unsafe_allow_html=True
)


# =========================================================
# CHAT DISPLAY
# =========================================================

if st.session_state.get("messages"):

    st.markdown(
        '<div class="anis-chat-screen">',
        unsafe_allow_html=True
    )


    for message in st.session_state.messages:

        role = message.get(
            "role",
            "assistant"
        )

        content = message.get(
            "content",
            ""
        )

        # -------------------------------------------------
        # USER
        # -------------------------------------------------

        if role == "user":

            st.markdown(
                '<div class="anis-user-row">',
                unsafe_allow_html=True
            )

            st.markdown(
                f"""
                <div class="anis-user-message">
                    {content}
                </div>
                """,
                unsafe_allow_html=True
            )

            st.markdown(
                '</div>',
                unsafe_allow_html=True
            )


            # Attached image
            attached_image = message.get(
                "image"
            )

            if attached_image is not None:

                st.image(
                    attached_image,
                    width=190
                )


        # -------------------------------------------------
        # ASSISTANT
        # -------------------------------------------------

        else:

            st.markdown(
                '<div class="anis-ai-row">',
                unsafe_allow_html=True
            )

            st.markdown(
                '<div class="anis-ai-message">',
                unsafe_allow_html=True
            )

            st.markdown(
                '<div class="anis-ai-name">'
                '✦ Anis AI'
                '</div>',
                unsafe_allow_html=True
            )

            # Markdown response
            st.markdown(
                content
            )

            st.markdown(
                '</div>',
                unsafe_allow_html=True
            )

            st.markdown(
                '</div>',
                unsafe_allow_html=True
            )


    st.markdown(
        '</div>',
        unsafe_allow_html=True
        )
    # =========================================================
# PART 12 — FINAL MOBILE LAYOUT
# =========================================================

st.markdown(
    """
    <style>

    /* =====================================================
       GLOBAL MOBILE APP
       ===================================================== */

    html,
    body,
    [data-testid="stAppViewContainer"],
    [data-testid="stApp"] {

        width: 100%;
        min-width: 0;

        margin: 0;
        padding: 0;

        overflow-x: hidden;
    }


    /* =====================================================
       MAIN CONTENT
       ===================================================== */

    [data-testid="stMain"] {

        width: 100% !important;

        max-width: 700px !important;

        margin: 0 auto !important;

        padding-left: 8px !important;
        padding-right: 8px !important;

        box-sizing: border-box;
    }


    /* =====================================================
       HEADER
       ===================================================== */

    .anis-header {

        width: 100%;

        height: 52px;

        display: flex;

        align-items: center;

        justify-content: space-between;

        box-sizing: border-box;

        padding: 0 8px;

        position: sticky;

        top: 0;

        z-index: 9000;

        background: #101010;
    }


    .anis-logo {

        font-size: 19px;

        font-weight: 600;

        color: #ffffff;

        white-space: nowrap;
    }


    .anis-profile {

        width: 34px;
        height: 34px;

        border-radius: 50%;

        display: flex;

        align-items: center;

        justify-content: center;

        background: #303030;

        color: white;

        font-size: 14px;
    }


    /* =====================================================
       SCROLL AREA
       ===================================================== */

    [data-testid="stAppViewContainer"] {

        overflow-y: auto !important;

        -webkit-overflow-scrolling: touch;
    }


    /* =====================================================
       REMOVE DESKTOP WIDTH
       ===================================================== */

    .block-container {

        width: 100% !important;

        max-width: 700px !important;

        padding-top: 0.5rem !important;

        padding-bottom: 120px !important;

        padding-left: 8px !important;
        padding-right: 8px !important;

        margin: 0 auto !important;

        box-sizing: border-box;
    }


    /* =====================================================
       BUTTONS
       ===================================================== */

    .stButton > button {

        min-height: 42px;

        border-radius: 14px;

        font-size: 14px;

        white-space: normal;
    }


    /* =====================================================
       FILE UPLOADER
       ===================================================== */

    [data-testid="stFileUploader"] {

        width: 100%;

        box-sizing: border-box;
    }


    /* =====================================================
       TEXTAREA
       ===================================================== */

    textarea {

        max-width: 100% !important;

        box-sizing: border-box !important;
    }


    /* =====================================================
       MOBILE PHONE
       ===================================================== */

    @media (max-width: 600px) {

        [data-testid="stMain"] {

            max-width: 100% !important;

            padding-left: 6px !important;
            padding-right: 6px !important;
        }


        .block-container {

            max-width: 100% !important;

            padding-left: 6px !important;
            padding-right: 6px !important;

            padding-bottom: 115px !important;
        }


        .anis-header {

            height: 50px;

            padding-left: 5px;
            padding-right: 5px;
        }


        .anis-logo {

            font-size: 18px;
        }
    }


    /* =====================================================
       VERY SMALL PHONE
       ===================================================== */

    @media (max-width: 360px) {

        .block-container {

            padding-left: 4px !important;
            padding-right: 4px !important;
        }


        .anis-header {

            height: 48px;
        }


        .anis-logo {

            font-size: 17px;
        }
    }


    /* =====================================================
       PREVENT HORIZONTAL SCROLL
       ===================================================== */

    * {

        max-width: 100%;

        box-sizing: border-box;
    }


    img,
    video {

        max-width: 100%;

        height: auto;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# =========================================================
# ANIS AI HEADER
# =========================================================

st.markdown(
    """
    <div class="anis-header">

        <div class="anis-logo">
            ✦ Anis AI
        </div>

        <div class="anis-profile">
            A
        </div>

    </div>
    """,
    unsafe_allow_html=True
)
    

    

