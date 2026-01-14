import streamlit as st
import google.generativeai as genai
from groq import Groq
from PIL import Image
import io, base64, time, json, os, sys
import fitz  # PyMuPDF
import pandas as pd
from docx import Document

# --- 0. إعدادات النظام ---
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

KEYS_FILE = "ultimate_vault.json"

def save_to_vault(data):
    with open(KEYS_FILE, 'w') as f:
        json.dump(data, f)
    st.session_state.api_vault = data
    st.rerun()

def load_from_vault():
    if os.path.exists(KEYS_FILE):
        try:
            with open(KEYS_FILE, 'r') as f:
                return json.load(f)
        except: pass
    return {"Gemini": {"key": "", "label": ""}, "Groq": {"key": "", "label": ""}}

# --- 1. التصميم والثيمات (Sidebar Controls) ---
st.set_page_config(page_title="AI Architect | Vision Fix", page_icon="👁️", layout="wide")

if 'api_vault' not in st.session_state:
    st.session_state.api_vault = load_from_vault()

with st.sidebar:
    st.markdown("### 🎨 UI Mode")
    theme_choice = st.selectbox("Theme", ["Dark (Cinematic)", "White (Clean)"], key="theme_t")
    st.session_state.theme = theme_choice
    st.markdown("---")
    st.info("💡 لكي يرى البرنامج الصور، اختر موديلات مثل: gemini-1.5-flash أو llama-3.2-11b-vision.")

# تطبيق التصميم
if st.session_state.theme == "Dark (Cinematic)":
    bg, txt, card = "radial-gradient(circle at 20% 20%, #1a1a2e 0%, #0b0b0e 100%)", "#e0e0e0", "rgba(255,255,255,0.02)"
else:
    bg, txt, card = "#ffffff", "#1a1a1a", "#f8f9fa"

st.markdown(f"<style>.stApp {{ background: {bg}; color: {txt}; }} .result-card {{ background: {card}; border-radius: 20px; padding: 25px; border: 1px solid rgba(128,128,128,0.2); }} .stButton>button {{ background: #eb4d4b; color: white; border-radius: 50px; font-weight: 600; }}</style>", unsafe_allow_html=True)

# --- 2. وظائف معالجة الصور والرؤية ---
def encode_image(image):
    buffered = io.BytesIO()
    if image.mode in ("RGBA", "P"): image = image.convert("RGB")
    image.save(buffered, format="JPEG")
    return base64.b64encode(buffered.getvalue()).decode('utf-8')

def ask_ai_vision(provider, key, model, prompt, images=None):
    try:
        if provider == "Gemini":
            genai.configure(api_key=key)
            # الموديلات الحديثة تقبل قائمة تحتوي على النص والصور مباشرة
            content = [prompt] + (images if images else [])
            return genai.GenerativeModel(model).generate_content(content).text
        
        elif provider == "Groq":
            client = Groq(api_key=key)
            if images:
                # تحويل الصورة لـ Base64 لكي يفهمها Groq Vision
                base64_image = encode_image(images[0])
                messages = [{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                    ]
                }]
            else:
                messages = [{"role": "user", "content": prompt}]
            
            return client.chat.completions.create(model=model, messages=messages).choices[0].message.content
    except Exception as e: return f"⚠️ خطأ في المحرك: {str(e)}"

# --- 3. واجهة المستخدم ---
st.markdown("<h1 style='text-align:center;'>AI ARCHITECT <span style='color:#eb4d4b'>VISION</span></h1>", unsafe_allow_html=True)
tabs = st.tabs(["📑 Analyzer", "🎨 Art Studio", "💼 Work Pro", "🔐 Vault"])

with tabs[0]:
    c1, c2 = st.columns([1, 1.2], gap="large")
    with c1:
        prov = st.selectbox("Provider:", ["Gemini", "Groq"])
        info = st.session_state.api_vault[prov]
        if info["key"]:
            # فلترة الموديلات لضمان اختيار موديل يدعم الرؤية
            if prov == "Gemini":
                genai.configure(api_key=info["key"])
                models = [m.name.replace('models/', '') for m in genai.list_models() if 'flash' in m.name or 'pro' in m.name]
                active_mod = st.selectbox("Vision Model:", models, index=0)
            else:
                active_mod = st.selectbox("Vision Model:", ["llama-3.2-11b-vision-preview", "llama-3.2-90b-vision-preview"])
            
            files = st.file_uploader("Upload Image/PDF", accept_multiple_files=True)
            q = st.text_area("Question about image:")
            
            if st.button("START VISION ANALYSIS 👁️"):
                txt_ctx, img_ctx = "", []
                if files:
                    for f in files:
                        if f.type.startswith('image'): img_ctx.append(Image.open(f))
                        elif f.name.endswith('.pdf'):
                            pdf = fitz.open(stream=f.read(), filetype="pdf")
                            img_ctx.append(Image.open(io.BytesIO(pdf[0].get_pixmap().tobytes("png"))))
                
                with st.spinner("AI is looking at your files..."):
                    st.session_state.v_ans = ask_ai_vision(prov, info["key"], active_mod, q, img_ctx)
        else: st.warning("قم بإضافة المفتاح في تاب Vault.")

    if 'v_ans' in st.session_state:
        with c2:
            st.markdown(f'<div class="result-card">{st.session_state.v_ans}</div>', unsafe_allow_html=True)
            st.code(st.session_state.v_ans)

with tabs[3]:
    st.markdown("### 🔐 Key Vault")
    for p in ["Gemini", "Groq"]:
        st.session_state.api_vault[p]["key"] = st.text_input(f"{p} API Key:", value=st.session_state.api_vault[p]["key"], type="password", key=f"k_{p}")
    if st.button("SAVE CONFIGURATION 💾"): save_to_vault(st.session_state.api_vault)
