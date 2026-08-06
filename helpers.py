import requests
import docx
import pypdf
import fitz  # PyMuPDF
import io
import google.generativeai as genai
from openai import OpenAI
from groq import Groq
from PIL import Image

def smart_read_file(uploaded_file, ocr_api_key):
    if uploaded_file is None:
        return ""
    
    filename = uploaded_file.name.lower()
    extracted_text = ""

    try:
        if filename.endswith((".jpg", ".jpeg", ".png", ".webp")):
            extracted_text = ocr_space_file(uploaded_file, ocr_api_key, language="eng+ben")
            
        elif filename.endswith(".pdf"):
            file_bytes = uploaded_file.read()
            doc_pdf = fitz.open(stream=file_bytes, filetype="pdf")
            
            for page_num in range(len(doc_pdf)):
                page = doc_pdf[page_num]
                text = page.get_text()
                
                if text.strip():
                    extracted_text += text + "\n"
                else:
                    pix = page.get_pixmap(dpi=150)
                    img_bytes = pix.tobytes("png")
                    
                    class MemFile:
                        def __init__(self, content, name):
                            self.content = content
                            self.name = name
                        def read(self):
                            return self.content
                    
                    img_file = MemFile(img_bytes, f"page_{page_num}.png")
                    scanned_text = ocr_space_file(img_file, ocr_api_key, language="eng+ben")
                    if scanned_text:
                        extracted_text += f"\n[Scanned Page {page_num+1} OCR]: {scanned_text}\n"
                        
        elif filename.endswith(".docx"):
            doc = docx.Document(uploaded_file)
            for para in doc.paragraphs:
                extracted_text += para.text + "\n"
                
        elif filename.endswith(".txt"):
            extracted_text = uploaded_file.read().decode("utf-8", errors="ignore")
            
    except Exception as e:
        print(f"File processing error: {e}")

    return truncate_text(extracted_text.strip(), max_chars=12000)

def ocr_space_file(file_obj, api_key, language="eng+ben"):
    url = "https://api.ocr.space/parse/image"
    try:
        file_bytes = file_obj.read() if hasattr(file_obj, "read") else file_obj
        file_type = getattr(file_obj, "type", "image/png")
        payload = {'isOverlayRequired': False, 'apikey': api_key, 'language': language, 'scale': True, 'OCREngine': 2}
        files = {'filename': (getattr(file_obj, "name", "image.png"), file_bytes, file_type)}
        response = requests.post(url, data=payload, files=files, timeout=30)
        result = response.json()
        if not result.get("IsErroredOnProcessing"):
            parsed = result.get("ParsedResults")
            if parsed:
                return parsed[0].get("ParsedText", "")
    except Exception as e:
        print(f"OCR Error: {e}")
    return ""

def needs_web_search(prompt, api_key):
    try:
        client = Groq(api_key=api_key)
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": "Analyze the user query. Answer ONLY with 'YES' if it requires real-time facts, current news, latest weather, or live data. Answer ONLY with 'NO' if it is conceptual, historical, coding, math, general knowledge, or creative writing."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=5,
            temperature=0.0
        ]
        decision = response.choices[0].message.content.strip().upper()
        return "YES" in decision
    except Exception as e:
        print(f"Intent detector error: {e}")
        return False

def smart_search(query, tavily_key, jina_key):
    if tavily_key:
        try:
            url = "https://api.tavily.com/search"
            payload = {"api_key": tavily_key, "query": query, "search_depth": "advanced", "max_results": 3}
            res = requests.post(url, json=payload, timeout=8)
            if res.status_code == 200:
                data = res.json()
                results = data.get("results", [])
                if results:
                    formatted = "\n\n".join([f"Source: {r.get('url')}\nContent: {r.get('content')}" for r in results])
                    urls = [r.get('url') for r in results if r.get('url')]
                    return formatted, urls
        except Exception as e:
            print(f"Tavily error: {e}")

    try:
        jina_search_url = f"https://s.jina.ai/{query}"
        headers = {"Accept": "application/json"}
        if jina_key:
            headers["Authorization"] = f"Bearer {jina_key}"
        res = requests.get(jina_search_url, headers=headers, timeout=8)
        if res.status_code == 200:
            data = res.json()
            data_list = data.get("data", [])
            if data_list:
                formatted = "\n\n".join([f"Source: {item.get('url')}\nContent: {item.get('content')}" for item in data_list[:3]])
                urls = [item.get('url') for item in data_list[:3] if item.get('url')]
                return formatted, urls
    except Exception as e:
        print(f"Jina search error: {e}")

    return "", []

def smart_scrape(url_to_scrape, firecrawl_key, jina_key):
    if firecrawl_key:
        try:
            url = "https://api.firecrawl.dev/v1/scrape"
            headers = {"Authorization": f"Bearer {firecrawl_key}", "Content-Type": "application/json"}
            payload = {"url": url_to_scrape, "formats": ["markdown"]}
            res = requests.post(url, json=payload, headers=headers, timeout=12)
            if res.status_code == 200 and res.json().get("success"):
                content = res.json().get("data", {}).get("markdown", "")
                return truncate_text(content, 10000), [url_to_scrape]
        except Exception as e:
            print(f"Firecrawl error: {e}")
    
    try:
        jina_url = f"https://r.jina.ai/{url_to_scrape}"
        headers = {"Accept": "application/json"}
        if jina_key:
            headers["Authorization"] = f"Bearer {jina_key}"
        res = requests.get(jina_url, headers=headers, timeout=12)
        if res.status_code == 200:
            content = res.json().get("data", {}).get("content", "")
            return truncate_text(content, 10000), [url_to_scrape]
    except Exception as e:
        print(f"Jina scrape error: {e}")
    
    return "Could not extract content from URL.", []

def select_model_by_task(query, file_content):
    total_len = len(query) + len(file_content)
    q_lower = query.lower()

    if any(k in q_lower for k in ["code", "python", "javascript", "function", "script", "bug", "sql", "html", "css", "কোড", "প্রোগ্রাম"]):
        return {"provider": "openrouter", "model": "deepseek/deepseek-chat"}
    
    if any(k in q_lower for k in ["math", "calculate", "equation", "formula", "physics", "chemistry", "গণিত", "সূত্র"]):
        return {"provider": "groq", "model": "llama-3.3-70b-versatile"}
    
    if total_len > 4000:
        return {"provider": "gemini", "model": "gemini-2.5-flash"}
    
    if total_len > 300 or len(query.split()) > 40:
        return {"provider": "groq", "model": "llama-3.3-70b-versatile"}
    
    return {"provider": "groq", "model": "llama-3.1-8b-instant"}

def truncate_text(text, max_chars=10000):
    if len(text) > max_chars:
        return text[:max_chars] + "\n\n[Content truncated due to length limits...]"
    return text

def manage_conversation_memory(messages, api_key, existing_summary=""):
    if len(messages) > 16:
        try:
            client = Groq(api_key=api_key)
            new_turns = "\n".join([f"{m['role']}: {m['content']}" for m in messages[-10:]])
            prompt_text = f"Previous Summary: {existing_summary}\n\nNew Conversation:\n{new_turns}\n\nUpdate and combine the summary concisely:"
            
            response = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "system", "content": "You are a memory manager. Update the ongoing conversation summary."}, {"role": "user", "content": prompt_text}],
                max_tokens=250
            ]
            updated_summary = response.choices[0].message.content.strip()
            return updated_summary, [{"role": "system", "content": f"Ongoing Conversation Summary: {updated_summary}"}] + messages[-8:]
        except Exception as e:
            print(f"Memory error: {e}")
    return existing_summary, messages

def provider_aware_ai_fallback(keys_dict, router_info, messages, max_tokens=4096):
    default_temp = 0.5
    preferred_provider = router_info["provider"]
    preferred_model = router_info["model"]

    providers_order = [preferred_provider, "groq", "gemini", "mistral", "openrouter"]
    providers_order = list(dict.fromkeys(providers_order))

    for prov in providers_order:
        if prov == "groq" and keys_dict.get("groq"):
            try:
                client = Groq(api_key=keys_dict["groq"], timeout=8.0, max_retries=0)
                m_to_use = preferred_model if preferred_provider == "groq" else "llama-3.3-70b-versatile"
                completion = client.chat.completions.create(model=m_to_use, messages=messages, temperature=default_temp, max_completion_tokens=max_tokens, stream=True)
                for chunk in completion:
                    if chunk.choices and chunk.choices[0].delta and chunk.choices[0].delta.content:
                        yield chunk.choices[0].delta.content
                return
            except Exception:
                pass

        elif prov == "gemini" and keys_dict.get("gemini"):
            try:
                genai.configure(api_key=keys_dict["gemini"])
                g_model = genai.GenerativeModel("gemini-2.5-flash")
                sys_inst = messages[0]['content'] if messages[0]['role'] == 'system' else ""
                history = [{"role": "user" if m['role']=="user" else "model", "parts": [m['content']]} for m in messages[1:-1]]
                chat = g_model.start_chat(history=history)
                response = chat.send_message(f"{sys_inst}\n\nUser: {messages[-1]['content']}", stream=True)
                for chunk in response:
                    if chunk.text:
                        yield chunk.text
                return
            except Exception:
                pass

        elif prov == "mistral" and keys_dict.get("mistral"):
            try:
                m_client = OpenAI(base_url="https://api.mistral.ai/v1", api_key=keys_dict["mistral"], timeout=8.0, max_retries=0)
                completion = m_client.chat.completions.create(model="mistral-small-latest", messages=messages, temperature=default_temp, max_tokens=max_tokens, stream=True)
                for chunk in completion:
                    if chunk.choices and chunk.choices[0].delta and chunk.choices[0].delta.content:
                        yield chunk.choices[0].delta.content
                return
            except Exception:
                pass

        elif prov == "openrouter" and keys_dict.get("openrouter"):
            try:
                o_client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=keys_dict["openrouter"], timeout=8.0, max_retries=0)
                m_to_use = preferred_model if preferred_provider == "openrouter" else "mistralai/mistral-small-3.2-24b-instruct:free"
                completion = o_client.chat.completions.create(model=m_to_use, messages=messages, temperature=default_temp, max_tokens=max_tokens, stream=True)
                for chunk in completion:
                    if chunk.choices and chunk.choices[0].delta and chunk.choices[0].delta.content:
                        yield chunk.choices[0].delta.content
                return
            except Exception:
                pass

    yield "দুঃখিত কিছুক্ষণ অপেক্ষা করুন টেকনিক্যাল সমস্যা হয়েছে ঠিক করা হচ্ছে"
    
