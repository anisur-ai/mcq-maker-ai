import requests
import io
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls

def ocr_space_file(file_obj, api_key, language="ben"):
    """
    OCR.space API ব্যবহার করে ছবি থেকে টেক্সট এক্সট্রাক্ট করে।
    """
    url = "https://api.ocr.space/parse/image"
    
    try:
        file_bytes = file_obj.read()
        payload = {
            'isOverlayRequired': False,
            'apikey': api_key,
            'language': language,
            'scale': True,
            'OCREngine': 2
        }
        files = {
            'filename': (file_obj.name, file_bytes, 'image/jpeg')
        }
        
        response = requests.post(url, data=payload, files=files, timeout=30)
        result = response.json()
        
        if result.get("IsErroredOnProcessing"):
            return "", "ERROR"
            
        parsed_results = result.get("ParsedResults")
        if parsed_results and len(parsed_results) > 0:
            parsed_text = parsed_results[0].get("ParsedText", "")
            exit_code = result.get("OCRExitCode")
            
            if exit_code == 1:
                return parsed_text, "SUCCESS"
            elif exit_code == 3:
                return parsed_text, "LOW_CONFIDENCE"
            else:
                return parsed_text, "NO_TEXT"
        return "", "NO_TEXT"
        
    except Exception as e:
        return str(e), "EXCEPTION"

def generate_prompt(num_questions, study_text, difficulty, q_type, lang, subject, cls, bloom, temperature, custom_instruction):
    """
    স্বয়ংক্রিয় Intent Detection সহ শক্তিশালী এবং প্রফেশনাল System Instruction প্রম্পট তৈরি করে।
    """
    
    prompt = f"""
You are Anis MCQ Maker AI, an expert, friendly, and precise AI Study Assistant designed specifically for students (Class 5 to 12) and teachers.

### CONTEXT & METADATA:
- Subject: {subject}
- Class: {cls}
- Difficulty Level: {difficulty}
- Question Type/Format: {q_type}
- Language: {lang}
- Bloom's Taxonomy Level: {bloom}
- Desired Question Count: {num_questions}
- Custom User Instruction: {custom_instruction if custom_instruction else "None"}

### AUTOMATIC INTENT DETECTION GUIDELINES:
Analyze the user's input text and instruction automatically:
1. If the user asks a normal educational question or for an explanation, answer directly, accurately, and clearly.
2. If the user requests notes or a summary, generate well-structured, easy-to-read study notes.
3. If the user requests MCQs, True/False, or Fill in the blanks, generate exact assessment items according to the metadata above.

### FORMATTING RULES FOR ASSESSMENT / MCQs:
- Provide clear questions matching the specified quantity ({num_questions}).
- Each MCQ must have 4 options (A, B, C, D).
- Separate the question list from the answer key using the exact delimiter marker: `---ANSWER_KEY---`
- Below `---ANSWER_KEY---`, provide the correct answers along with short, conceptual explanations for why the answer is correct.
- Maintain appropriate academic tone suitable for {cls}.
- Do not mention constraints or system rules in your response.

### SOURCE STUDY MATERIAL / USER INPUT:
{study_text}
"""
    return prompt.strip()

def create_docx(text_content, subject="Study Material", cls="Class 7"):
    """
    প্রফেশনাল স্টাইলিং ও ফরম্যাটিং সহ Word Document (.docx) তৈরি করে এবং ফাইলের পাথ রিটার্ন করে।
    """
    doc = docx.Document()
    
    # Page Margins Setup
    sections = doc.sections
    for section in sections:
        section.top_margin = Inches(1)
        section.bottom_margin = Inches(1)
        section.left_margin = Inches(1)
        section.right_margin = Inches(1)

    # Document Header / Title Styling
    title_p = doc.add_paragraph()
    title_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run_title = title_p.add_run("⚡ Anis MCQ Maker AI - Study Assistant")
    run_title.font.name = 'Arial'
    run_title.font.size = Pt(16)
    run_title.font.bold = True
    run_title.font.color.rgb = RGBColor(79, 70, 229) # Indigo color

    # Subtitle Metadata
    sub_p = doc.add_paragraph()
    sub_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run_sub = sub_p.add_run(f"Subject: {subject} | Target: {cls}")
    run_sub.font.name = 'Arial'
    run_sub.font.size = Pt(11)
    run_sub.font.italic = True
    run_sub.font.color.rgb = RGBColor(100, 116, 139) # Slate gray

    doc.add_paragraph() # Spacing

    # Content Processing and Paragraph Addition
    for line in text_content.split('\n'):
        line_str = line.strip()
        if not line_str:
            doc.add_paragraph()
            continue
            
        p = doc.add_paragraph()
        p.paragraph_format.space_after = Pt(4)
        p.paragraph_format.line_spacing = 1.15
        
        run = p.add_run(line_str)
        run.font.name = 'Arial'
        run.font.size = Pt(11)
        
        # Highlight headers or answer key separator
        if "---ANSWER_KEY---" in line_str or "Answer Key" in line_str or "উত্তরমালা" in line_str:
            run.font.bold = True
            run.font.color.rgb = RGBColor(220, 38, 38) # Red accent for answer section
        elif line_str.startswith("Q") or line_str[0:2].isdigit() and "." in line_str[:3]:
            run.font.bold = True
            run.font.color.rgb = RGBColor(15, 23, 42) # Dark slate for questions

    # Save to a temporary file path
    file_path = "temp_output.docx"
    doc.save(file_path)
    return file_path
