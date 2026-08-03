import os
import re
import requests
from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH

# ১. OCR Text Clean (অপ্রয়োজনীয় স্পেস ও খালি লাইন মোছা)
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
    except Exception:
        return None, "SERVER_ERROR"

# ৩. Dynamic Prompt Generator (সাথে সাধারণ কথার চ্যাট সাপোর্ট যুক্ত)
def generate_prompt(num_q, text_content, difficulty, q_type, lang, subject, cls, bloom, temp, custom_ins):
    
    # পরীক্ষা করা হচ্ছে ইনপুটটি কোনো সাধারণ কথা (যেমন কেমন আছেন, কী করছেন) কি না
    chat_keywords = ["কেমন আছেন", "কি করছেন", "কী করছিস", "কী করছেন", "hello", "hi", "how are you", "what are you doing"]
    is_general_chat = any(keyword in text_content.lower() for keyword in chat_keywords)

    if is_general_chat and len(text_content.strip()) < 50:
        # যদি সাধারণ কথা হয়, তবে বন্ধুসুলভ ও সুন্দরভাবে উত্তর দেওয়ার প্রম্পট
        prompt = f"""
তুমি একজন খুব ভালো বন্ধুসুলভ ও হেল্পফুল এআই অ্যাসিস্ট্যান্ট (Anis MCQ Maker AI)। ব্যবহারকারী তোমার সাথে সাধারণ একটি কথা বা কুশল বিনিময় করেছে: "{text_content}"
তুমি খুব বিনয়ী, সুন্দর এবং মিষ্টি ভাষায় তার উত্তর দাও। জানিয়ে দাও যে তুমি কেমন আছো এবং পড়াশোনা বা MCQ তৈরিতে তাকে কীভাবে সাহায্য করতে পারো। ভাষা রাখবে {lang}-এ।
"""
    else:
        # স্বাভাবিক প্রশ্নপত্র তৈরির প্রম্পট
        prompt = f"""
তুমি একজন অত্যন্ত অভিজ্ঞ ও পেশাদার শিক্ষক। নিচে দেওয়া তথ্যের ওপর ভিত্তি করে নিখুঁত প্রশ্নপত্র তৈরি করো:

- মোট প্রশ্নের সংখ্যা: {num_q}
- বিষয়: {subject}
- শ্রেণী: {cls}
- কঠিনতার মাত্রা: {difficulty}
- প্রশ্নের ধরন: {q_type}
- ভাষা: {lang}
- Bloom's Taxonomy স্তর: {bloom}

নির্দেশাবলী:
১. প্রতিটি প্রশ্ন স্পষ্ট ভাষায় লিখবে।
২. প্রশ্নের শেষে অবশ্যই '---ANSWER_KEY---' শিরোনাম দিয়ে উত্তরমালা ও ১-২ লাইনের ব্যাখ্যা লিখবে।
৩. প্রদত্ত মূল টেক্সট বহির্ভূত কোনো তথ্য যোগ করবে না।

পড়া/বিষয়বস্তু:
{text_content}

বিশেষ নির্দেশ:
{custom_ins}
"""
    return prompt

# ৪. Professional DOCX Generator
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
    
    file_path = "mcq_output.docx"
    doc.save(file_path)
    return file_path
        
