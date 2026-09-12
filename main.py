# ============================================
# main.py — PART 4 START
# ============================================

# ===== ইনপুট বারের কন্ট্রোল রো ("+", মডেল সিলেক্টর, মাইক) =====
control_col1, control_col2, control_col3 = st.columns([1, 3, 1])

uploaded_image = None
voice_text = None

with control_col1:
    with st.popover("➕", use_container_width=True):
        uploaded_image = st.file_uploader(
            "ছবি পাঠান",
            type=["png", "jpg", "jpeg"],
            label_visibility="collapsed",
            key="image_uploader"
        )

with control_col2:
    selected_idx = 0
    if st.session_state.selected_model in model_list:
        selected_idx = model_list.index(st.session_state.selected_model)

    st.session_state.selected_model = st.selectbox(
        "মডেল",
        options=model_list,
        index=selected_idx,
        label_visibility="collapsed",
    )

with control_col3:
    with st.popover("🎤", use_container_width=True):
        audio_input = st.audio_input("কথা বলুন", label_visibility="collapsed")
        if audio_input is not None:
            voice_text = audio_input

# ছবি আপলোড হলে ছোট প্রিভিউ দেখানো
if uploaded_image is not None:
    st.image(uploaded_image, width=80, caption="সংযুক্ত ছবি")

# ============================================
# main.py — PART 4 END
# ============================================# ============================================
# main.py — PART 5 START
# ============================================

# ===== মূল টেক্সট ইনপুট বক্স =====
user_input = st.chat_input("Anis Ai-কে কিছু জিজ্ঞেস করুন...")

final_input = user_input
if final_input is None and voice_text is not None:
    final_input = "voice_input_placeholder"

# ===== ইউজার মেসেজ সাবমিট হলে যা ঘটবে =====
if final_input:

    display_text = final_input
    if uploaded_image is not None:
        display_text += "  📷 [ছবি সংযুক্ত]"

    st.session_state.messages.append({
        "role": "user",
        "content": display_text
    })

    with st.chat_message("user", avatar="🧑"):
        st.markdown(display_text)

    # ===== AI-এর উত্তর আনা =====
    with st.chat_message("assistant", avatar=LOGO_IMAGE):
        placeholder = st.empty()
        placeholder.markdown("⏳ *লিখছে...*")

        try:
            ai_result = get_ai_response(
                user_message=final_input,
                web_search_enabled=st.session_state.web_search_enabled,
                image_file=uploaded_image,
            )

            answer_text = ai_result.get("answer", "দুঃখিত, উত্তর তৈরি করা যায়নি।")
            model_used = st.session_state.selected_model

            placeholder.markdown(answer_text)
            st.caption(f"⚡ {model_used}")

            st.session_state.messages.append({