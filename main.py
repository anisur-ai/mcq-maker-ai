import streamlit as st
from helpers import ocr_space_file, generate_prompt, four_layer_ai_fallback, create_docx

# Page Configuration
st.set_page_config(page_title="Anis MCQ Maker AI", page_icon="⚡", layout="wide")

# Load API Keys from Secrets Dictionary
keys_dict = {
    "groq": st.secrets.get("GROQ_API_KEY"),
    "gemini": st.secrets.get("GEMINI_API_KEY"),
    "mistral": st.secrets.get("MISTRAL_API_KEY"),
    "openrouter": st.secrets.get("OPENROUTER_API_KEY")
}
ocr_api_key = st.secrets.get("OCR_API_KEY")

# App Header
st.title("⚡ Anis MCQ Maker AI")
st.markdown("Your Smart Study Assistant")

# Sidebar Controls
st.sidebar.header("⚙️ Configuration")

subject = st.sidebar.text_input("Subject", "History")
cls = st.sidebar.selectbox("Class Level", ["Class 5", "Class 6", "Class 7", "Class 8", "Class 9", "Class 10", "Class 11", "Class 12"])
difficulty = st.sidebar.selectbox("Difficulty", ["Easy", "Medium", "Hard", "Expert"])
q_type = st.sidebar.selectbox("Question Type", ["MCQ (4 Options)", "True/False", "Fill in the Blanks", "Short Questions"])
num_questions = st.sidebar.slider("Number of Questions", 1, 25, 5)
lang = st.sidebar.selectbox("Language", ["Bengali", "English"])
bloom = st.sidebar.selectbox("Bloom's Taxonomy", ["Remembering", "Understanding", "Applying", "Analyzing"])

custom_instruction = st.sidebar.text_area("Custom Instructions (Optional)", "")

# Main Input Section
st.subheader("📖 Input Study Material")
input_method = st.radio("Choose Input Method", ["Text Input", "Upload Image / OCR"])

study_text = ""

if input_method == "Text Input":
    study_text = st.text_area("Paste your textbook chapter or notes here:", height=200)
else:
    uploaded_file = st.file_uploader("Upload an image of your book/notes", type=["jpg", "jpeg", "png"])
    if uploaded_file is not None:
        st.image(uploaded_file, caption="Uploaded Image", use_column_width=True)
        if st.button("Extract Text (OCR)"):
            if not ocr_api_key:
                st.error("OCR API Key missing in secrets!")
            else:
                with st.spinner("Extracting text from image..."):
                    extracted_text, status = ocr_space_file(uploaded_file, ocr_api_key, language="ben" if lang=="Bengali" else "eng")
                    if status in ["SUCCESS", "LOW_CONFIDENCE"]:
                        study_text = extracted_text
                        st.success("Text extracted successfully!")
                        st.text_area("Extracted Text Preview:", study_text, height=150)
                    else:
                        st.error(f"OCR Failed with status: {status}")

# Generate Button Action
if st.button("🚀 Generate Content / MCQs", type="primary"):
    if not study_text.strip():
        st.warning("Please provide some study material or text first!")
    else:
        # Prompt Generation
        final_prompt = generate_prompt(
            num_questions=num_questions,
            study_text=study_text,
            difficulty=difficulty,
            q_type=q_type,
            lang=lang,
            subject=subject,
            cls=cls,
            bloom=bloom,
            custom_instruction=custom_instruction
        )

        messages = [
            {"role": "system", "content": "You are a helpful and expert AI study assistant."},
            {"role": "user", "content": final_prompt}
        ]

        st.subheader("✨ Generated Output:")
        response_container = st.empty()
        full_output = ""
        has_error = False  # এরর স্ট্যাটাস ট্র্যাক করার জন্য ফ্ল্যাগ

        try:
            with st.spinner("Processing your request..."):
                default_primary_model = "llama-3.3-70b-versatile"
                
                stream_generator = four_layer_ai_fallback(
                    keys_dict=keys_dict,
                    selected_model=default_primary_model,
                    messages=messages,
                    max_tokens=4096
                )

                for chunk in stream_generator:
                    delta = chunk.choices[0].delta.content
                    full_output += delta
                    response_container.markdown(full_output + "▌")
                    
                    # যদি chunk.is_error True হয়, তাহলে ফ্ল্যাগ সেট হবে
                    if getattr(chunk, "is_error", False):
                        has_error = True

                response_container.markdown(full_output)

            # Word Document Download Option (ফ্ল্যাগ ফলস থাকলেই কেবল ডাউনলোড বাটন দেখাবে)
            if full_output and not has_error:
                docx_path = create_docx(full_output, subject=subject, cls=cls)
                with open(docx_path, "rb") as file:
                    st.download_button(
                        label="📥 Download as Word Document (.docx)",
                        data=file,
                        file_name=f"{subject}_{cls}_MCQs.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                    )

        except Exception as e:
            pass
