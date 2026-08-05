import requests
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
import google.generativeai as genai
from openai import OpenAI
from groq import Groq
import tempfile

def ocr_space_file(file_obj, api_key, language="ben"):
    url = "https://api.ocr.space/parse/image"
    try:
        file_bytes = file_obj.read()
        file_type = file_obj.type if hasattr(file_obj, "type") else "application/octet-stream"
        payload = {'isOverlayRequired': False, 'apikey': api_key, 'language': language, 'scale': True, 'OCREngine': 2}
        files = {'filename': (file_obj.name, file_bytes, file_type)}
        
        response = requests.post(url, data=payload, files=files, timeout=30)
        result = response.json()
        if result.get("IsErroredOnProcessing"):
            return "", "ERROR"
        parsed_results = result.get("ParsedResults")
        if parsed_results and len(parsed_results) > 0:
            parsed_text = parsed_results[0].get("ParsedText", "")
            exit_code = result.get("OCRExitCode")
            if exit_code in [1, 3]:
                return parsed_text, "SUCCESS"
        return "", "NO_TEXT"
    except Exception as e:
        return str(e), "EXCEPTION"

def generate_prompt(num_questions, study_text, difficulty, q_type, lang, subject, cls, bloom, custom_instruction):
    prompt = f"""
You are Anis MCQ Maker AI, an expert and precise AI Study Assistant designed specifically for students (Class 5 to 12) and teachers.

### CONTEXT & METADATA:
- Subject: {subject}
- Class: {cls}
- Difficulty Level: {difficulty}
- Question Type/Format: {q_type}
- Language: {lang}
- Bloom's Taxonomy Level: {bloom}
- Desired Question Count: {num_questions}
- Custom User Instruction: {custom_instruction if custom_instruction else "None"}

### FORMATTING RULES:
- Provide clear questions matching the specified quantity ({num_questions}).
- Each MCQ must have 4 options (A, B, C, D).
- Separate the question list from the answer key using the exact delimiter marker: `---ANSWER_KEY---`
- Below `---ANSWER_KEY---`, provide correct answers with short conceptual explanations.

### SOURCE STUDY MATERIAL / USER INPUT:
{study_text}
"""
    return prompt.strip()

class StreamChunkMock:
    def __init__(self, text, is_error=False):
        self.choices = [type('obj', (object,), {'delta': type('obj', (object,), {'content': text})()})()]
        self.is_error = is_error

def four_layer_ai_fallback(keys_dict, selected_model, messages, max_tokens=4096):
    default_temp = 0.5  
    
    GEMINI_MODEL_NAME = "gemini-2.5-flash"
    MISTRAL_MODEL_NAME = "mistral-small-latest"
    OPENROUTER_MODEL_NAME = "mistralai/mistral-small-3.2-24b-instruct:free"
    
    # --- 1. TRY GROQ ---
    if keys_dict.get("groq"):
        try:
            client = Groq(
                api_key=keys_dict["groq"],
                timeout=8.0,
                max_retries=0
            )
            completion = client.chat.completions.create(
                model=selected_model,
                messages=messages,
                temperature=default_temp,
                max_completion_tokens=max_tokens,
                stream=True
            )
            for chunk in completion:
                if chunk.choices and chunk.choices[0].delta and chunk.choices[0].delta.content:
                    yield StreamChunkMock(chunk.choices[0].delta.content, is_error=False)
            return
        except Exception as e:
            print(f"Groq failed: {e}. Switching to Gemini...")

    # --- 2. TRY GEMINI ---
    if keys_dict.get("gemini"):
        try:
            genai.configure(api_key=keys_dict["gemini"])
            gemini_model = genai.GenerativeModel(GEMINI_MODEL_NAME)
            
            system_instruction = messages[0]['content']
            chat_history = []
            for msg in messages[1:-1]:
                role = "user" if msg['role'] == "user" else "model"
                chat_history.append({"role": role, "parts": [msg['content']]})
                
            chat = gemini_model.start_chat(history=chat_history)
            latest_prompt = f"{system_instruction}\n\nUser Request: {messages[-1]['content']}"
            response = chat.send_message(latest_prompt, stream=True)
            
            for chunk in response:
                if chunk.text:
                    yield StreamChunkMock(chunk.text, is_error=False)
            return
        except Exception as e:
            print(f"Gemini failed: {e}. Switching to Mistral...")

    # --- 3. TRY MISTRAL ---
    if keys_dict.get("mistral"):
        try:
            mistral_client = OpenAI(
                base_url="https://api.mistral.ai/v1",
                api_key=keys_dict["mistral"],
                timeout=8.0,
                max_retries=0
            )
            completion = mistral_client.chat.completions.create(
                model=MISTRAL_MODEL_NAME,
                messages=messages,
                temperature=default_temp,
                max_tokens=max_tokens,
                stream=True
            )
            for chunk in completion:
                if chunk.choices and chunk.choices[0].delta and chunk.choices[0].delta.content:
                    yield StreamChunkMock(chunk.choices[0].delta.content, is_error=False)
            return
        except Exception as e:
            print(f"Mistral failed: {e}. Switching to OpenRouter...")

    # --- 4. TRY OPENROUTER ---
    if keys_dict.get("openrouter"):
        try:
            or_client = OpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=keys_dict["openrouter"],
                timeout=8.0,
                max_retries=0
            )
            completion = or_client.chat.completions.create(
                model=OPENROUTER_MODEL_NAME,
                messages=messages,
                temperature=default_temp,
                max_tokens=max_tokens,
                stream=True
            )
            for chunk in completion:
                if chunk.choices and chunk.choices[0].delta and chunk.choices[0].delta.content:
                    yield StreamChunkMock(chunk.choices[0].delta.content, is_error=False)
            return
        except Exception as e:
            print(f"OpenRouter failed: {e}")

    # --- সবকটি এআই ব্যর্থ হলে is_error=True সহ এরর মেসেজ পাঠানো ---
    error_notice = """
⚠️ **সাময়িক প্রযুক্তিগত সমস্যার কারণে অনুরোধটি সম্পন্ন করা যায়নি।**

অনুগ্রহ করে ১–২ মিনিট পরে আবার চেষ্টা করুন। আপনার সহযোগিতার জন্য ধন্যবাদ।
"""
    yield StreamChunkMock(error_notice, is_error=True)
    return

def create_docx(text_content, subject="Study Material", cls="Class 7"):
    doc = docx.Document()
    for section in doc.sections:
        section.top_margin = Inches(1)
        section.bottom_margin = Inches(1)
        section.left_margin = Inches(1)
        section.right_margin = Inches(1)

    title_p = doc.add_paragraph()
    title_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run_title = title_p.add_run("⚡ Anis MCQ Maker AI - Study Assistant")
    run_title.font.name = 'Arial'
    run_title.font.size = Pt(16)
    run_title.font.bold = True
    run_title.font.color.rgb = RGBColor(79, 70, 229)

    sub_p = doc.add_paragraph()
    sub_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run_sub = sub_p.add_run(f"Subject: {subject}  |  Class: {cls}")
    run_sub.font.name = 'Arial'
    run_sub.font.size = Pt(11)
    run_sub.font.italic = True
    run_sub.font.color.rgb = RGBColor(100, 116, 139)

    doc.add_paragraph()

    for line in text_content.split('\n'):
        line_str = line.strip()
        if not line_str:
            doc.add_paragraph()
            continue
        p = doc.add_paragraph()
        run = p.add_run(line_str)
        run.font.name = 'Arial'
        run.font.size = Pt(11)
        if "---ANSWER_KEY---" in line_str:
            run.font.bold = True
            run.font.color.rgb = RGBColor(220, 38, 38)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp:
        doc.save(tmp.name)
        return tmp.name
        
