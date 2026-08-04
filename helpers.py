import requests
import logging
import tempfile
import re
from datetime import datetime
from docx import Document
from docx.shared import Pt
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

# Logging Setup
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def clean_ocr_text(text):
    """
    Cleans up redundant spaces and multiple empty line breaks from OCR text.
    """
    if not text:
        return ""
    # Multiple newlines reduction
    text = re.sub(r'\n\s*\n', '\n\n', text)
    # Extra trailing spaces removal
    text = "\n".join([line.strip() for line in text.splitlines()])
    return text.strip()

def ocr_space_file(file, api_key, language='ben'):
    """
    Sends an uploaded image file to the OCR.Space API and extracts cleaned text with detailed status.
    """
    try:
        url = 'https://api.ocr.space/parse/image'
        payload = {
            'apikey': api_key,
            'language': language,
            'isOverlayRequired': False,
            'detectOrientation': True,
            'scale': True,
            'OCREngine': 2
        }
        
        file_bytes = file.getvalue()
        files = {'file': (file.name, file_bytes, file.type)}
        
        response = requests.post(url, data=payload, files=files, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        
        if result.get("IsErroredOnProcessing"):
            error_msg = result.get("ErrorMessage", ["Unknown error"])[0]
            logging.error(f"OCR Error: {error_msg}")
            
            if "maximum" in error_msg.lower() or "limit" in error_msg.lower():
                return None, "LIMIT_EXCEEDED"
            return None, "SERVER_ERROR"

        parsed_results = result.get("ParsedResults", [])
        if not parsed_results:
            return None, "NO_TEXT"
            
        raw_text = parsed_results[0].get("ParsedText", "")
        cleaned_text = clean_ocr_text(raw_text)
        
        if not cleaned_text:
            return None, "NO_TEXT"
            
        if len(cleaned_text) < 15:
            return cleaned_text, "LOW_CONFIDENCE"
            
        return cleaned_text, "SUCCESS"

    except requests.exceptions.RequestException as e:
        logging.error(f"OCR Request failed: {e}")
        return None, "NETWORK_ERROR"
    except Exception as e:
        logging.error(f"Unexpected OCR error: {e}")
        return None, "SERVER_ERROR"


def generate_prompt(num_questions, text, difficulty, q_type, lang, subject, cls, bloom, temp_mode, custom_instruction=""):
    """
    Generates a system prompt for LLMs based on strict intent recognition, temperature modes, and anti-hallucination rules.
    """
    if temp_mode <= 0.3:
        tone = "Generate highly accurate, strictly textbook-based questions with zero deviation."
    elif temp_mode >= 0.9:
        tone = "Generate creative, analytical, and challenging questions while remaining strictly faithful to the core facts of the source."
    else:
        tone = "Generate well-balanced, standard exam-oriented questions suitable for regular assessments."

    prompt = f"""
[SYSTEM INSTRUCTION]
You are an advanced AI Educational Assistant designed for Class 5 to 12 students and teachers.

CONTEXT:
- Subject: {subject}
- Target Class: {cls}
- Language: {lang}
- Output Type Requested: {q_type}
- Difficulty Level: {difficulty}
- Bloom's Taxonomy Level: {bloom}
- Number of Questions Requested: {num_questions}
- AI Generation Mode: {tone}

INPUT TEXT/QUERY:
\"\"\"{text}\"\"\"

SPECIAL CUSTOM INSTRUCTIONS:
{custom_instruction if custom_instruction else "None"}

OPERATIONAL RULES & INTENT RECOGNITION:
1. INTENT ANALYSIS FIRST:
   - If the input text is a general greeting or casual chat, reply warmly and explain how you can help create question papers.
   - If the input text asks an explicit question or seeks an explanation of a topic, answer the question clearly and directly first.
   - If the input text is study material, generate exact and highly relevant questions.

2. QUALITY & ANTI-HALLUCINATION RULES:
   - Do NOT invent facts not present or implied in the input material unless answering general educational queries.
   - If the input material is insufficient to generate {num_questions} unique questions, generate as many high-quality questions as possible and politely inform that more text is needed.
   - Do not copy sentences verbatim from the source unless absolutely necessary.
   - Ensure every question tests a different concept.
   - Avoid duplicate or overlapping questions.
   - If the input contains multiple images or chapters, merge all content seamlessly and generate questions without repeating the same concept.
   - Mode Instruction: {tone}

3. QUESTION FORMATTING:
   - Randomize option positions (A, B, C, D) evenly across questions.
   - Format clearly using Markdown. Do NOT use HTML tables.
   - Append answers at the end separated strictly by "---ANSWER_KEY---".

BEGIN RESPONSE NOW.
"""
    return prompt.strip()


def create_docx(text, subject="General", cls="Class 7"):
    """
    Creates a temporary Word Document (.docx) with robust Bengali font support.
    """
    doc = Document()
    
    # Configure Base Styles
    style = doc.styles['Normal']
    font = style.font
    font.name = 'Nirmala UI'
    font.size = Pt(11)
    
    # Safely Update existing rFonts or Create New Node for XML Safety
    rPr = style.element.get_or_add_rPr()
    rFonts = rPr.rFonts
    if rFonts is None:
        rFonts = OxmlElement("w:rFonts")
        rPr.append(rFonts)

    rFonts.set(qn("w:ascii"), "Nirmala UI")
    rFonts.set(qn("w:hAnsi"), "Nirmala UI")
    rFonts.set(qn("w:cs"), "SolaimanLipi")
    rFonts.set(qn("w:eastAsia"), "Nirmala UI")

    # Title Section
    doc.add_heading(f"{subject} - {cls} Question Paper", level=0)
    doc.add_paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    doc.add_paragraph("-" * 40)
    
    # Content Breakdown
    for line in text.split("\n"):
        if line.strip() == "---ANSWER_KEY---":
            doc.add_page_break()
            doc.add_heading("Answer Key & Explanations", level=1)
        else:
            doc.add_paragraph(line)
            
    # Save to Temporary File
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".docx")
    doc.save(temp_file.name)
    temp_file.close()
    
    return temp_file.name
        
