import streamlit as st
import google.generativeai as genai
from groq import Groq
from PIL import Image
import io, base64, time, json, os, sys
import fitz  # PyMuPDF
import pandas as pd
from docx import Document

# --- 0. ضبط الترميز والبيئة ---
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

KEYS_FILE = "free_keys_config.json"

def save_keys_to_vault(keys_dict):
    with open(KEYS_FILE, 'w') as f:
        json.dump(keys_dict, f)

def load_keys_from_vault():
    if os.path.exists(KEYS_FILE):
        try:
            with open(KEYS_FILE, 'r') as f:
                return json.load(f)
        except: pass
    return {"Gemini": "", "Groq": ""}

# --- 1. تصميم الواجهة السينمائية (Midjourney Dark Style) ---
st.set_page_config(page_title="AI Architect | Free Edition", page_icon="🪄", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&display=swap');
    .stApp { background: radial-gradient(circle at 20% 20%, #1a1a2e 0%, #0b0b0e 100%); color: #e0e0e0; font-family: 'Inter', sans-serif; }
    .stTabs [aria-selected="true"] { color: #eb4d4b !important; border-bottom: 2px solid #eb4d4b !important; }
    .stButton>button { background: #eb4d4b; color: white; border-radius: 50px; font-weight: 600; width: 100%; transition: 0.3s; }
    .stButton>button:hover { background: #ff6b6b; transform: scale(1.02); }
    .result-card { background: rgba(255, 255, 255, 0.02); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 20px; padding: 25px; box-shadow: 0 10px 40px rgba(0,0,0,0.4); }
    </style>
    """, unsafe_allow_html=True)

# --- 2. إدارة الحالة والمفاتيح ---
if 'free_keys' not in st.session_state:
    st.session_state.free_keys = load_keys_from_vault()

# --- 3. محرك التوليد (المجاني فقط) ---
def run_ai_free(provider, key, model, prompt, images=None):
    try:
        if provider == "Google Gemini":
            genai.configure(api_key=key)
            return genai.GenerativeModel(model).generate_content([prompt] + (images if images else [])).text
        elif provider == "Groq":
            c = Groq(api_key=key)
            return c.chat.completions.create(model=model, messages=[{"role": "user", "content": prompt}]).choices[0].message.content
    except Exception as e: return f"⚠️ خطأ: {str(e)}"

# --- 4. واجهة المستخدم الرئيسية ---
st.markdown("<h1 style='text-align:center;'>AI ARCHITECT <span style='color:#eb4d4b'>FREE POWER</span></h1>", unsafe_allow_html=True)

tabs = st.tabs(["📑 Analyzer", "🎨 Studio", "🔐 Key Vault"])

# --- TAB: Key Vault (لحفظ المفاتيح المجانية) ---
with tabs[2]:
    st.markdown("### 🔐 Free Key Vault")
    st.info("قم بحفظ مفاتيح Gemini و Groq لتفعيل البرنامج مجاناً بالكامل.")
    col_k1, col_k2 = st.columns(2)
    with col_k1:
        v_gem = st.text_input("Gemini API Key:", value=st.session_state.free_keys["Gemini"], type="password")
    with col_k2:
        v_groq = st.text_input("Groq API Key:", value=st.session_state.free_keys["Groq"], type="password")
    
    if st.button("SAVE KEYS 💾"):
        new_keys = {"Gemini": v_gem, "Groq": v_groq}
        st.session_state.free_keys = new_keys
        save_keys_to_vault(new_keys)
        st.success("تم الحفظ بنجاح! البرنامج جاهز للعمل مجاناً.")

# --- TAB: Analyzer ---
with tabs[0]:
    c1, c2 = st.columns([1, 1.2], gap="large")
    with c1:
        provider_choice = st.selectbox("Select Free Brain:", ["Google Gemini", "Groq"])
        active_key = st.session_state.free_keys.get(provider_choice)
        
        selected_model = ""
        if active_key:
            try:
                if provider_choice == "Google Gemini":
                    genai.configure(api_key=active_key)
                    models = [m.name.replace('models/', '') for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
                    selected_model = st.selectbox("Select Free Model:", models, index=0)
                else:
                    selected_model = st.selectbox("Select Free Model:", [m.id for m in Groq(api_key=active_key).models.list().data])
            except: st.warning("تأكد من صحة المفتاح المسجل.")

        files = st.file_uploader("Upload Docs or Images", accept_multiple_files=True)
        user_input = st.text_area("What's the mission?")
        if st.button("RUN ANALYSIS 🚀"):
            with st.spinner("Analyzing..."):
                res = run_ai_free(provider_choice, active_key, selected_model, user_input)
                st.session_state.result_free = res

    if 'result_free' in st.session_state:
        with c2:
            st.markdown(f'<div class="result-card">{st.session_state.result_free}</div>', unsafe_allow_html=True)
            st.code(st.session_state.result_free)
