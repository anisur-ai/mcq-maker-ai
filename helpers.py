import os
import requests
from fpdf import FPDF
from docx import Document

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
        )
        result = r.json()
        
        if result.get("IsErroredOnProcessing"):
            return None
        
        parsed_results = result.get("ParsedResults")
        if parsed_results and len(parsed_results) > 0:
            return parsed_results[0].get("ParsedText")
        return None
    except Exception:
        return None

def generate_prompt(num_q, text_content, difficulty, q_type, lang, subject, cls, bloom, temp, custom_ins):
    prompt = f"""
তুমি একজন অভিজ্ঞ শিক্ষক। নিচের নির্দেশাবলী মেনে প্রশ্ন তৈরি করো:

- মোট প্রশ্নের সংখ্যা: {num_q}
- বিষয়: {subject}
- শ্রেণী: {cls}
- কঠিনতার মাত্রা (Difficulty): {difficulty}
- প্রশ্নের ধরন: {q_type}
- ভাষা: {lang}
- Bloom's Taxonomy স্তর: {bloom}

নির্দেশাবলী:
১. প্রতিটি প্রশ্নের ৪টি অপশন (A, B, C, D) বাধ্যতামূলক (যদি MCQ হয়)।
২. শেষে Answer Key ও প্রতিটি উত্তরের ১-২ লাইনের ব্যাখ্যা (Explanation) দেবে।
৩. বইয়ের বাইরে তথ্য যোগ করবে না। প্রশ্নে অস্পষ্টতা থাকবে না। কোনো প্রশ্ন পুনরাবৃত্তি করবে না।

পড়া/বিষয়বস্তু:
{text_content}

বিশেষ নির্দেশ:
{custom_ins}
"""
    return prompt

def create_docx(text):
    doc = Document()
    doc.add_heading('Smart MCQ Generator - Questions', 0)
    doc.add_paragraph(text)
    file_path = "mcq_output.docx"
    doc.save(file_path)
    return file_path

def create_pdf(text):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=11)
    for line in text.split('\n'):
        pdf.multi_cell(0, 8, txt=line.encode('latin-1', 'replace').decode('latin-1'))
    file_path = "mcq_output.pdf"
    pdf.output(file_path)
    return file_path
      
