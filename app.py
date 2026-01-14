import streamlit as st
import google.generativeai as genai
from groq import Groq
from PIL import Image
import io, base64, time, json, os, sys
import fitz  # PyMuPDF
import pandas as pd
from docx import Document
from pptx import Presentation

# --- 0. إعدادات النظام ---
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

KEYS_FILE = "pure_vault.json"

def save_to_vault(data):
    with open(KEYS_FILE, 'w') as f:
        json.dump(data, f)
    st.session_state.api_vault = data
    st.success("✅ تم الحفظ! جاري تحديث الواجهة...")
    time.sleep(1)
    st.rerun() 

def load_from_vault():
    if os.path.exists(KEYS_FILE):
        try:
            with open(KEYS_FILE, 'r') as f:
                return json.load(f)
        except: pass
    return {"Gemini": {"key": "", "label": ""}, "Groq": {"key": "", "label": ""}}

# --- 1. إعدادات الصفحة وتحكم الثيمات (Theme Toggle) ---
st.set_page_config(page_title="AI Architect | Cinematic", page_icon="🎨", layout="wide")

# القائمة الجانبية - هنا يوجد زر الثيمات
with st.sidebar:
    st.markdown("## ⚙️ Settings")
    st.markdown("---")
    # زر تبديل الإضاءة
    st.markdown("### 🎨 UI Aesthetics")
    theme_choice = st.selectbox(
        "Select Lighting Mode", 
        ["Dark (Cinematic)", "White (Clean)", "Automatic (Device)"],
        key="theme_selector"
    )
    st.session_state.theme = theme_choice
    st.markdown("---")

# اختيار ألوان التصميم بناءً على الثيم
if st.session_state.theme == "Dark (Cinematic)":
    bg_gradient = "radial-gradient(circle at 20% 20%, #1a1a2e 0%, #0b0b0e 100%)"
    text_color = "#e0e0e0"
    card_bg = "rgba(255, 255, 255, 0.02)"
    border_color = "rgba(255, 255, 255, 0.08)"
    sidebar_bg = "#0f0f14"
elif st.session_state.theme == "White (Clean)":
    bg_gradient = "#ffffff"
    text_color = "#1a1a1a"
    card_bg = "#f8f9fa"
    border_color = "#dee2e6"
    sidebar_bg = "#f0f2f6"
else: # Automatic
    bg_gradient = "transparent"
    text_color = "inherit"
    card_bg = "rgba(128, 128, 128, 0.05)"
    border_color = "rgba(128, 128, 128, 0.1)"
    sidebar_bg = "inherit"

st.markdown(f"""
    <style>
    .stApp {{ background: {bg_gradient}; color: {text_color}; transition: 0.5s all; }}
    section[data-testid="stSidebar"] {{ background-color: {sidebar_bg} !important; }}
    .result-card {{ 
        background: {card_bg}; 
        border: 1px solid {border_color}; 
        border-radius: 20px; padding: 25px; margin-top: 20px; 
    }}
    .stButton>button {{ background: #eb4d4b; color: white; border-radius: 50px; font-weight: 600; width: 100%; }}
    .copy-label {{ font-size: 12px; color: #888; margin-top: 15px; }}
    </style>
    """, unsafe_allow_html=True)

# --- 2. إدارة الحالة ---
if 'api_vault' not in st.session_state:
    st.session_state.api_vault = load_from_vault()

# --- 3. وظائف المعالجة والذكاء ---
def process_file_content(file):
    ext = file.name.split('.')[-1].lower()
    try:
        if ext == 'docx': return "\n".join([p.text for p in Document(file).paragraphs])
        elif ext == 'xlsx': return f"Data: {pd.read_excel(file).to_string()}"
        elif ext in ['txt', 'py']: return file.getvalue().decode('utf-8')
    except: return f"Error in {file.name}"
    return ""

def run_ai_logic(provider, key, model, prompt, images=None):
    try:
        if provider == "Gemini":
            genai.configure(api_key=key)
            return genai.GenerativeModel(model).generate_content([prompt] + (images if images else [])).text
        elif provider == "Groq":
            c = Groq(api_key=key)
            return c.chat.completions.create(model=model, messages=[{"role": "user", "content": prompt}]).choices[0].message.content
    except Exception as e: return f"⚠️ Error: {str(e)}"

# --- 4. واجهة المستخدم الرئيسية ---
st.markdown("<h1 style='text-align:center;'>AI ARCHITECT <span style='color:#eb4d4b'>PRO</span></h1>", unsafe_allow_html=True)

tabs = st.tabs(["📑 Analyzer", "🎨 Studio", "🔐 Key Vault"])

# --- Analyzer Tab ---
with tabs[0]:
    col1, col2 = st.columns([1, 1.2], gap="large")
    with col1:
        choice = st.selectbox("Select Brain:", ["Gemini", "Groq"])
        acc_info = st.session_state.api_vault.get(choice)
        
        if acc_info and acc_info["key"]:
            try:
                if choice == "Gemini":
                    genai.configure(api_key=acc_info["key"])
                    models = [m.name.replace('models/', '') for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
                    active_model = st.selectbox("Model:", models)
                else:
                    active_model = st.selectbox("Model:", [m.id for m in Groq(api_key=acc_info["key"]).models.list().data])
                
                uploaded = st.file_uploader("Upload Files", accept_multiple_files=True)
                query = st.text_area("Request:")
                if st.button("RUN ENGINE 🚀"):
                    with st.spinner("Analyzing..."):
                        res = run_ai_logic(choice, acc_info["key"], active_model, query)
                        st.session_state.last_res = res
            except: st.error("المفتاح غير صالح")
        else: st.warning("اذهب لتاب Vault لإضافة المفتاح.")

    if 'last_res' in st.session_state:
        with col2:
            st.markdown(f'<div class="result-card">{st.session_state.last_res}</div>', unsafe_allow_html=True)
            # زر النسخ التلقائي
            st.markdown('<p class="copy-label">📋 Copy Result:</p>', unsafe_allow_html=True)
            st.code(st.session_state.last_res)

# --- Vault Tab ---
with tabs[2]:
    st.markdown("### 🔐 Key Vault")
    for p in ["Gemini", "Groq"]:
        st.session_state.api_vault[p]["key"] = st.text_input(f"{p} API Key:", value=st.session_state.api_vault[p]["key"], type="password", key=f"vault_{p}")
    if st.button("SAVE AND CONNECT 🔗"):
        save_to_vault(st.session_state.api_vault)
