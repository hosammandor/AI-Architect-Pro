import streamlit as st  # هذا هو السطر الذي كان ينقصك!
import google.generativeai as genai
from groq import Groq
from openai import OpenAI
from PIL import Image
import io, base64, time, requests, sys
import fitz  # PyMuPDF
import pandas as pd
from docx import Document
from pptx import Presentation

# --- ضبط الترميز لدعم العربية ---
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# --- 1. إعدادات الصفحة والتصميم السينمائي ---
st.set_page_config(page_title="AI Architect | Cinematic Pro", page_icon="🎨", layout="wide")

st.markdown("""
    <style>
    .stApp {
        background: radial-gradient(circle at top right, #1a1a2e, #020205);
        color: #e0e0e0;
    }
    section[data-testid="stSidebar"] {
        background: rgba(10, 10, 15, 0.9) !important;
        backdrop-filter: blur(15px);
    }
    .stButton>button {
        background: linear-gradient(135deg, #00d2ff 0%, #3a7bd5 100%);
        color: white; border-radius: 12px; font-weight: 700; width: 100%; transition: 0.4s;
    }
    .result-box {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.08);
        padding: 25px; border-radius: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. وظائف المساعدة ---
def process_office_file(file):
    ext = file.name.split('.')[-1].lower()
    content = ""
    try:
        if ext == 'docx':
            doc = Document(file); content = "\n".join([p.text for p in doc.paragraphs])
        elif ext == 'xlsx':
            df = pd.read_excel(file); content = f"Excel Data: {df.to_string()}"
    except Exception as e: content = f"Error: {e}"
    return f"--- {file.name} ---\n{content}\n"

def encode_image(image):
    buffered = io.BytesIO()
    if image.mode in ("RGBA", "P"): image = image.convert("RGB")
    image.save(buffered, format="JPEG")
    return base64.b64encode(buffered.getvalue()).decode('utf-8')

# --- 3. محرك التوليد ---
def generate_response(provider, api_key, model_name, query, images=None):
    try:
        if provider == "Google Gemini":
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel(model_name)
            res = model.generate_content([query] + (images if images else []))
            return res.text
        elif provider == "Groq (Ultra Fast)":
            client = Groq(api_key=api_key)
            if images: msgs = [{"role": "user", "content": [{"type": "text", "text": query}, {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{encode_image(images[0])}"}}]}]
            else: msgs = [{"role": "user", "content": query}]
            res = client.chat.completions.create(messages=msgs, model=model_name)
            return res.choices[0].message.content
        elif provider == "xAI Grok":
            client = OpenAI(api_key=api_key, base_url="https://api.x.ai/v1")
            msgs = [{"role": "user", "content": query}]
            res = client.chat.completions.create(model=model_name, messages=msgs)
            return res.choices[0].message.content
    except Exception as e:
        st.error(f"Error: {str(e)}"); return None

# --- 4. القائمة الجانبية (مع كشف الأخطاء) ---
with st.sidebar:
    st.markdown("<h2 style='text-align: center; color: #fff;'>⚙️ CONFIG</h2>", unsafe_allow_html=True)
    provider = st.selectbox("PROVIDER", ["Google Gemini", "Groq (Ultra Fast)", "xAI Grok"])
    api_key = st.text_input("API KEY", type="password")
    
    model_choice = None
    if api_key:
        with st.spinner("Checking Connection..."):
            try:
                if provider == "Google Gemini":
                    genai.configure(api_key=api_key)
                    models = [m.name.replace('models/', '') for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
                    model_choice = st.selectbox("MODEL", models, index=0)
                    st.success("✅ Connected")
                elif provider == "Groq (Ultra Fast)":
                    client = Groq(api_key=api_key)
                    models = [m.id for m in client.models.list().data]
                    model_choice = st.selectbox("MODEL", models, index=0)
                    st.success("✅ Connected")
                elif provider == "xAI Grok":
                    client = OpenAI(api_key=api_key, base_url="https://api.x.ai/v1")
                    models = [m.id for m in client.models.list().data]; model_choice = st.selectbox("MODEL", models)
                    st.success("✅ Connected")
            except Exception as e:
                st.error(f"❌ Authentication Failed: {str(e)}")

# --- 5. الواجهة الرئيسية ---
if api_key and model_choice:
    st.markdown("<h1 style='text-align: center; margin-bottom: 50px;'>AI ARCHITECT <span style='color:#00d2ff'>ULTIMATE</span></h1>", unsafe_allow_html=True)
    
    tabs = st.tabs(["📑 ANALYZER", "🎨 ART PROMPTS", "👁️ VISION"])

    with tabs[0]: # Analyzer
        col1, col2 = st.columns([1, 1.2])
        with col1:
            docs = st.file_uploader("Upload Docs", type=["pdf", "docx", "xlsx", "txt", "py", "jpg", "png"], accept_multiple_files=True)
            d_q = st.text_area("What to do?")
            if st.button("RUN"):
                payload_text = []
                payload_imgs = []
                if docs:
                    for d in docs:
                        ext = d.name.split('.')[-1].lower()
                        if ext in ['docx', 'xlsx']: payload_text.append(process_office_file(d))
                        elif ext == 'pdf':
                            pdf = fitz.open(stream=d.read(), filetype="pdf")
                            for p in pdf: payload_imgs.append(Image.open(io.BytesIO(p.get_pixmap(matrix=fitz.Matrix(1,1)).tobytes("png"))))
                        elif ext in ['jpg', 'png']: payload_imgs.append(Image.open(d))
                        else: payload_text.append(d.getvalue().decode('utf-8'))
                
                with st.spinner("Thinking..."):
                    res = generate_response(provider, api_key, model_choice, "".join(payload_text) + "\n" + d_q, payload_imgs)
                    if res:
                        with col2:
                            st.markdown(f'<div class="result-box">{res}</div>', unsafe_allow_html=True)
                            st.code(res)

    with tabs[1]: # Art Prompts
        idea = st.text_input("Describe visual idea")
        if st.button("Generate Art Prompt"):
            res = generate_response(provider, api_key, model_choice, f"Midjourney v6 prompt for: {idea}")
            if res: st.markdown(f'<div class="result-box">{res}</div>', unsafe_allow_html=True)

else:
    st.markdown("<div style='text-align: center; margin-top: 150px; color: #555;'><h2>AWAITING API KEY...</h2></div>", unsafe_allow_html=True)
