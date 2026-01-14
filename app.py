import streamlit as st
import google.generativeai as genai
from groq import Groq
from openai import OpenAI
from PIL import Image
import io, base64, time, requests, sys
import fitz  # PyMuPDF
import pandas as pd
from docx import Document
from pptx import Presentation

# --- ضبط الترميز للأمان ---
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# --- 1. تصميم الواجهة السينمائية (Midjourney Cinematic Style) ---
st.set_page_config(page_title="AI Architect | God Mode", page_icon="🪄", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&display=swap');
    
    .stApp {
        background-color: #0b0b0e;
        background-image: radial-gradient(circle at 20% 20%, #1a1a2e 0%, #0b0b0e 100%);
        color: #e0e0e0;
        font-family: 'Inter', sans-serif;
    }
    section[data-testid="stSidebar"] {
        background-color: rgba(10, 10, 15, 0.95) !important;
        border-right: 1px solid rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(20px);
    }
    .stTabs [data-baseweb="tab-list"] { gap: 20px; border-bottom: 1px solid rgba(255,255,255,0.05); }
    .stTabs [aria-selected="true"] {
        color: #eb4d4b !important;
        border-bottom: 2px solid #eb4d4b !important;
    }
    .stButton>button {
        background: #eb4d4b;
        color: white; border: none; padding: 12px 30px; border-radius: 50px;
        font-weight: 600; transition: 0.3s all;
    }
    .stButton>button:hover {
        background: #ff6b6b; transform: translateY(-2px);
        box-shadow: 0 5px 20px rgba(235, 77, 75, 0.4);
    }
    .result-card {
        background: rgba(255, 255, 255, 0.02);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 20px; padding: 25px;
        margin-top: 20px; box-shadow: 0 10px 40px rgba(0,0,0,0.4);
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. وظائف المعالجة ---
def process_any_file(file):
    ext = file.name.split('.')[-1].lower()
    try:
        if ext == 'docx': return "\n".join([p.text for p in Document(file).paragraphs])
        elif ext == 'xlsx': return f"Excel Data: {pd.read_excel(file).to_string()}"
        elif ext == 'pptx':
            prs = Presentation(file)
            return "\n".join([sh.text for s in prs.slides for sh in s.shapes if hasattr(sh, "text")])
        elif ext in ['txt', 'py']: return file.getvalue().decode('utf-8')
    except Exception as e: return f"Error reading {file.name}: {e}"
    return ""

def generate_doc_download(content):
    doc = Document()
    doc.add_heading('AI Architect Pro Report', 0)
    doc.add_paragraph(content)
    bio = io.BytesIO()
    doc.save(bio)
    return bio.getvalue()

def encode_image(image):
    buffered = io.BytesIO()
    if image.mode in ("RGBA", "P"): image = image.convert("RGB")
    image.save(buffered, format="JPEG")
    return base64.b64encode(buffered.getvalue()).decode('utf-8')

# --- 3. المحرك الذكي الرباعي (The Multi-Brain Engine) ---
def run_ai_logic(provider, key, model, prompt, images=None):
    try:
        if provider == "Google Gemini":
            genai.configure(api_key=key)
            return genai.GenerativeModel(model).generate_content([prompt] + (images if images else [])).text
        elif provider == "Groq":
            c = Groq(api_key=key)
            if images:
                msgs = [{"role": "user", "content": [{"type": "text", "text": prompt}, {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{encode_image(images[0])}"}}]}]
            else: msgs = [{"role": "user", "content": prompt}]
            return c.chat.completions.create(model=model, messages=msgs).choices[0].message.content
        elif provider == "DeepSeek":
            c = OpenAI(api_key=key, base_url="https://api.deepseek.com")
            return c.chat.completions.create(model=model, messages=[{"role": "user", "content": prompt}]).choices[0].message.content
        elif provider == "xAI Grok":
            c = OpenAI(api_key=key, base_url="https://api.x.ai/v1")
            return c.chat.completions.create(model=model, messages=[{"role": "user", "content": prompt}]).choices[0].message.content
    except Exception as e:
        if "402" in str(e) or "Insufficient Balance" in str(e):
            return "⚠️ خطأ في الرصيد: محفظة DeepSeek فارغة. يرجى شحن الرصيد أو التبديل لمزود Gemini المجاني."
        return f"⚠️ Error: {str(e)}"

# --- 4. القائمة الجانبية (الاكتشاف والاقتراح) ---
with st.sidebar:
    st.markdown("<h1 style='color:#eb4d4b; font-size:24px;'>AI ARCHITECT</h1>", unsafe_allow_html=True)
    provider = st.selectbox("PROVIDER", ["Google Gemini", "Groq", "DeepSeek", "xAI Grok"])
    api_key = st.text_input("ACCESS KEY", type="password", placeholder="Enter Key...")
    
    model_choice = None
    if api_key:
        try:
            with st.spinner("Syncing..."):
                if provider == "Google Gemini":
                    genai.configure(api_key=api_key)
                    models = [m.name.replace('models/', '') for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
                    model_choice = st.selectbox("MODEL", models, index=0)
                elif provider == "Groq":
                    models = [m.id for m in Groq(api_key=api_key).models.list().data]
                    model_choice = st.selectbox("MODEL", models, index=0)
                elif provider == "DeepSeek":
                    model_choice = st.selectbox("MODEL", ["deepseek-chat", "deepseek-reasoner"])
                elif provider == "xAI Grok":
                    model_choice = st.selectbox("MODEL", [m.id for m in OpenAI(api_key=api_key, base_url="https://api.x.ai/v1").models.list().data])
            st.success(f"Connected to {provider}")
        except: st.error("Authentication Failed")

# --- 5. الواجهة الرئيسية ---
if api_key and model_choice:
    st.markdown("<h2 style='font-weight:300; margin-bottom:40px;'>Infinite <span style='color:#eb4d4b'>Intelligence</span></h2>", unsafe_allow_html=True)
    tabs = st.tabs(["📑 Analyzer", "🎨 Studio", "👁️ Vision", "🧠 Architect"])

    with tabs[0]: # Analyzer
        c1, c2 = st.columns([1, 1.2], gap="large")
        with c1:
            uploaded = st.file_uploader("Upload Docs (Up to 10)", accept_multiple_files=True)
            query = st.text_area("Your Request", placeholder="Summarize, analyze or compare...")
            if st.button("RUN ENGINE 🚀"):
                txt_ctx, img_ctx = "", []
                if uploaded:
                    for f in uploaded[:10]:
                        ext = f.name.split('.')[-1].lower()
                        if ext in ['jpg', 'png', 'jpeg']: img_ctx.append(Image.open(f))
                        elif ext == 'pdf':
                            pdf_doc = fitz.open(stream=f.read(), filetype="pdf")
                            for page in pdf_doc: img_ctx.append(Image.open(io.BytesIO(page.get_pixmap(matrix=fitz.Matrix(1,1)).tobytes("png"))))
                        else: txt_ctx += process_any_file(f)
                
                with st.spinner("Processing..."):
                    res = run_ai_logic(provider, api_key, model_choice, txt_ctx + "\n" + query, img_ctx)
                    st.session_state['f_out'] = res

        if 'f_out' in st.session_state:
            with c2:
                st.markdown(f'<div class="result-card">{st.session_state["f_out"]}</div>', unsafe_allow_html=True)
                st.code(st.session_state['f_out'])
                st.download_button("Export to Word", generate_doc_download(st.session_state['f_out']), "Report.docx")

    with tabs[1]: # Studio
        idea = st.text_input("Visual Vision:")
        if st.button("GENERATE PROMPT ✨"):
            res = run_ai_logic(provider, api_key, model_choice, f"Generate detailed Midjourney prompt for: {idea}")
            if res: st.markdown(f'<div class="result-card">{res}</div>', unsafe_allow_html=True)

else:
    st.markdown("<div style='text-align:center; margin-top:150px; opacity:0.3;'><h1>AI ARCHITECT</h1><p>AWAITING API KEY...</p></div>", unsafe_allow_html=True)
