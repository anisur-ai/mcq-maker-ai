import streamlit as st
from groq import Groq
from helpers import ocr_space_file, generate_prompt, create_docx

# Streamlit Config
st.set_page_config(page_title="Anis MCQ Maker AI", layout="wide")

# ultra-professional & attractive CSS Design
custom_css = """
<style>
    .stApp {
        background: radial-gradient(circle at 50% -20%, #1e1b4b, #0f172a, #020617);
        color: #f8fafc;
        font-family: 'Inter', sans-serif;
    }
    section[data-testid="stSidebar"] {
        background: rgba(15, 23, 42, 0.65) !important;
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border-right: 1px solid rgba(255, 255, 255, 0.08);
    }
    .glowing-title {
        font-size: 2.5rem;
        font-weight: 800;
        text-align: center;
        background: linear-gradient(135deg, #38bdf8 0%, #818cf8 50%, #c084fc 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-shadow: 0 0 30px rgba(129, 140, 248, 0.35);
        letter-spacing: 0.5px;
        margin-bottom: 25px;
        padding: 10px 0;
    }
    .stTextArea textarea, .stSelectbox select, .stTextInput input {
        background-color: rgba(30, 41, 59, 0.7) !important;
        color: #f8fafc !important;
        border: 1px solid rgba(255, 255, 255, 0.12) !important;
        border-radius: 12px !important;
    }
    .stTextArea textarea:focus, .stTextInput input:focus {
        border-color: #818cf8 !important;
        box-shadow: 0 0 10px rgba(129, 140, 248, 0.5) !important;
    }
    div.stButton > button {
        background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 50%, #d946ef 100%);
        color: #ffffff;
        border: none;
        border-radius: 10px;
        font-weight: 700;
        font-size: 1.05rem;
        padding: 12px 24px;
        box-shadow: 0 4px 20px rgba(124, 58, 237, 0.4);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }
    div.stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(217, 70, 239, 0.6);
        color: #ffffff;
    }
    .stAlert {
        border-radius: 12px !important;
        backdrop-filter: blur(8px);
    }
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

groq_api_key = st.secrets.get("GROQ_API_KEY")
ocr_api_key = st.secrets.get("OCR_API_KEY")

if not groq_api_key:
    st.error("⚠️ GROQ_API_KEY পাওয়া যায়নি! / GROQ_API_KEY not found!")
    st.stop()

client = Groq(api_key=groq_api_key)

# হেডার
st.markdown('<div class="glowing-title">📚 Anis MCQ Maker AI 📚</div>', unsafe_allow_html=True)

# Sidebar Options
st.sidebar.header("⚙️ কাস্টমাইজেশন / Options")

# ভাষা নির্বাচন
lang = st.sidebar.selectbox("ভাষা / Language", ["বাংলা", "English", "দ্বিভাষিক (Bilingual)"])

# ভাষার ওপর নির্ভর করে ইন্টারফেসের লেখা পরিবর্তন (Dynamic UI Text)
if lang == "English":
    lbl_subject = "Subject"
    lbl_class = "Enter Class (5 to 12)"
    lbl_diff = "Difficulty Level"
    lbl_qtype = "Question Type"
    lbl_ocr_lang = "OCR Language (If image used)"
    lbl_num_q = "Number of Questions"
    lbl_text_input = "Paste your study material or ask anything here:"
    lbl_upload = "Or upload image of material (JPG/PNG):"
    lbl_custom = "Special Instructions (Optional):"
    lbl_btn = "Generate MCQ 🚀"
    lbl_msg_low_class = "⚠️ This app is meant for Class 5 to Class 12."
    lbl_msg_high_class = "⚠️ Only Class 5 to Class 12 supported."
    lbl_msg_invalid_class = "💡 Please enter digits only (e.g., 7, 8, 10)."
else:
    lbl_subject = "বিষয় (Subject)"
    lbl_class = "শ্রেণী লিখুন (Class 5 থেকে 12)"
    lbl_diff = "কঠিনতার মাত্রা"
    lbl_qtype = "প্রশ্নের ধরন"
    lbl_ocr_lang = "OCR পড়ার ভাষা (ছবি থাকলে)"
    lbl_num_q = "প্রশ্নের সংখ্যা লিখুন"
    lbl_text_input = "পড়াটি পেস্ট করুন বা যেকোনো প্রশ্ন লিখুন:"
    lbl_upload = "অথবা পড়ার ছবি তুলে আপলোড করুন (JPG/PNG):"
    lbl_custom = "বিশেষ নির্দেশ (ঐচ্ছিক):"
    lbl_btn = "MCQ তৈরি করুন 🚀"
    lbl_msg_low_class = "⚠️ এই অ্যাপটি মূলত ৫ম থেকে ১২শ শ্রেণীর জন্য প্রযোজ্য।"
    lbl_msg_high_class = "⚠️ শুধুমাত্র Class 5 থেকে Class 12 পর্যন্ত প্রযোজ্য।"
    lbl_msg_invalid_class = "💡 অনুগ্রহ করে ক্লাসের শুধু সংখ্যাটি লিখুন (যেমন: 7, 8, 10)।"

subject = st.sidebar.selectbox(lbl_subject, ["ইতিহাস / History", "ভূগোল / Geography", "জীবনবিজ্ঞান / Life Science", "গণিত / Math", "বাংলা / Bengali", "ইংরেজি / English"])

# ক্লাস হাতে লেখার ইনপুট ও ভ্যালিডেশন
class_num_input = st.sidebar.text_input(lbl_class, value="7")
cls = f"Class {class_num_input}"
try:
    c_num = int(class_num_input.strip())
    if c_num < 5:
        st.sidebar.warning(lbl_msg_low_class)
    elif c_num > 12:
        st.sidebar.warning(lbl_msg_high_class)
except ValueError:
    st.sidebar.info(lbl_msg_invalid_class)

difficulty = st.sidebar.selectbox(lbl_diff, ["সহজ / Easy", "মাঝারি / Medium", "কঠিন / Hard"])
q_type = st.sidebar.selectbox(lbl_qtype, ["MCQ", "True/False", "Fill in the blanks", "Short Answer"])

ocr_lang_choice = st.sidebar.radio(lbl_ocr_lang, ["বাংলা (ben)", "English (eng)"])
ocr_lang_code = "ben" if "ben" in ocr_lang_choice else "eng"

bloom = st.sidebar.selectbox("Bloom's Taxonomy", ["Knowledge", "Understanding", "Application", "Analysis"])
num_questions_str = st.sidebar.text_input(lbl_num_q, value="10")
temperature_mode = st.sidebar.select_slider("AI Mode", options=["Accurate", "Balanced", "Creative"], value="Balanced")
temp_map = {"Accurate": 0.2, "Balanced": 0.7, "Creative": 1.0}

# ইনপুট সেকশন
text_input = st.text_area(lbl_text_input, height=150)
uploaded_file = st.file_uploader(lbl_upload, type=["jpg", "jpeg", "png"])
custom_instruction = st.text_input(lbl_custom)

if st.button(lbl_btn, use_container_width=True):
    final_text = ""
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        num_questions = int(num_questions_str)
    except ValueError:
        num_questions = 10

    if uploaded_file:
        if not ocr_api_key:
            st.error("⚠️ OCR_API_KEY পাওয়া যায়নি / OCR_API_KEY missing!")
            st.stop()
            
        status_text.text("📷 Reading text from image (OCR)...")
        progress_bar.progress(30)
        
        ocr_text, status = ocr_space_file(uploaded_file, ocr_api_key, language=ocr_lang_code)
        
        if status == "LIMIT_EXCEEDED":
            st.error("⚠️ OCR daily limit exceeded! Please paste raw text.")
            progress_bar.empty()
            status_text.empty()
            st.stop()
        elif status == "LOW_CONFIDENCE":
            st.warning("⚠️ Low text detected from image.")
            final_text = ocr_text
        elif ocr_text:
            final_text = ocr_text
            st.success("✅ OCR text extraction complete!")
        else:
            st.error("Could not read text from image.")
            progress_bar.empty()
            status_text.empty()
            st.stop()
            
    elif text_input:
        final_text = text_input

    if final_text:
        status_text.text("🤖 AI is processing...")
        progress_bar.progress(70)
        
        try:
            prompt = generate_prompt(
                num_questions, final_text, difficulty, q_type, lang, 
                subject, cls, bloom, temp_map[temperature_mode], custom_instruction
            )
            
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                temperature=temp_map[temperature_mode]
            )
            
            output_text = response.choices[0].message.content
            st.session_state['last_mcq'] = output_text
            
            progress_bar.progress(100)
            status_text.text("✅ Ready!")
            progress_bar.empty()
            status_text.empty()
            
        except Exception:
            st.error("⚠️ Error generating response. Please try again.")
            progress_bar.empty()
            status_text.empty()
    else:
        st.warning("Please provide text or upload an image.")

# আউটপুট প্রদর্শনের অংশ
if 'last_mcq' in st.session_state:
    full_output = st.session_state['last_mcq']
    
    # সাধারণ কথাবার্তা হলে সরাসরি উত্তর দেখাবে, আর প্রশ্নপত্র তৈরি হলে উত্তরমালা আলাদা দেখাবে
    if "---ANSWER_KEY---" in full_output:
        parts = full_output.split("---ANSWER_KEY---")
        questions_part = parts[0]
        answers_part = parts[1]
    else:
        questions_part = full_output
        answers_part = None

    st.success("✅ Output Generated Successfully!")
    
    st.markdown("### 📄 Result / Response")
    st.write(questions_part)
    
    st.code(questions_part, language="text")
    
    if answers_part:
        with st.expander("👁️ View Answer Key & Explanations"):
            st.markdown(answers_part)
            
        st.write("---")
        with st.expander("📝 Quiz Mode"):
            st.info("Test your knowledge interactively:")
            q_sample = st.radio("Select the correct option:", ["Option A", "Option B", "Option C", "Option D"])
            if st.button("Submit Answer"):
                st.success("🎉 Answer Submitted!")

        st.subheader("📥 Export File")
        docx_file = create_docx(full_output, subject=subject, cls=cls)
        with open(docx_file, "rb") as fp:
            st.download_button(label="📄 Download DOCX", data=fp, file_name="MCQs.docx", use_container_width=True)
