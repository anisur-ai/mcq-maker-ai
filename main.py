import os
import streamlit as st
import base64
from groq import Groq

# Streamlit Secrets থেকে API Key নেওয়া
api_key = st.secrets.get("GROQ_API_KEY")

if not api_key:
    st.error("⚠️ Streamlit Secrets-এ GROQ_API_KEY পাওয়া যায়নি!")
    st.stop()

client = Groq(api_key=api_key)

st.title("📚 Smart MCQ Maker AI App")
st.write("বইয়ের ছবি দিন বা পড়া লিখে দিন—আপনার AI প্রশ্ন বানিয়ে দেবে!")

# ১. প্রশ্নের সংখ্যা
num_questions = st.number_input("কয়টি MCQ চান?", min_value=1, max_value=20, value=10)

# ২. পড়া বা টেক্সট লেখার বক্স
text_input = st.text_area("পড়াটি এখানে লিখুন বা পেস্ট করুন (ঐচ্ছিক):")

# ৩. ছবি আপলোড করার সুবিধা
uploaded_file = st.file_uploader("অথবা পড়ার ছবি তুলে আপলোড করুন (JPG/PNG):", type=["jpg", "jpeg", "png"])

# ৪. বিশেষ কোনো নির্দেশ
custom_instruction = st.text_input("বিশেষ কোনো নির্দেশ? (যেমন: 'শুধু কঠিন প্রশ্ন করো'):")

# মেকিং বাটন
if st.button("MCQ তৈরি করুন 🚀"):
    if text_input or uploaded_file:
        with st.spinner("AI বিশ্লেষণ করে প্রশ্ন তৈরি করছে..."):
            try:
                # যদি ব্যবহারকারী ছবি আপলোড করে
                if uploaded_file:
                    bytes_data = uploaded_file.getvalue()
                    base64_image = base64.b64encode(bytes_data).decode('utf-8')
                    
                    prompt = f"এই ছবিতে থাকা পড়া থেকে {num_questions}টি স্পষ্ট বাংলা MCQ প্রশ্ন ও শেষে সঠিক উত্তর তৈরি করে দাও। {custom_instruction}"
                    
                    response = client.chat.completions.create(
                        model="llama-3.2-11b-vision-preview",
                        messages=[
                            {
                                "role": "user",
                                "content": [
                                    {"type": "text", "text": prompt},
                                    {
                                        "type": "image_url",
                                        "image_url": {
                                            "url": f"data:image/jpeg;base64,{base64_image}"
                                        },
                                    },
                                ],
                            }
                        ],
                    )
                # যদি ব্যবহারকারী শুধু টেক্সট দেয়
                else:
                    prompt = f"""
তুমি একজন শিক্ষক। নিচের পড়া থেকে {num_questions}টি MCQ প্রশ্ন ও শেষে উত্তর তৈরি করো।
পড়া: {text_input}
বিশেষ নির্দেশ: {custom_instruction}
"""
                    response = client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=[{"role": "user", "content": prompt}]
                    )

                st.success("✅ আপনার MCQ তৈরি হয়ে গেছে!")
                st.write(response.choices[0].message.content)

            except Exception as e:
                st.error(f"একটি সমস্যা হয়েছে: {e}")
    else:
        st.warning("অনুগ্রহ করে কোনো পড়া লিখুন অথবা বইয়ের ছবি আপলোড করুন।")
