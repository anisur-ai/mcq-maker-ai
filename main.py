import os
import streamlit as st
from groq import Groq
from PIL import Image

# Streamlit Secrets থেকে API Key নেওয়া
api_key = st.secrets.get("GROQ_API_KEY")

if not api_key:
    st.error("⚠️ Streamlit Secrets-এ GROQ_API_KEY পাওয়া যায়নি!")
    st.stop()

client = Groq(api_key=api_key)

st.title("📚 Smart MCQ Maker AI App")
st.write("বইয়ের ছবি দিন বা পড়া লিখে দিন—আপনার AI প্রশ্ন বানিয়ে দেবে!")

# ১. প্রশ্নের সংখ্যা
num_questions = st.number_input("কয়টি MCQ চান? (খালি রাখলে AI নিজে ঠিক করবে)", min_value=1, max_value=20, value=10)

# ২. পড়া বা টেক্সট লেখার বক্স
text_input = st.text_area("পড়াটি এখানে লিখুন বা পেস্ট করুন (ঐচ্ছিক):")

# ৩. ছবি আপলোড করার সুবিধা
uploaded_file = st.file_uploader("অথবা পড়ার ছবি তুলে আপলোড করুন (JPG/PNG):", type=["jpg", "jpeg", "png"])

# ৪. বিশেষ কোনো নির্দেশ
custom_instruction = st.text_input("বিশেষ কোনো নির্দেশ? (যেমন: 'শুধু কঠিন প্রশ্ন করো' বা 'উত্তরসহ ব্যাখ্যা দাও'):")

# মেকিং বাটন
if st.button("MCQ তৈরি করুন 🚀"):
    if text_input or uploaded_file:
        
        prompt = f"""
তুমি একজন বিশেষজ্ঞ শিক্ষক। নিচে দেওয়া পড়া থেকে {num_questions}টি MCQ প্রশ্ন তৈরি করো।

পড়া/বিষয়:
{text_input if text_input else "আপলোড করা ছবি বা বিষয়বস্তু থেকে প্রশ্ন তৈরি করো।"}

বিশেষ নির্দেশ: {custom_instruction}

নিয়মাবলী:
১. প্রতিটি প্রশ্নের ৪টি করে স্পষ্ট অপশন (A, B, C, D) দেবে।
২. শেষে প্রতিটি প্রশ্নের সঠিক উত্তর স্পষ্ট করে জানিয়ে দেবে।
৩. সম্পূর্ণ লেখাটি স্পষ্ট বাংলা ভাষায় হতে হবে।
"""
        with st.spinner("AI প্রশ্ন তৈরি করছে... অনুগ্রহ করে অপেক্ষা করুন।"):
            try:
                response = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": "user", "content": prompt}]
                )
                st.success("✅ আপনার MCQ তৈরি হয়ে গেছে!")
                st.write(response.choices[0].message.content)
            except Exception as e:
                st.error(f"একটি সমস্যা হয়েছে: {e}")
    else:
        st.warning("অনুগ্রহ করে কোনো পড়া লিখুন অথবা ছবি আপলোড করুন।")
