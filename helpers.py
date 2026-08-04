import os
import re
import requests
import logging
from datetime import datetime
from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH

# Logging Setup for Production
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# ১. OCR Text Clean
def clean_ocr_text(text):
    if not text:
        return ""
    cleaned = re.sub(r'[ \t]+', ' ', text)
    cleaned = re.sub(r'\n\s*\n', '\n\n', cleaned)
    return cleaned.strip()

# ২. OCR Space Service
def ocr_space_file(uploaded_file, api_key, language='ben'):
    payload = {
        'apikey': api_key,
        'language': language,
        'isOverlayRequired': False
    }
    files = {
        "filename": ("image.jpg", uploaded_file.getvalue())
    }
    try:
        r = requests.post(
            "https://api.ocr.space/parse/image",
            files=files,
            data=payload,
            timeout=30
        )
        r.raise_for_status()  # HTTP Error Status Check (500, 404, etc.)
        result = r.json()
        
        if result.get("IsErroredOnProcessing"):
            error_msg = result.get("ErrorMessage", [""])[0]
            if "limit" in error_msg.lower():
                return None, "LIMIT_EXCEEDED"
            return None, "ERROR"
        
        parsed_results = result.get("ParsedResults")
        if parsed_results and len(parsed_results) > 0:
            parsed_text = parsed_results[0].get("ParsedText", "")
            cleaned_text = clean_ocr_text(parsed_text)
            
            if len(cleaned_text.strip()) < 10:
                return cleaned_text, "LOW_CONFIDENCE"
            return cleaned_text, "SUCCESS"
            
        return None, "NO_TEXT"
    except Exception as e:
        logging.exception("OCR Error Occurred")
        return None, "SERVER_ERROR"

# ৩. Optimized Hybrid Prompt Generator
def generate_prompt(num_q, text_content, difficulty, q_type, lang, subject, cls, bloom, temp, custom_ins):
    
    if temp <= 0.3:
        temp_instruction = "সম্পূর্ণ পাঠ্যবইভিত্তিক ও অত্যন্ত নির্ভুল তথ্য ব্যবহার করবে।"
    elif temp >= 0.9:
        temp_instruction = "শিক্ষার্থীদের চিন্তাশক্তি বৃদ্ধির জন্য সৃজনশীল ও ঘুরিয়ে লেখা প্রশ্ন তৈরি করবে।"
    else:
        temp_instruction = "মানসম্মত, সহজবোধ্য ও ব্যালেন্সড প্রশ্ন তৈরি করবে।"

    return f"""
তুমি একজন বুদ্ধিমান শিক্ষাবিদ ও AI অ্যাসিস্ট্যান্ট (Anis MCQ Maker AI)। ব্যবহারকারীর ইনপুট পড়ে তার মূল উদ্দেশ্য (Intent) বুঝে উত্তর দাও:

১. **Ambiguous Intent (অস্পষ্ট উদ্দেশ্য):** ইনপুটটি যদি খুব সংক্ষিপ্ত বা অস্পষ্ট হয় (যেমন শুধু "পলাশীর যুদ্ধ"), তবে অনুমান না করে জিজ্ঞেস করো: "আপনি কি এর ব্যাখ্যা চান, নাকি MCQ প্রশ্ন তৈরি করতে চান?"
২. **Chat:** সাধারণ কুশলে মিষ্টি ও সংক্ষিপ্ত উত্তর দাও ({lang})।
৩. **Explanation:** নির্দিষ্ট বিষয়ের সংক্ষিপ্ত ও স্পষ্ট পয়েন্টভিত্তিক ব্যাখ্যা দাও।
৪. **Question Paper Generator:**
   - মোট প্রশ্ন: {num_q} | বিষয়: {subject} | শ্রেণী: {cls} | মান: {difficulty} | ধরন: {q_type} | Bloom: {bloom} | ভাষা: {lang}
   - টোন: {temp_instruction}
   - **টেক্সট বিশ্লেষণ ও পুনরাবৃত্তি রোধ:** ইনপুটটি বড় অধ্যায় হলে মূল ও গুরুত্বপূর্ণ ধারণাগুলো থেকে প্রশ্ন করবে; ছোট অনুচ্ছেদ হলে শুধু তার ওপর ভিত্তি করে বানাবে। ইনপুটে একই তথ্য বারবার থাকলেও তা থেকে একাধিক একজাতীয় প্রশ্ন তৈরি করবে না। তথ্য অপর্যাপ্ত হলে স্পষ্ট জানাবে।
   - **নিয়ম:** প্রশ্ন ১,২,৩.. ও অপশন (A),(B),(C),(D) নতুন লাইনে লিখবে (কোনো টেবিল নয়)। উত্তর আগে থেকে বোল্ড/চিহ্নিত করবে না। সঠিক উত্তর A,B,C,D-তে সমানভাবে ছড়াবে। 
   - প্রশ্ন শেষে `---ANSWER_KEY---` শিরোনাম দিয়ে সঠিক উত্তর ও ১ লাইনের ব্যাখ্যা দেবে।

ইনপুট/পড়া: {text_content}
বিশেষ নির্দেশ: {custom_ins}
"""

# ৪. Professional Dynamic DOCX Generator
def create_docx(text, subject="বিষয়", cls="শ্রেণী"):
    doc = Document()
    
    title = doc.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = title.add_run("EXAMINATION / PRACTICE QUESTION PAPER")
    run.bold = True
    run.font.size = Pt(16)
    
    sub_title = doc.add_paragraph()
    sub_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run_sub = sub_title.add_run(f"Subject: {subject} | Class: {cls}")
    run_sub.font.size = Pt(11)
    
    doc.add_paragraph("-" * 55)
    
    p = doc.add_paragraph(text)
    p.paragraph_format.line_spacing = 1.25
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    file_path = f"MCQ_{timestamp}.docx"
    doc.save(file_path)
    return file_path
