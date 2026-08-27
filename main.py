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
    layout="centered",
    initial_sidebar_state="collapsed",
)


# =========================================================
# ANIS AI — MOBILE APP STYLE
# =========================================================

st.markdown(
    """
    <style>

    /* =====================================================
       GLOBAL MOBILE APP
       ===================================================== */

    html,
    body,
    [data-testid="stAppViewContainer"] {
        background: #000000 !important;
    }

    [data-testid="stAppViewContainer"] {
        max-width: 100vw !important;
        min-height: 100dvh !important;
        overflow-x: hidden !important;
    }

    [data-testid="stAppViewBlockContainer"] {
        max-width: 100% !important;
        padding-left: 12px !important;
        padding-right: 12px !important;
        padding-top: 8px !important;
        padding-bottom: 110px !important;
    }


    /* =====================================================
       REMOVE STREAMLIT DEFAULT TOP SPACE
       ===================================================== */

    header[data-testid="stHeader"] {
        background: transparent !important;
    }

    #MainMenu {
        visibility: hidden;
    }

    footer {
        visibility: hidden;
    }


    /* =====================================================
       MOBILE APP HEADER
       ===================================================== */

    .anis-header {
        width: 100%;
        height: 54px;

        display: flex;
        align-items: center;
        justify-content: space-between;

        padding: 0 4px;
        margin-bottom: 8px;
    }

    .anis-brand {
        font-size: 20px;
        font-weight: 600;
        color: #ffffff;
        letter-spacing: -0.3px;
    }

    .anis-profile {
        width: 34px;
        height: 34px;

        border-radius: 50%;

        display: flex;
        align-items: center;
        justify-content: center;

        background: #303030;
        color: #ffffff;

        font-size: 15px;
        font-weight: 600;
    }


    /* =====================================================
       HOME / WELCOME
       ===================================================== */

    .anis-home {
        min-height: calc(100dvh - 170px);

        display: flex;
        flex-direction: column;
        justify-content: center;

        padding: 20px 4px 30px;
    }

    .anis-greeting {
        margin-bottom: 34px;
    }

    .anis-greeting h1 {
        margin: 0;
        padding: 0;

        font-size: clamp(30px, 8vw, 42px);
        line-height: 1.1;

        font-weight: 600;
        letter-spacing: -1.5px;

        color: #ffffff;
    }

    .anis-greeting p {
        margin: 8px 0 0;

        font-size: clamp(22px, 5.5vw, 30px);
        line-height: 1.2;

        color: #8f8f8f;

        letter-spacing: -0.8px;
    }


    /* =====================================================
       ACTION CARDS
       ===================================================== */

    .anis-actions {
        display: grid;
        grid-template-columns: 1fr 1fr;

        gap: 10px;

        width: 100%;
    }

    .anis-action {
        min-height: 82px;

        padding: 15px;

        border-radius: 20px;

        background: #181818;
        border: 1px solid #252525;

        display: flex;
        flex-direction: column;
        justify-content: space-between;

        color: #ffffff;

        transition:
            transform 0.15s ease,
            background 0.15s ease;
    }

    .anis-action:hover {
        background: #222222;
        transform: translateY(-1px);
    }

    .anis-action-icon {
        font-size: 22px;
        margin-bottom: 8px;
    }

    .anis-action-text {
        font-size: 14px;
        font-weight: 500;
    }


    /* =====================================================
       MOBILE CHAT INPUT AREA
       ===================================================== */

    .anis-input-space {
        height: 90px;
    }


    /* =====================================================
       MOBILE BREAKPOINT
       ===================================================== */

    @media (max-width: 600px) {

        [data-testid="stAppViewBlockContainer"] {
            padding-left: 10px !important;
            padding-right: 10px !important;
        }

        .anis-home {
            min-height: calc(100dvh - 165px);
        }

        .anis-greeting h1 {
            font-size: 34px;
        }

        .anis-greeting p {
            font-size: 24px;
        }

        .anis-action {
            min-height: 78px;
            border-radius: 18px;
        }
    }


    /* =====================================================
       VERY SMALL PHONES
       ===================================================== */

    @media (max-width: 360px) {

        .anis-greeting h1 {
            font-size: 30px;
        }

        .anis-greeting p {
            font-size: 21px;
        }

        .anis-actions {
            gap: 8px;
        }

        .anis-action {
            padding: 12px;
        }
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# MOBILE HEADER
# =========================================================

st.markdown(
    """
    <div class="anis-header">

        <div class="anis-brand">
            Anis AI
        </div>

        <div class="anis-profile">
            A
        </div>

    </div>
    """,
    unsafe_allow_html=True,
)
# =========================================================
# PART 2 — ANIS AI MOBILE SIDEBAR
# =========================================================

# ---------- MOBILE SIDEBAR CSS ----------

st.markdown(
    """
    <style>

    /* Hide normal Streamlit sidebar */
    section[data-testid="stSidebar"] {
        display: none !important;
    }

    /* Mobile sidebar button */
    .mobile-menu-btn {
        position: fixed;
        top: 13px;
        left: 12px;
        z-index: 99999;

        width: 38px;
        height: 38px;

        border-radius: 50%;
        border: 1px solid #292929;

        background: #151515;
        color: white;

        display: flex;
        align-items: center;
        justify-content: center;

        font-size: 19px;
        cursor: pointer;
    }

    /* Move Anis AI slightly away from menu */
    .anis-header {
        padding-left: 48px !important;
    }

    /* Sidebar panel */
    .mobile-sidebar {
        position: fixed;

        top: 0;
        left: 0;

        width: min(82vw, 330px);
        height: 100dvh;

        background: #111111;

        z-index: 99990;

        padding: 18px 14px;

        box-sizing: border-box;

        border-right: 1px solid #292929;

        overflow-y: auto;
    }

    .sidebar-title {
        color: white;
        font-size: 20px;
        font-weight: 600;

        margin-bottom: 24px;

        padding-left: 8px;
    }

    .sidebar-section {
        color: #858585;

        font-size: 12px;
        font-weight: 500;

        margin: 18px 8px 8px;
    }

    .history-title {
        color: #eeeeee;

        font-size: 14px;

        padding: 10px 8px;

        border-radius: 12px;

        margin-bottom: 3px;
    }

    .mobile-overlay {
        position: fixed;

        inset: 0;

        background: rgba(0, 0, 0, 0.65);

        z-index: 99980;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# MOBILE MENU HEADER BUTTON
# =========================================================

menu_col, title_col, profile_col = st.columns(
    [1, 5, 1],
    vertical_alignment="center"
)

with menu_col:
    menu_clicked = st.button(
        "☰",
        key="mobile_menu_button",
        help="Open menu",
    )

with profile_col:
    profile_clicked = st.button(
        "A",
        key="mobile_profile_button",
        help="Profile",
    )


# =========================================================
# SIDEBAR STATE
# =========================================================

if "mobile_sidebar_open" not in st.session_state:
    st.session_state.mobile_sidebar_open = False

if "profile_open" not in st.session_state:
    st.session_state.profile_open = False


if menu_clicked:
    st.session_state.mobile_sidebar_open = True
    st.session_state.profile_open = False
    st.rerun()


if profile_clicked:
    st.session_state.profile_open = not st.session_state.profile_open
    st.session_state.mobile_sidebar_open = False
    st.rerun()


# =========================================================
# MOBILE SIDEBAR
# =========================================================

if st.session_state.mobile_sidebar_open:

    st.markdown(
        '<div class="mobile-overlay"></div>',
        unsafe_allow_html=True
    )

    st.markdown(
        """
        <div class="mobile-sidebar">

            <div class="sidebar-title">
                ✦ Anis AI
            </div>

        </div>
        """,
        unsafe_allow_html=True
    )

    if st.button(
        "✦  New Chat",
        use_container_width=True,
        key="mobile_new_chat"
    ):
        st.session_state.mobile_sidebar_open = False
        start_new_chat()


    st.markdown(
        '<div class="sidebar-section">TOOLS</div>',
        unsafe_allow_html=True
    )

    if st.button(
        "📝  Create MCQ",
        use_container_width=True,
        key="mobile_mcq"
    ):
        st.session_state.mobile_sidebar_open = False
        st.session_state.active_mode = "mcq"
        st.rerun()


    if st.button(
        "🔍  Analyze",
        use_container_width=True,
        key="mobile_analyze"
    ):
        st.session_state.mobile_sidebar_open = False
        st.session_state.active_mode = "analyze"
        st.rerun()


    if st.button(
        "📚  Help Me Learn",
        use_container_width=True,
        key="mobile_learn"
    ):
        st.session_state.mobile_sidebar_open = False
        st.session_state.active_mode = "learn"
        st.rerun()


    st.markdown(
        '<div class="sidebar-section">CHAT HISTORY</div>',
        unsafe_allow_html=True
    )


    # Existing history is preserved
    if not st.session_state.history:

        st.caption("No previous conversations.")

    else:

        for chat in reversed(st.session_state.history):

            chat_id = chat.get("id")
            title = chat.get(
                "title",
                "Conversation"
            )

            if len(title) > 30:
                title = title[:30] + "..."

            if st.button(
                f"💬  {title}",
                key=f"mobile_history_{chat_id}",
                use_container_width=True,
            ):
                load_chat(chat)


    st.markdown(
        '<div class="sidebar-section">ACCOUNT</div>',
        unsafe_allow_html=True
    )


    if st.button(
        "⚙️  Settings",
        use_container_width=True,
        key="mobile_settings"
    ):
        st.session_state.mobile_sidebar_open = False
        st.info("Settings will be added later.")


    if st.button(
        "👤  Account",
        use_container_width=True,
        key="mobile_account"
    ):
        st.session_state.mobile_sidebar_open = False
        st.info("Account settings will be added later.")


    if st.button(
        "×  Close Menu",
        use_container_width=True,
        key="mobile_close_sidebar"
    ):
        st.session_state.mobile_sidebar_open = False
        st.rerun()


# =========================================================
# PROFILE POPUP
# =========================================================

if st.session_state.profile_open:

    st.markdown(
        """
        <div style="
            position:fixed;
            top:58px;
            right:12px;
            z-index:99999;
            width:230px;
            padding:16px;
            border-radius:18px;
            background:#181818;
            border:1px solid #292929;
            color:white;
            box-shadow:0 10px 35px rgba(0,0,0,.5);
        ">
            <div style="
                font-size:15px;
                font-weight:600;
                margin-bottom:10px;
            ">
                Anis AI Account
            </div>

            <div style="
                font-size:13px;
                color:#999;
            ">
                Google account will appear here
            </div>
        </div>
        """,
        unsafe_allow_html=True
)
    # =========================================================
# PART 3 — ANIS AI MOBILE HOME SCREEN
# =========================================================

# Keep active mode available
if "active_mode" not in st.session_state:
    st.session_state.active_mode = None


# =========================================================
# HOME SCREEN
# =========================================================

if not st.session_state.messages:

    st.markdown(
        """
        <style>

        /* =================================================
           ANIS AI HOME
           ================================================= */

        .anis-home-screen {
            min-height: calc(100dvh - 190px);

            display: flex;
            flex-direction: column;
            justify-content: center;

            padding: 10px 4px 35px;
            box-sizing: border-box;
        }


        /* =================================================
           GREETING
           ================================================= */

        .anis-welcome {
            margin-bottom: 32px;
        }

        .anis-welcome-title {
            font-size: clamp(32px, 9vw, 44px);
            font-weight: 600;

            line-height: 1.1;

            margin: 0;

            letter-spacing: -1.5px;

            color: #ffffff;
        }

        .anis-welcome-subtitle {
            margin-top: 8px;

            font-size: clamp(22px, 6vw, 30px);

            line-height: 1.2;

            color: #8b8b8b;

            letter-spacing: -0.8px;
        }


        /* =================================================
           ACTION BUTTON AREA
           ================================================= */

        .anis-tool-title {
            color: #777777;

            font-size: 13px;

            margin-bottom: 10px;

            padding-left: 3px;
        }


        .anis-tools {
            display: grid;

            grid-template-columns: 1fr 1fr;

            gap: 10px;

            width: 100%;
        }


        .anis-tool-card {
            min-height: 88px;

            padding: 16px;

            border-radius: 20px;

            background: #181818;

            border: 1px solid #292929;

            box-sizing: border-box;

            display: flex;

            flex-direction: column;

            justify-content: space-between;

            transition: all .15s ease;
        }


        .anis-tool-icon {
            font-size: 22px;

            line-height: 1;
        }


        .anis-tool-name {
            color: #eeeeee;

            font-size: 14px;

            font-weight: 500;
        }


        .anis-tool-description {
            color: #777777;

            font-size: 11px;

            margin-top: 3px;
        }


        /* =================================================
           SMALL PHONE
           ================================================= */

        @media (max-width: 360px) {

            .anis-home-screen {
                padding-left: 2px;
                padding-right: 2px;
            }

            .anis-tools {
                gap: 7px;
            }

            .anis-tool-card {
                min-height: 82px;
                padding: 13px;
                border-radius: 17px;
            }

            .anis-tool-name {
                font-size: 13px;
            }
        }

        </style>


        <div class="anis-home-screen">

            <div class="anis-welcome">

                <div class="anis-welcome-title">
                    Hi Anis
                </div>

                <div class="anis-welcome-subtitle">
                    Where should we start?
                </div>

            </div>


            <div class="anis-tool-title">
                Explore Anis AI
            </div>


            <div class="anis-tools">

                <div class="anis-tool-card">

                    <div class="anis-tool-icon">
                        🖼️
                    </div>

                    <div>
                        <div class="anis-tool-name">
                            Create image
                        </div>

                        <div class="anis-tool-description">
                            Create images with AI
                        </div>
                    </div>

                </div>


                <div class="anis-tool-card">

                    <div class="anis-tool-icon">
                        📝
                    </div>

                    <div>
                        <div class="anis-tool-name">
                            Create MCQ
                        </div>

                        <div class="anis-tool-description">
                            Generate smart questions
                        </div>
                    </div>

                </div>


                <div class="anis-tool-card">

                    <div class="anis-tool-icon">
                        🔍
                    </div>

                    <div>
                        <div class="anis-tool-name">
                            Analyze
                        </div>

                        <div class="anis-tool-description">
                            Analyze text or images
                        </div>
                    </div>

                </div>


                <div class="anis-tool-card">

                    <div class="anis-tool-icon">
                        📚
                    </div>

                    <div>
                        <div class="anis-tool-name">
                            Help me learn
                        </div>

                        <div class="anis-tool-description">
                            Learn anything simply
                        </div>
                    </div>

                </div>

            </div>

        </div>
        """,
        unsafe_allow_html=True
    )


    # =====================================================
    # FUNCTIONAL TOOL BUTTONS
    # =====================================================

    tool_col1, tool_col2 = st.columns(2)

    with tool_col1:

        if st.button(
            "📝 Create MCQ",
            use_container_width=True,
            key="home_create_mcq",
        ):

            st.session_state.active_mode = "mcq"

            st.session_state.messages.append(
                {
                    "role": "user",
                    "content": "I want to create MCQs."
                }
            )

            st.rerun()


        if st.button(
            "🔍 Analyze",
            use_container_width=True,
            key="home_analyze",
        ):

            st.session_state.active_mode = "analyze"

            st.session_state.messages.append(
                {
                    "role": "user",
                    "content": "I want to analyze something."
                }
            )

            st.rerun()


    with tool_col2:

        if st.button(
            "📚 Help Me Learn",
            use_container_width=True,
            key="home_learn",
        ):

            st.session_state.active_mode = "learn"

            st.session_state.messages.append(
                {
                    "role": "user",
                    "content": "Help me learn."
                }
            )

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
    
