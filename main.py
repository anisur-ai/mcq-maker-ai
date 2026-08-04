import streamlit as st
import logging
import os
import io
from concurrent.futures import ThreadPoolExecutor, as_completed
from groq import Groq
from helpers import ocr_space_file, generate_prompt, create_docx

# Optional PDF generator support (ReportLab)
try:
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False

# Page Configuration
st.set_page_config(
    page_title="Anis MCQ Maker AI",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize Session States
if 'chat_memory' not in st.session_state:
    st.session_state['chat_memory'] = []

if 'history' not in st.session_state:
    st.session_state['history'] = []

if 'last_output' not in st.session_state:
    st.session_state['last_output'] = ""

if 'last_usage' not in st.session_state:
    st.session_state['last_usage'] = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}

# ULTRA-MODERN GLASSMORPHISM & PREMIUM UI CSS
custom_css = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }

    .stApp {
        background: radial-gradient(circle at 15% 15%, #0f172a 0%, #020617 100%);
        color: #f1f5f9;
    }

    section[data-testid="stSidebar"] {
        background: rgba(15, 23, 42, 0.55) !important;
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border-right: 1px solid rgba(255, 255, 255, 0.08);
    }

    .hero-container {
        text-align: center;
        padding: 2.5rem 1rem 1.5rem 1rem;
        background: rgba(30, 41, 59, 0.3);
        backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 24px;
        margin-bottom: 2rem;
        box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
    }

    .hero-title {
        font-size: 2.8rem;
        font-weight: 800;
        letter-spacing: -1px;
        background: linear-gradient(135deg, #38bdf8 0%, #818cf8 50%, #c084fc 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }

    .hero-subtitle {
        color: #94a3b8;
        font-size: 1.05rem;
        font-weight: 500;
    }

    div.stButton > button {
        background: linear-gradient(135deg, #6366f1 0%, #a855f7 50%, #ec4899 100%) !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 14px !important;
        font-weight: 700 !important;
        font-size: 1.1rem !important;
        padding: 14px 28px !important;
        box-shadow: 0 8px 25px rgba(168, 85, 247, 0.35) !important;
        transition: all 0.3s ease !important;
    }

    div.stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 12px 30px rgba(168, 85, 247, 0.5) !important;
    }

    .stTextArea textarea, .stTextInput input {
        background: rgba(15, 23, 42, 0.6) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 14px !important;
        color: #f8fafc !important;
        backdrop-filter: blur(10px);
    }

    .stTextArea textarea:focus, .stTextInput input:focus {
        border-color: #818cf8 !important;
        box-shadow: 0 0 15px rgba(129, 140, 248, 0.3) !important;
    }

    section[data-testid="stFileUploadDropzone"] {
        background: rgba(30, 41, 59, 0.4) !important;
        border: 2px dashed rgba(129, 140, 248, 0.4) !important;
        border-radius: 16px !important;
    }

    .result-card {
        background: rgba(15, 23, 42, 0.7);
        backdrop-filter: blur(16px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 20px;
        padding: 2rem;
        margin-top: 1.5rem;
        box-shadow: 0 15px 35px rgba(0, 0, 0, 0.4);
    }

    .badge-tag {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
        background: rgba(99, 102, 241, 0.2);
        color: #818cf8;
        border: 1px solid rgba(129, 140, 248, 0.3);
        margin-bottom: 1rem;
    }
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# API Keys Check
groq_api_key = st.secrets.get("GROQ_API_KEY")
ocr_api_key = st.secrets.get("OCR_API_KEY")

if not groq_api_key:
    st.error("⚠️ GROQ_API_KEY পাওয়া যায়নি! অনুগ্রহ করে Streamlit Secrets থেকে API Key যোগ করুন।")
    st.stop()

client = Groq(api_key=groq_api_key)

# Dynamic Model Dictionary (Non-Hardcoded constant setup)
MODELS = {
    "Best Quality (Llama 3.3 70B)": "llama-3.3-70b-versatile",
    "Fast (Llama 3.1 8B)": "llama-3.1-8b-instant",
    "Balanced (Mixtral 8x7B)": "mixtral-8x7b-32768"
}

# Cached OCR function to prevent redundant API hits for same images
@st.cache_data(show_spinner=False)
def cached_ocr_process(file_bytes, file_name, api_key, lang_code):
    uploaded_file_obj = io.BytesIO(file_bytes)
    uploaded_file_obj.name = file_name
    return ocr_space_file(uploaded_file_obj, api_key, language=lang_code)

# Helper for PDF generation
def create_pdf(text_content, subject, cls):
    if not PDF_SUPPORT:
        return None
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=16,
        textColor=colors.HexColor('#1e293b') if 'colors' in globals() else None,
        spaceAfter=12
    )
    
    body_style = ParagraphStyle(
        'BodyStyle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=11,
        spaceAfter=8,
        leading=14
    )
    
    story = [Paragraph(f"<b>Subject:</b> {subject} | <b>Class:</b> {cls}", title_style), Spacer(1, 10)]
    
    for line in text_content.split('\n'):
        if line.strip():
            story.append(Paragraph(line, body_style))
        else:
            story.append(Spacer(1, 6))
            
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()

# App Hero Banner
st.markdown("""
<div class="hero-container">
    <div class="hero-title">⚡ Anis MCQ Maker AI</div>
    <div class="hero-subtitle">স্মার্ট এডুকেশনাল প্রশ্নপত্র ও নোট তৈরির অল-ইন-ওয়ান AI অ্যাসিস্ট্যান্ট</div>
</div>
""", unsafe_allow_html=True)

# Sidebar UI
st.sidebar.markdown("### ⚙️ কনফিগারেশন / Options")

selected_model_label = st.sidebar.selectbox("🤖 AI Model / Engine", list(MODELS.keys()), index=0)
selected_model = MODELS[selected_model_label]

lang = st.sidebar.selectbox("🌐 ভাষা / Language", ["বাংলা", "English", "দ্বিভাষিক (Bilingual)"])

if lang == "English":
    lbl_subject, lbl_class = "Subject", "Enter Class (5 to 12)"
    lbl_diff, lbl_qtype = "Difficulty Level", "Question Type"
    lbl_text_input = "Paste study material, notes or ask any question:"
    lbl_upload = "Or upload images (Multiple JPG/PNG supported):"
    lbl_btn = "Generate Response 🚀"
else:
    lbl_subject, lbl_class = "বিষয় (Subject)", "শ্রেণী (Class 5 থেকে 12)"
    lbl_diff, lbl_qtype = "কঠিনতার মাত্রা", "প্রশ্নের ধরন"
    lbl_text_input = "পড়া পেস্ট করুন, টপিক লিখুন বা প্রশ্ন করুন:"
    lbl_upload = "অথবা একাধিক ছবি আপলোড করুন (JPG/PNG):"
    lbl_btn = "আউটপুট তৈরি করুন 🚀"

subject = st.sidebar.selectbox(lbl_subject, ["ইতিহাস / History", "ভূগোল / Geography", "জীবনবিজ্ঞান / Life Science", "গণিত / Math", "বাংলা / Bengali", "ইংরেজি / English"])
class_num_input = st.sidebar.text_input(lbl_class, value="7")

try:
    cls_val = int(class_num_input.strip())
    if cls_val < 5 or cls_val > 12:
        st.sidebar.warning("⚠️ শ্রেণী Class 5 থেকে 12-এর মধ্যে হওয়া বাঞ্ছনীয়।")
except ValueError:
    st.sidebar.warning("⚠️ সঠিক শ্রেণী সংখ্যা লিখুন (যেমন: 7)।")

cls = f"Class {class_num_input.strip()}"

difficulty = st.sidebar.selectbox(lbl_diff, ["সহজ / Easy", "মাঝারি / Medium", "কঠিন / Hard"])
q_type = st.sidebar.selectbox(lbl_qtype, ["MCQ", "True/False", "Fill in the blanks", "Short Answer"])
ocr_lang_code = "ben" if "বাংলা" in lang else "eng"

bloom = st.sidebar.selectbox("Bloom's Taxonomy Level", ["Knowledge", "Understanding", "Application", "Analysis"])
num_questions_str = st.sidebar.text_input("প্রশ্নের সংখ্যা", value="10")
temperature_mode = st.sidebar.select_slider("AI Creative Engine", options=["Accurate", "Balanced", "Creative"], value="Balanced")
temp_map = {"Accurate": 0.2, "Balanced": 0.7, "Creative": 1.0}

developer_mode = st.sidebar.checkbox("🛠️ Developer / Debug Mode", value=False)

# Token Usage & Estimated Cost Tracker (Sidebar)
if st.sidebar.checkbox("📊 Token & Cost Tracker", value=True):
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🧮 Token Stats")
    st.sidebar.text(f"Prompt Tokens: {st.session_state['last_usage']['prompt_tokens']}")
    st.sidebar.text(f"Completion Tokens: {st.session_state['last_usage']['completion_tokens']}")
    st.sidebar.text(f"Total Tokens: {st.session_state['last_usage']['total_tokens']}")
    # Approximate cost estimation for Llama 3.3 70B (Roughly $0.59 per 1M tokens combined)
    approx_cost = (st.session_state['last_usage']['total_tokens'] / 1_000_000) * 0.59
    st.sidebar.text(f"Estimated Cost: ${approx_cost:.6f}")

if st.sidebar.button("🧹 Clear Chat Memory"):
    st.session_state['chat_memory'] = []
    st.sidebar.success("কনভার্সেশন মেমরি ক্লিয়ার করা হয়েছে!")

# Main Input Section
text_input = st.text_area(lbl_text_input, height=140, placeholder="এখানে আপনার পড়ার অংশ পেস্ট করুন, টপিক লিখুন বা প্রশ্ন করুন...")
uploaded_files = st.file_uploader(lbl_upload, type=["jpg", "jpeg", "png"], accept_multiple_files=True)

if uploaded_files and len(uploaded_files) > 10:
    st.warning("⚠️ একবারে সর্বোচ্চ ১০টি ছবি আপলোড করা যাবে।")
    st.stop()

custom_instruction = st.text_input("🎯 বিশেষ নির্দেশ (ঐচ্ছিক):", placeholder="যেমন: প্রশ্নগুলো একটু ঘুরিয়ে তৈরি করো...")

# Generate or Retry Trigger Button
col_btn1, col_btn2 = st.columns([4, 1])
with col_btn1:
    generate_clicked = st.button(lbl_btn, use_container_width=True)
with col_btn2:
    retry_clicked = st.button("🔄 Retry", use_container_width=True)

if generate_clicked or retry_clicked:
    combined_ocr_text = ""
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        num_questions = int(num_questions_str)
    except ValueError:
        num_questions = 10

    # Parallel OCR Extraction using ThreadPoolExecutor for high-speed processing
    if uploaded_files:
        if not ocr_api_key:
            st.error("⚠️ OCR_API_KEY পাওয়া যায়নি!")
            st.stop()
            
        def process_single_image(idx_file):
            idx, file = idx_file
            file_bytes = file.read()
            file.seek(0)
            ocr_text, status = cached_ocr_process(file_bytes, file.name, ocr_api_key, ocr_lang_code)
            return idx, ocr_text, status

        status_text.text("📷 প্যারালাল OCR প্রসেসিং চলছে...")
        progress_bar.progress(30)
        
        ocr_results = {}
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {executor.submit(process_single_image, (i, f)): i for i, f in enumerate(uploaded_files)}
            for future in as_completed(futures):
                idx, ocr_text, status = future.result()
                if status in ["SUCCESS", "LOW_CONFIDENCE"]:
                    ocr_results[idx] = ocr_text

        for idx in sorted(ocr_results.keys()):
            combined_ocr_text += f"\n=== Image {idx+1} Text ===\n" + ocr_results[idx] + "\n"

    # Combine text inputs and OCR text
    final_text = f"{text_input.strip()}\n\n{combined_ocr_text.strip()}".strip()

    if final_text:
        status_text.text("🧠 AI প্রম্পট ও Intent বিশ্লেষণ করছে...")
        progress_bar.progress(60)
        
        try:
            # System Instruction Generation
            system_instruction = generate_prompt(
                num_questions, final_text, difficulty, q_type, lang, 
                subject, cls, bloom, temp_map[temperature_mode], custom_instruction
            )
            
            # Message chain with capped memory (last 12 items)
            messages = [{"role": "system", "content": system_instruction}]
            for msg in st.session_state['chat_memory'][-12:]:
                messages.append(msg)
            messages.append({"role": "user", "content": final_text})
            
            progress_bar.progress(100)
            status_text.empty()
            progress_bar.empty()

            st.markdown('<div class="result-card">', unsafe_allow_html=True)
            st.markdown('<span class="badge-tag">✨ AI STREAMING OUTPUT</span>', unsafe_allow_html=True)
            st.markdown("### 📄 আউটপুট / রেসপন্স")
            
            response_container = st.empty()
            full_output = ""
            
            # API Completion Call with Streaming Optimization
            completion = client.chat.completions.create(
                model=selected_model,
                messages=messages,
                temperature=temp_map[temperature_mode],
                max_completion_tokens=4096,
                stream=True
            )
            
            for chunk in completion:
                if chunk.choices and chunk.choices[0].delta and chunk.choices[0].delta.content:
                    delta = chunk.choices[0].delta.content
                    full_output += delta
                    # Optimized rendering update frequency to prevent UI lag
                    if len(full_output) % 60 == 0:
                        response_container.markdown(full_output + "▌")
                
            response_container.markdown(full_output)
            
            # Approximate token computation for tracker
            prompt_chars = sum(len(m['content']) for m in messages)
            comp_chars = len(full_output)
            st.session_state['last_usage'] = {
                "prompt_tokens": prompt_chars // 4,
                "completion_tokens": comp_chars // 4,
                "total_tokens": (prompt_chars + comp_chars) // 4
            }
            
            # Update Chat Memory & History
            st.session_state['chat_memory'].append({"role": "user", "content": final_text})
            st.session_state['chat_memory'].append({"role": "assistant", "content": full_output})
            st.session_state['chat_memory'] = st.session_state['chat_memory'][-12:]
            
            st.session_state['last_output'] = full_output
            st.session_state['history'].append({"subject": subject, "text": full_output})
            st.session_state['history'] = st.session_state['history'][-20:]

            # Answer Key Parsing & Display Section
            if "---ANSWER_KEY---" in full_output:
                parts = full_output.split("---ANSWER_KEY---")
                questions_part, answers_part = parts[0], parts[1]
            else:
                questions_part, answers_part = full_output, None
            
            col_exp1, col_exp2 = st.columns(2)
            with col_exp1:
                with st.expander("📋 মূল টেক্সট দেখুন"):
                    st.code(questions_part, language="text")
            with col_exp2:
                if answers_part:
                    with st.expander("👁️ উত্তরমালা ও ব্যাখ্যা দেখুন"):
                        st.markdown(answers_part)

            # File Export Section (DOCX & PDF)
            st.write("---")
            st.subheader("📥 ফাইল ডাউনলোড")
            
            col_dl1, col_dl2 = st.columns(2)
            
            docx_path = create_docx(full_output, subject=subject, cls=cls)
            with open(docx_path, "rb") as fp:
                docx_data = fp.read()
            try:
                os.remove(docx_path)
            except Exception:
                pass
                
            with col_dl1:
                st.download_button(
                    label="📄 Download DOCX (Word)", 
                    data=docx_data, 
                    file_name=f"{subject}_{cls}_Questions.docx", 
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    use_container_width=True
                )
                
            if PDF_SUPPORT:
                pdf_data = create_pdf(full_output, subject, cls)
                with col_dl2:
                    st.download_button(
                        label="📑 Download PDF (Acrobat)", 
                        data=pdf_data, 
                        file_name=f"{subject}_{cls}_Questions.pdf", 
                        mime="application/pdf",
                        use_container_width=True
                    )
            
            st.markdown('</div>', unsafe_allow_html=True)

        except Exception as e:
            progress_bar.empty()
            status_text.empty()
            st.error("⚠️ AI থেকে উত্তর পেতে সমস্যা হয়েছে।")
            if developer_mode:
                st.exception(e)
            else:
                logging.exception("Groq API Call Error")
    else:
        st.warning("অনুগ্রহ করে কোনো পড়া পেস্ট করুন, প্রশ্ন লিখুন অথবা ছবি আপলোড করুন।")

# Session History Display
if st.session_state['history']:
    st.write("---")
    with st.expander("📜 পূর্ববর্তী তৈরি করা রেসপন্স (সর্বশেষ ২০টি)"):
        for idx, item in enumerate(reversed(st.session_state['history'])):
            st.markdown(f"**{idx+1}. Subject: {item['subject']}**")
            st.caption(item['text'][:140] + "...")
    
