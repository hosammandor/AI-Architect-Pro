import streamlit as st
import google.generativeai as genai
from groq import Groq
from PIL import Image
import io, base64, time, json, os, sys
import fitz  # PyMuPDF
import pandas as pd
from docx import Document

# --- 0. ضبط النظام والملفات ---
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

KEYS_FILE = "ultimate_vault.json"

def save_to_vault(data):
    with open(KEYS_FILE, 'w') as f:
        json.dump(data, f)
    st.session_state.api_vault = data
    st.success("✅ تم تحديث المفاتيح والموديلات!")
    time.sleep(1)
    st.rerun()

def load_from_vault():
    if os.path.exists(KEYS_FILE):
        try:
            with open(KEYS_FILE, 'r') as f:
                return json.load(f)
        except: pass
    return {"Gemini": {"key": "", "label": ""}, "Groq": {"key": "", "label": ""}}

# --- 1. التصميم والثيمات (Themes) ---
st.set_page_config(page_title="AI Architect | v38.0", page_icon="🚀", layout="wide")

if 'api_vault' not in st.session_state:
    st.session_state.api_vault = load_from_vault()

with st.sidebar:
    st.markdown("### 🎨 UI Aesthetics")
    theme_choice = st.selectbox("Select Mode", ["Dark (Cinematic)", "White (Clean)", "Automatic"], key="theme_t")
    st.session_state.theme = theme_choice
    st.markdown("---")
    st.info("💡 تم تحديث موديلات Groq المتاحة لعام 2026 تلقائياً.")

if st.session_state.theme == "Dark (Cinematic)":
    bg, txt, card, brd = "radial-gradient(circle at 20% 20%, #1a1a2e 0%, #0b0b0e 100%)", "#e0e0e0", "rgba(255,255,255,0.02)", "rgba(255,255,255,0.08)"
else:
    bg, txt, card, brd = "#ffffff", "#1a1a1a", "#f8f9fa", "#dee2e6"

st.markdown(f"<style>.stApp {{ background: {bg}; color: {txt}; }} .result-card {{ background: {card}; border: 1px solid {brd}; border-radius: 20px; padding: 25px; }} .stButton>button {{ background: #eb4d4b; color: white; border-radius: 50px; font-weight: 600; width: 100%; border: none; }}</style>", unsafe_allow_html=True)

# --- 2. وظائف الذكاء والرؤية ---
def encode_img_to_base64(image):
    buffered = io.BytesIO()
    if image.mode in ("RGBA", "P"): image = image.convert("RGB")
    image.save(buffered, format="JPEG")
    return base64.b64encode(buffered.getvalue()).decode('utf-8')

def call_ai_engine(provider, key, model, prompt, images=None):
    try:
        if provider == "Gemini":
            genai.configure(api_key=key)
            content = [prompt] + (images if images else [])
            return genai.GenerativeModel(model).generate_content(content).text
        elif provider == "Groq":
            client = Groq(api_key=key)
            if images:
                b64_img = encode_img_to_base64(images[0])
                msgs = [{"role": "user", "content": [{"type": "text", "text": prompt}, {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64_img}"}}]}]
            else:
                msgs = [{"role": "user", "content": prompt}]
            return client.chat.completions.create(model=model, messages=msgs).choices[0].message.content
    except Exception as e: return f"⚠️ خطأ: {str(e)}"

# --- 3. واجهة المستخدم الرئيسية ---
st.markdown("<h1 style='text-align:center; font-weight:700;'>AI ARCHITECT <span style='color:#eb4d4b'>PRO 2026</span></h1>", unsafe_allow_html=True)
tabs = st.tabs(["📑 Analyzer", "🎨 Studio", "💼 Work Pro", "🔐 Vault"])

# --- TAB: Analyzer ---
with tabs[0]:
    c1, c2 = st.columns([1, 1.2], gap="large")
    with c1:
        prov = st.selectbox("Select Provider:", ["Gemini", "Groq"])
        info = st.session_state.api_vault[prov]
        if info["key"]:
            try:
                # جلب الموديلات الحية لتجنب خطأ Decommissioned
                if prov == "Gemini":
                    genai.configure(api_key=info["key"])
                    models = [m.name.replace('models/', '') for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
                    active_mod = st.selectbox("Active Model:", models)
                else:
                    client = Groq(api_key=info["key"])
                    # فلترة الموديلات لجلب الموديلات التي تدعم الرؤية أو الأحدث فقط
                    models = [m.id for m in client.models.list().data if "vision" in m.id or "llama-3.3" in m.id or "mixtral" in m.id]
                    active_mod = st.selectbox("Active Model:", models)
                
                files = st.file_uploader("Upload Files (Images, PDF, Docs)", accept_multiple_files=True)
                q = st.text_area("What is your question?")
                if st.button("EXECUTE ANALYSIS 🚀"):
                    img_ctx = []
                    if files:
                        for f in files:
                            if f.type.startswith('image'): img_ctx.append(Image.open(f))
                            elif f.name.endswith('.pdf'):
                                pdf = fitz.open(stream=f.read(), filetype="pdf")
                                img_ctx.append(Image.open(io.BytesIO(pdf[0].get_pixmap().tobytes("png"))))
                    
                    with st.spinner("AI is analyzing..."):
                        st.session_state.ans = call_ai_engine(prov, info["key"], active_mod, q, img_ctx)
            except: st.error("المفتاح غير صالح أو هناك مشكلة في الاتصال بالسيرفر.")
        else: st.warning("قم بإضافة المفتاح في تاب Vault.")

    if 'ans' in st.session_state:
        with c2:
            st.markdown(f'<div class="result-card">{st.session_
