import streamlit as st
from groq import Groq
from helpers import ocr_space_file, generate_prompt, create_docx, create_pdf

# Streamlit Config
st.set_page_config(page_title="Anis MCQ Maker AI", layout="wide")

# CSS দিয়ে ব্যাকগ্রাউন্ড ও গ্লোয়িং হেডার স্টাইল
custom_css = """
<style>
    /* মূল ব্যাকগ্রাউন্ডে অ্যানিমেটেড গ্রেডিয়েন্ট */
    .stApp {
        background: linear-gradient(-45deg, #0f172a, #1e1b4b, #311042, #111827);
        background-size: 400% 400%;
        animation: gradientBG 12s ease infinite;
        color: #f8fafc;
    }

    @keyframes gradientBG {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }

    /* সাইডবার গ্লাস মোড */
    section[data-testid="stSidebar"] {
        background-color: rgba(15, 23, 42, 0.75) !important;
        backdrop-filter: blur(10px);
        border-right: 1px solid rgba(255, 255, 255, 0.1);
    }

    /* গ্লোয়িং হেডার টাইটেল */
    .glowing-title {
        font-size: 2.2rem;
        font-weight: 700;
        text-align: center;
        background: linear-gradient(90deg, #38bdf8, #818cf8, #c084fc);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-shadow: 0 0 15px rgba(129, 140, 248, 0.4);
        margin-bottom: 20px;
        padding: 5px 0;
    }

    /* বাটনের ডিজাইন */
    div.stButton > button {
        background: linear-gradient(90deg, #6366f1, #a855f7);
        color: white;
        border: none;
        border-radius: 8px;
        font-weight: bold;
        box-shadow: 0 0 15px rgba(168, 85, 247, 0.4);
        transition: all 0.3s ease;
    }
    
    div.stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 0 25px rgba(168, 85, 247, 0.8);
    }
</style>
"""

st.markdown(custom_css, unsafe_allow_html=True)

groq_api_key = st.secrets.get("GROQ_API_KEY")
ocr_api_key = st.secrets.get("OCR_API_KEY")

if not groq_api_key:
    st.error("⚠️ GROQ_API_KEY পাওয়া যায়নি!")
    st.stop()

client = Groq(api_key=groq_api_key)

# বইয়ের চিহ্ন সহ সুন্দর টাইটেল
st.markdown('<div class="glowing-title">📚 Anis MCQ Maker AI 📚</div>', unsafe_allow_html=True)

# Sidebar Options
st.sidebar.header("⚙️ কাস্টমাইজেশন অপশন")

subject = st.sidebar.selectbox("বিষয় (Subject)", ["ইতিহাস", "ভূগোল", "জীবনবিজ্ঞান", "গণিত", "বাংলা", "ইংরেজি"])
cls = st.sidebar.selectbox("শ্রেণী (Class)", [f"Class {i}" for i in range(5, 13)])
difficulty = st.sidebar.selectbox("কঠিনতার মাত্রা", ["সহজ", "মাঝারি", "কঠিন"])
q_type = st.sidebar.selectbox("প্রশ্নের ধরন", ["শুধু MCQ", "True/False", "Fill in the blanks", "Short Answer"])
lang = st.sidebar.selectbox("ভাষা", ["বাংলা", "English", "দ্বিভাষিক (Bilingual)"])
bloom = st.sidebar.selectbox("Bloom's Taxonomy", ["Knowledge", "Understanding", "Application", "Analysis"])

num_questions_str = st.sidebar.text_input("প্রশ্নের সংখ্যা লিখুন (যেমন: 10 বা 25)", value="10")

temperature_mode = st.sidebar.select_slider("AI মোড (Temperature)", options=["Accurate", "Balanced", "Creative"], value="Balanced")

temp_map = {"Accurate": 0.2, "Balanced": 0.7, "Creative": 1.0}

text_input = st.text_area("পড়াটি এখানে পেস্ট করুন:", height=150)
uploaded_file = st.file_uploader("অথবা পড়ার ছবি তুলে আপলোড করুন (JPG/PNG):", type=["jpg", "jpeg", "png"])
custom_instruction = st.text_input("বিশেষ নির্দেশ (ঐচ্ছিক):")

if st.button("MCQ তৈরি করুন 🚀", use_container_width=True):
    final_text = ""
    
    try:
        num_questions = int(num_questions_str)
    except ValueError:
        num_questions = 10

    if uploaded_file:
        if not ocr_api_key:
            st.error("⚠️ OCR_API_KEY পাওয়া যায়নি! Streamlit Secrets চেক করুন।")
            st.stop()
            
        with st.spinner("ছবি থেকে টেক্সট পড়া হচ্ছে..."):
            ocr_text = ocr_space_file(uploaded_file, ocr_api_key)
            if not ocr_text:
                st.error("ছবি থেকে লেখা পড়া যায়নি। অনুগ্রহ করে পরিষ্কার ছবি দিন।")
                st.stop()
            else:
                final_text = ocr_text
                st.success("✅ ছবি থেকে লেখা পড়া সম্পন্ন হয়েছে!")
                with st.expander("ছবি থেকে বের হওয়া লেখা দেখুন/এডিট করুন"):
                    final_text = st.text_area("OCR Text", value=final_text, height=100)
    elif text_input:
        final_text = text_input

    if final_text:
        with st.spinner("AI প্রশ্ন সাজাচ্ছে..."):
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
                
            except Exception:
                st.error("⚠️ দুঃখিত, প্রশ্ন তৈরি করার সময়ে সমস্যা হয়েছে। আবার চেষ্টা করুন।")
    else:
        st.warning("অনুগ্রহ করে কোনো লেখা দিন অথবা বইয়ের ছবি আপলোড করুন।")

if 'last_mcq' in st.session_state:
    st.success("✅ প্রশ্ন সফলভাবে তৈরি হয়েছে!")
    st.write(st.session_state['last_mcq'])
    
    st.subheader("📥 ফাইল এক্সপোর্ট করুন")
    col1, col2 = st.columns(2)
    
    with col1:
        docx_file = create_docx(st.session_state['last_mcq'])
        with open(docx_file, "rb") as fp:
            st.download_button(label="📄 Download DOCX", data=fp, file_name="MCQs.docx", use_container_width=True)
            
    with col2:
        pdf_file = create_pdf(st.session_state['last_mcq'])
        with open(pdf_file, "rb") as fp:
            st.download_button(label="📕 Download PDF", data=fp, file_name="MCQs.pdf", use_container_width=True)
