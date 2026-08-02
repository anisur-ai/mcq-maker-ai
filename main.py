import streamlit as st
import streamlit as st
from groq import Groq
from PIL import Image

# Streamlit Secrets থেকে Groq API Key নেওয়া
# API Key নিরাপত্তার সাথে খুঁজে নেওয়ার উপায়
api_key = st.secrets.get("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")

if not api_key:
    st.error("⚠️ Streamlit Secrets-এ GROQ_API_KEY পাওয়া যায়নি! অনুগ্রহ করে Manage app > Secrets-এ API Key যোগ করুন।")
    st.stop()

client = Groq(api_key=api_key)

st.set_page_config(page_title="MCQ Maker AI", page_icon="📚")

st.title("📚 Smart MCQ Maker AI App")
st.write("বইয়ের ছবি দিন বা পড়া লিখে দিন—আপনার ইচ্ছেমতো AI প্রশ্ন বানিয়ে দেবে!")

# ১. প্রশ্নের সংখ্যা বাছাই (ডিফল্ট ১০ রাখা হয়েছে)
num_questions = st.number_input("কয়টি MCQ চান? (খালি রাখলে AI নিজে ঠিক করবে)", min_value=1, max_value=30, value=10)

# ২. পড়া বা টেক্সট লেখার বক্স
text_input = st.text_area("পড়াটি এখানে লিখুন বা পেস্ট করুন (ঐচ্ছিক):")

# ৩. ছবি আপলোড করার সুবিধা
uploaded_file = st.file_uploader("অথবা পড়ার ছবি তুলে আপলোড করুন (JPG/PNG):", type=["jpg", "jpeg", "png"])

# ৪. ব্যবহারকারীর বিশেষ কোনো নির্দেশ/আদেশ
custom_instruction = st.text_input("বিশেষ কোনো নির্দেশ? (যেমন: 'শুধু কঠিন প্রশ্ন করো' বা 'উত্তরসহ ব্যাখ্যা দাও'):")

# মেকিং বাটন
if st.button("MCQ তৈরি করুন 🚀"):
    if text_input or uploaded_file:
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # স্মার্ট প্রম্পট লজিক
        prompt = f"""
        তুমি একজন বিশেষজ্ঞ শিক্ষক। প্রদত্ত পড়া বা ছবি থেকে মোট {num_questions}টি MCQ প্রশ্ন তৈরি করো।
        
        নিয়মাবলী:
        ১. প্রতিটি প্রশ্নের ৪টি করে স্পষ্ট অপশন (A, B, C, D) থাকবে।
        ২. শেষে প্রতিটি প্রশ্নের সঠিক উত্তর এবং সংক্ষেপে ১ লাইনে উত্তরটির ব্যাখ্যা থাকবে।
        ৩. সম্পূর্ণ লেখাটি স্পষ্ট বাংলা ভাষায় হতে হবে।
        """
        
        if custom_instruction:
            prompt += f"\nব্যবহারকারীর অতিরিক্ত নির্দেশ: {custom_instruction}"

        with st.spinner("AI ছবি ও পড়া বিশ্লেষণ করে MCQ তৈরি করছে..."):
            try:
                if uploaded_file:
                    image = Image.open(uploaded_file)
                    response = model.generate_content([prompt, image])
                else:
                    full_prompt = f"{prompt}\n\nনিচে দেওয়া পড়া থেকে প্রশ্ন তৈরি করো:\n{text_input}"
                    response = model.generate_content(full_prompt)
                    
                st.success("আপনার প্রশ্ন প্রস্তুত!")
                st.markdown(response.text)
            except Exception as e:
                st.error(f"একটি সমস্যা হয়েছে: {e}")
    else:
        st.warning("দয়া করে আগে কিছু লিখে দিন অথবা বই/খাতার কোনো ছবি আপলোড করুন!")
