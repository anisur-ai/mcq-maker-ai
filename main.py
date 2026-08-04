import streamlit as st
import logging
import os
from groq import Groq
from helpers import ocr_space_file, generate_prompt, create_docx

# Streamlit Config
st.set_page_config(page_title="Anis MCQ Maker AI", layout="wide")

# Session State Initialization (Up to 20 items in history)
if 'history' not in st.session_state:
    st.session_state['history'] = []

# Glassmorphism UI Design
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
        margin-bottom: 25px;
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
    }
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# API Keys Checking
groq_api_key = st.secrets.get("GROQ_API_KEY")
ocr_api_key = st.secrets.get("OCR_API_KEY")

if not groq_api_key:
    st.error("⚠️ GROQ_API_KEY পাওয়া যায়নি! অনুগ্রহ করে Streamlit Secrets থেকে API Key যোগ করুন।")
    st.stop()

client = Groq(api_key=groq_api_key)

st.markdown('<div class="glowing-title">📚 Anis MCQ Maker AI 📚</div>', unsafe_allow_html=True)

# Sidebar Options
st.sidebar.header("⚙️ অপশনস / Sidebar Settings")
lang = st.sidebar.selectbox("ভাষা / Language", ["বাংলা", "English", "দ্বিভাষিক (Bilingual)"])

if lang == "English":
    lbl_subject, lbl_class = "Subject", "Enter Class (5 to 12)"
    lbl_diff, lbl_qtype = "Difficulty Level", "Question Type"
    lbl_text_input = "Paste study material or ask anything here:"
    lbl_upload = "Or upload images (Multiple supported JPG/PNG):"
    lbl_btn = "Generate Output 🚀"
else:
    lbl_subject, lbl_class = "বিষয় (Subject)", "শ্রেণী লিখুন (Class 5 থেকে 12)"
    lbl_diff, lbl_qtype = "কঠিনতার মাত্রা", "প্রশ্নের ধরন"
    lbl_text_input = "পড়াটি পেস্ট করুন বা যেকোনো প্রশ্ন লিখুন:"
    lbl_upload = "অথবা একাধিক ছবি আপলোড করুন (JPG/PNG):"
    lbl_btn = "আউটপুট তৈরি করুন 🚀"

subject = st.sidebar.selectbox(lbl_subject, ["ইতিহাস / History", "ভূগোল / Geography", "জীবনবিজ্ঞান / Life Science", "গণিত / Math", "বাংলা / Bengali", "ইংরেজি / English"])
class_num_input = st.sidebar.text_input(lbl_class, value="7")

# Class Validation Logic
try:
    cls_val = int(class_num_input.strip())
    if cls_val < 5 or cls_val > 12:
        st.sidebar.warning("⚠️ শ্রেণী সাধারণত Class 5 থেকে 12 এর মধ্যে রাখা ভালো।")
except ValueError:
    st.sidebar.warning("⚠️ শ্রেণীর ঘরে সঠিক সংখ্যা লিখুন (যেমন: 7)।")

cls = f"Class {class_num_input.strip()}"

difficulty = st.sidebar.selectbox(lbl_diff, ["সহজ / Easy", "মাঝারি / Medium", "কঠিন / Hard"])
q_type = st.sidebar.selectbox(lbl_qtype, ["MCQ", "True/False", "Fill in the blanks", "Short Answer"])
ocr_lang_code = "ben" if "বাংলা" in lang else "eng"

bloom = st.sidebar.selectbox("Bloom's Taxonomy", ["Knowledge", "Understanding", "Application", "Analysis"])
num_questions_str = st.sidebar.text_input("প্রশ্নের সংখ্যা", value="10")
temperature_mode = st.sidebar.select_slider("AI Mode", options=["Accurate", "Balanced", "Creative"], value="Balanced")
temp_map = {"Accurate": 0.2, "Balanced": 0.7, "Creative": 1.0}

# Main Form Area
text_input = st.text_area(lbl_text_input, height=150)
uploaded_files = st.file_uploader(lbl_upload, type=["jpg", "jpeg", "png"], accept_multiple_files=True)
custom_instruction = st.text_input("বিশেষ নির্দেশ (ঐচ্ছিক):")

if st.button(lbl_btn, use_container_width=True):
    combined_ocr_text = ""
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        num_questions = int(num_questions_str)
    except ValueError:
        num_questions = 10

    # Process Multiple Images
    if uploaded_files:
        if not ocr_api_key:
            st.error("⚠️ OCR_API_KEY পাওয়া যায়নি!")
            st.stop()
            
        for idx, file in enumerate(uploaded_files):
            status_text.text(f"📷 Extracting text from image {idx+1}/{len(uploaded_files)}...")
            progress_bar.progress(int((idx + 1) / len(uploaded_files) * 40))
            
            ocr_text, status = ocr_space_file(file, ocr_api_key, language=ocr_lang_code)
            
            if status == "SUCCESS":
                combined_ocr_text += f"\n=== Image {idx+1} Text ===\n" + ocr_text + "\n"
            elif status == "LIMIT_EXCEEDED":
                st.error(f"⚠️ ছবি {idx+1}: OCR Free Limit শেষ হয়ে গেছে।")
            elif status == "LOW_CONFIDENCE":
                st.warning(f"⚠️ ছবি {idx+1}: ছবির লেখা খুব আবছা।")
                combined_ocr_text += f"\n=== Image {idx+1} Text ===\n" + ocr_text + "\n"
            elif status == "NO_TEXT":
                st.warning(f"⚠️ ছবি {idx+1}: কোনো পড়া খুঁজে পাওয়া যায়নি।")
            else:
                st.error(f"⚠️ ছবি {idx+1}: OCR সার্ভারে সংযোগের সমস্যা।")
                
        final_text = combined_ocr_text
    else:
        final_text = text_input

    if final_text.strip():
        status_text.text("🤖 AI Processing...")
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
            
            # Save History
            st.session_state['history'].append({"subject": subject, "text": output_text})
            st.session_state['history'] = st.session_state['history'][-20:]
            
            progress_bar.progress(100)
            status_text.text("✅ সম্পূর্ণ হয়েছে!")
            progress_bar.empty()
            status_text.empty()
            
        except Exception as e:
            logging.exception("Groq API Call Error")
            st.error("⚠️ AI সার্ভিস থেকে রেসপন্স পেতে সমস্যা হয়েছে।")
            progress_bar.empty()
            status_text.empty()
    else:
        st.warning("অনুগ্রহ করে কোনো পড়া পেস্ট করুন অথবা ছবি আপলোড করুন।")

# Display Result & Export
if 'last_mcq' in st.session_state:
    full_output = st.session_state['last_mcq']
    
    if "---ANSWER_KEY---" in full_output:
        parts = full_output.split("---ANSWER_KEY---")
        questions_part, answers_part = parts[0], parts[1]
    else:
        questions_part, answers_part = full_output, None

    st.success("✅ আপনার রেসপন্স প্রস্তুত!")
    
    st.markdown("### 📄 Response / Question Paper")
    st.markdown(questions_part)
    
    st.markdown("#### 📋 One-Click Copy Text")
    st.code(questions_part, language="text")
    
    if answers_part:
        with st.expander("👁️ View Answer Key & Explanations"):
            st.markdown(answers_part)
            
    st.write("---")
    st.subheader("📥 Export File")
    
    docx_path = create_docx(full_output, subject=subject, cls=cls)
    
    with open(docx_path, "rb") as fp:
        st.download_button(
            label="📄 Download DOCX", 
            data=fp, 
            file_name=f"{subject}_{cls}_Questions.docx", 
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            use_container_width=True
        )
    
    # Safe Temporary File Clean Up
    try:
        os.remove(docx_path)
    except Exception:
        pass

# Session History Display
if st.session_state['history']:
    st.write("---")
    with st.expander("📜 Session History (সর্বশেষ ২০টি প্রশ্নপত্র)"):
        for idx, item in enumerate(reversed(st.session_state['history'])):
            st.markdown(f"**{idx+1}. Subject: {item['subject']}**")
            st.caption(item['text'][:150] + "...")
