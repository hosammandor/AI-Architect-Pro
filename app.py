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

# --- ضبط الترميز واللغة ---
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# --- 1. تصميم الواجهة السينمائية (Midjourney Reference) ---
st.set_page_config(page_title="AI Architect | Cinematic", page_icon="🎨", layout="wide")

st.markdown("""
    <style>
    /* الخطوط والخلفية الأساسية */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&display=swap');
    
    .stApp {
        background-color: #0b0b0e;
        background-image: radial-gradient(circle at 20% 20%, #1a1a2e 0%, #0b0b0e 100%);
        color: #e0e0e0;
        font-family: 'Inter', sans-serif;
    }

    /* تنسيق السايد بار (Midjourney Style) */
    section[data-testid="stSidebar"] {
        background-color: rgba(15, 15, 20, 0.95) !important;
        border-right: 1px solid rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(20px);
    }
    
    /* تنسيق التابات */
    .stTabs [data-baseweb="tab-list"] {
        gap: 30px;
        background-color: transparent;
        border-bottom: 1px solid rgba(255, 255, 255, 0.05);
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        background-color: transparent;
        color: #888;
        font-weight: 300;
        transition: 0.4s;
        border: none;
    }
    .stTabs [aria-selected="true"] {
        color: #ff4b4b !important; /* لون Midjourney المميز في أزرار Sign up */
        border-bottom: 2px solid #ff4b4b !important;
        background-color: transparent !important;
    }

    /* صناديق الإدخال والنتائج (Glassmorphism) */
    .stTextArea textarea, .stTextInput input {
        background-color: rgba(255, 255, 255, 0.03) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 12px !important;
        color: #fff !important;
    }
    
    .result-card {
        background: rgba(255, 255, 255, 0.02);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 20px;
        padding: 30px;
        box-shadow: 0 10px 40px rgba(0,0,0,0.4);
        margin-top: 20px;
    }

    /* الأزرار الاحترافية */
    .stButton>button {
        background: #eb4d4b;
        color: white;
        border: none;
        padding: 12px 24px;
        border-radius: 50px;
        font-weight: 600;
        letter-spacing: 0.5px;
        transition: 0.3s all;
        width: auto;
        min-width: 160px;
    }
    .stButton>button:hover {
        background: #ff6b6b;
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(235, 77, 75, 0.4);
    }

    /* كود بلوك بلمسة فنية */
    code {
        background-color: rgba(0,0,0,0.3) !important;
        color: #00d2ff !important;
        border-radius: 8px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. وظائف معالجة البيانات ---
def process_file(file):
    ext = file.name.split('.')[-1].lower()
    try:
        if ext == 'docx':
            doc = Document(file)
            return "\n".join([p.text for p in doc.paragraphs])
        elif ext == 'xlsx':
            df = pd.read_excel(file)
            return df.to_string()
        elif ext == 'pptx':
            prs = Presentation(file)
            text = ""
            for s in prs.slides:
                for sh in s.shapes:
                    if hasattr(sh, "text"): text += sh.text + "\n"
            return text
        elif ext in ['txt', 'py']:
            return file.getvalue().decode('utf-8')
    except Exception as e:
        return f"Error: {e}"
    return ""

def get_binary_download(content, type='word'):
    bio = io.BytesIO()
    if type == 'word':
        doc = Document()
        doc.add_paragraph(content)
        doc.save(bio)
    return bio.getvalue()

# --- 3. محرك التوليد الموحد ---
def ask_ai(provider, key, model, prompt, imgs=None):
    try:
        if provider == "Google Gemini":
            genai.configure(api_key=key)
            m = genai.GenerativeModel(model)
            return m.generate_content([prompt] + (imgs if imgs else [])).text
        elif provider == "Groq":
            c = Groq(api_key=key)
            msgs = [{"role": "user", "content": prompt}]
            return c.chat.completions.create(messages=msgs, model=model).choices[0].message.content
        elif provider == "xAI Grok":
            c = OpenAI(api_key=key, base_url="https://api.x.ai/v1")
            return c.chat.completions.create(model=model, messages=[{"role": "user", "content": prompt}]).choices[0].message.content
    except Exception as e:
        return f"Error: {str(e)}"

# --- 4. القائمة الجانبية (Configuration) ---
with st.sidebar:
    st.markdown("<h1 style='color:#eb4d4b; font-size:24px;'>Midjourney AI</h1>", unsafe_allow_html=True)
    st.markdown("---")
    provider = st.selectbox("CHOOSE ARCHITECT", ["Google Gemini", "Groq", "xAI Grok"])
    api_key = st.text_input("ACCESS TOKEN", type="password", placeholder="Enter your API key...")
    
    model_choice = None
    if api_key:
        with st.spinner("Fetching Models..."):
            try:
                if provider == "Google Gemini":
                    genai.configure(api_key=api_key)
                    models = [m.name.replace('models/', '') for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
                    model_choice = st.selectbox("SELECT BRAIN", models)
                elif provider == "Groq":
                    c = Groq(api_key=api_key)
                    models = [m.id for m in c.models.list().data]
                    model_choice = st.selectbox("SELECT BRAIN", models)
                elif provider == "xAI Grok":
                    c = OpenAI(api_key=api_key, base_url="https://api.x.ai/v1")
                    models = [m.id for m in c.models.list().data]
                    model_choice = st.selectbox("SELECT BRAIN", models)
            except:
                st.error("Invalid Token")

# --- 5. الواجهة الرئيسية ---
if api_key and model_choice:
    st.markdown("<h2 style='letter-spacing:-1px; font-weight:300;'>Explore <span style='color:#eb4d4b'>Intelligence</span></h2>", unsafe_allow_html=True)
    
    tabs = st.tabs(["📑 Analyzer", "🎨 Prompt Studio", "👁️ Vision", "🧠 Architect"])

    with tabs[0]: # Analyzer
        col1, col2 = st.columns([1, 1.2], gap="large")
        with col1:
            st.markdown("#### Upload Data")
            files = st.file_uploader("Drop images, docs or code", accept_multiple_files=True)
            query = st.text_area("What's the mission?", placeholder="Summarize these files or extract insights...")
            if st.button("START ANALYSIS"):
                context = ""
                images = []
                if files:
                    for f in files:
                        ext = f.name.split('.')[-1].lower()
                        if ext in ['jpg', 'png', 'jpeg']:
                            images.append(Image.open(f))
                        elif ext == 'pdf':
                            pdf = fitz.open(stream=f.read(), filetype="pdf")
                            for p in pdf: images.append(Image.open(io.BytesIO(p.get_pixmap(matrix=fitz.Matrix(1,1)).tobytes("png"))))
                        else:
                            context += process_file(f)
                
                with st.spinner("Processing..."):
                    response = ask_ai(provider, api_key, model_choice, context + "\n" + query, images)
                    st.session_state['res'] = response
        
        if 'res' in st.session_state:
            with col2:
                st.markdown(f'<div class="result-card">{st.session_state["res"]}</div>', unsafe_allow_html=True)
                st.code(st.session_state['res']) # Copy feature
                st.download_button("Export as Word", get_binary_download(st.session_state['res']), "Report.docx")

    with tabs[1]: # Prompt Studio
        st.markdown("#### Artistic Prompt Generator")
        idea = st.text_input("Describe your visual vision:", placeholder="A futuristic city in the style of Van Gogh...")
        if st.button("CRAFT PROMPT"):
            res = ask_ai(provider, api_key, model_choice, f"Create a detailed Midjourney v6 prompt for: {idea}")
            if res: st.markdown(f'<div class="result-card">{res}</div>', unsafe_allow_html=True)

    with tabs[2]: # Vision
        v_files = st.file_uploader("Upload images for visual intelligence", type=['jpg','png'], key="vision")
        if v_files:
            if st.button("DESCRIBE IMAGE"):
                res = ask_ai(provider, api_key, model_choice, "Describe this image in detail", [Image.open(v_files)])
                st.markdown(f'<div class="result-card">{res}</div>', unsafe_allow_html=True)

    with tabs[3]: # Architect
        st.markdown("#### Master Prompt Builder")
        u_idea = st.text_area("Your complex request:")
        if st.button("BUILD ARCHITECTURE"):
            res = ask_ai(provider, api_key, model_choice, f"Engineer a professional AI prompt for: {u_idea}")
            st.code(res)

else:
    st.markdown("""
        <div style='text-align: center; margin-top: 100px; opacity: 0.5;'>
            <h1 style='font-size: 60px;'>Midjourney</h1>
            <p style='font-size: 20px;'>AWAITING AUTHENTICATION...</p>
        </div>
    """, unsafe_allow_html=True)
