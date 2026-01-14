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
    st.success("✅ تم الحفظ والربط بنجاح!")
    time.sleep(1)
    st.rerun() 

def load_from_vault():
    if os.path.exists(KEYS_FILE):
        try:
            with open(KEYS_FILE, 'r') as f:
                return json.load(f)
        except: pass
    return {"Gemini": {"key": "", "label": ""}, "Groq": {"key": "", "label": ""}}

# --- 1. إعدادات الصفحة وTheme Toggle (موجود في السايد بار) ---
st.set_page_config(page_title="AI Architect | Creator", page_icon="🎨", layout="wide")

with st.sidebar:
    st.markdown("## 🌓 UI Settings")
    theme_choice = st.selectbox("Lighting Mode", ["Dark (Cinematic)", "White (Clean)", "Automatic (Device)"])
    st.session_state.theme = theme_choice
    st.markdown("---")
    st.info("💡 افتح القائمة الجانبية في أي وقت لتغيير الإضاءة.")

# تخصيص الألوان بناءً على الثيم
if st.session_state.theme == "Dark (Cinematic)":
    bg_style = "radial-gradient(circle at 20% 20%, #1a1a2e 0%, #0b0b0e 100%)"
    text_col = "#e0e0e0"
    card_bg = "rgba(255, 255, 255, 0.02)"
    border_col = "rgba(255, 255, 255, 0.08)"
elif st.session_state.theme == "White (Clean)":
    bg_style = "#ffffff"
    text_col = "#1a1a1a"
    card_bg = "#f8f9fa"
    border_col = "#dee2e6"
else:
    bg_style = "transparent"
    text_col = "inherit"
    card_bg = "rgba(128, 128, 128, 0.05)"
    border_col = "rgba(128, 128, 128, 0.1)"

st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&display=swap');
    .stApp {{ background: {bg_style}; color: {text_col}; font-family: 'Inter', sans-serif; transition: 0.5s all; }}
    .result-card {{ 
        background: {card_bg}; border: 1px solid {border_col}; 
        border-radius: 20px; padding: 25px; margin-top: 25px; 
        backdrop-filter: blur(10px); box-shadow: 0 10px 30px rgba(0,0,0,0.2);
    }}
    .stButton>button {{ background: linear-gradient(135deg, #eb4d4b 0%, #ff6b6b 100%); color: white; border-radius: 50px; font-weight: 600; width: 100%; border: none; padding: 10px; }}
    .stButton>button:hover {{ transform: scale(1.02); box-shadow: 0 5px 15px rgba(235,77,75,0.4); }}
    .copy-section {{ font-size: 12px; color: #888; margin-top: 20px; }}
    </style>
    """, unsafe_allow_html=True)

# --- 2. إدارة الحالة ---
if 'api_vault' not in st.session_state:
    st.session_state.api_vault = load_from_vault()

# --- 3. وظائف المساعدة والذكاء ---
def run_ai(provider, key, model, prompt, images=None):
    try:
        if provider == "Gemini":
            genai.configure(api_key=key)
            return genai.GenerativeModel(model).generate_content([prompt] + (images if images else [])).text
        elif provider == "Groq":
            c = Groq(api_key=key)
            return c.chat.completions.create(model=model, messages=[{"role": "user", "content": prompt}]).choices[0].message.content
    except Exception as e: return f"⚠️ Error: {str(e)}"

# --- 4. واجهة المستخدم الرئيسية ---
st.markdown("<h1 style='text-align:center; font-weight:700; letter-spacing:-2px;'>AI ARCHITECT <span style='color:#eb4d4b'>CREATOR</span></h1>", unsafe_allow_html=True)

tabs = st.tabs(["📑 Analyzer", "🎨 Prompt Studio", "🔐 Key Vault"])

# --- TAB: Prompt Studio (الطلب الأساسي) ---
with tabs[1]:
    st.markdown("### 🎨 Midjourney v6 Prompt Studio")
    st.write("حول أفكارك البسيطة إلى أوامر بصرية مذهلة.")
    
    col_a, col_b = st.columns([1, 1.2], gap="large")
    with col_a:
        art_idea = st.text_area("What is your vision?", placeholder="e.g. A futuristic Cairo in the year 2099, neon lights, rainy atmosphere...", height=150)
        style = st.selectbox("Art Style", ["Cinematic", "Cyberpunk", "Hyper-Realistic", "Anime", "Oil Painting", "Architectural Sketch"])
        
        if st.button("GENERATE MASTER PROMPT ✨"):
            # استخدام أفضل مفتاح متاح تلقائياً
            active_key = st.session_state.api_vault["Gemini"]["key"] or st.session_state.api_vault["Groq"]["key"]
            active_prov = "Gemini" if st.session_state.api_vault["Gemini"]["key"] else "Groq"
            active_mod = "gemini-2.0-flash" if active_prov == "Gemini" else "llama-3.3-70b-versatile"
            
            if active_key:
                with st.spinner("Engineering prompt..."):
                    prompt_query = f"Act as a Midjourney expert. Create a detailed, high-quality v6 prompt for: {art_idea}. Style: {style}. Include lighting, camera settings, and --ar 16:9."
                    res = run_ai(active_prov, active_key, active_mod, prompt_query)
                    st.session_state.art_res = res
            else:
                st.warning("⚠️ يرجى إضافة مفتاح (Gemini أو Groq) في تاب Vault أولاً.")

    if 'art_res' in st.session_state:
        with col_b:
            st.markdown(f'<div class="result-card">{st.session_state.art_res}</div>', unsafe_allow_html=True)
            st.markdown('<p class="copy-section">📋 Copy and paste into Midjourney:</p>', unsafe_allow_html=True)
            st.code(st.session_state.art_res, language=None)

# --- TAB: Analyzer ---
with tabs[0]:
    # (كود المحلل كما هو مع إضافة ميزة النسخ)
    c1, c2 = st.columns([1, 1.2], gap="large")
    with c1:
        provider = st.selectbox("Select Provider:", ["Gemini", "Groq"], key="analyzer_p")
        k_info = st.session_state.api_vault.get(provider)
        if k_info and k_info["key"]:
            st.info(f"Connected to: {k_info['label']}")
            q = st.text_area("Mission Instructions:", key="analyzer_q")
            if st.button("RUN ENGINE 🚀"):
                with st.spinner("Thinking..."):
                    mod = "gemini-2.0-flash" if provider == "Gemini" else "llama-3.3-70b-versatile"
                    res = run_ai(provider, k_info["key"], mod, q)
                    st.session_state.last_analysis = res
        else: st.warning("قم بإعداد المفاتيح أولاً.")

    if 'last_analysis' in st.session_state:
        with c2:
            st.markdown(f'<div class="result-card">{st.session_state.last_analysis}</div>', unsafe_allow_html=True)
            st.code(st.session_state.last_analysis)

# --- TAB: Key Vault ---
with tabs[2]:
    st.markdown("### 🔐 Secure Vault")
    for p in ["Gemini", "Groq"]:
        col1, col2 = st.columns([2, 1])
        with col1: st.session_state.api_vault[p]["key"] = st.text_input(f"{p} API Key:", value=st.session_state.api_vault[p]["key"], type="password", key=f"vault_key_{p}")
        with col2: st.session_state.api_vault[p]["label"] = st.text_input(f"Label:", value=st.session_state.api_vault[p]["label"], key=f"vault_lbl_{p}")
    if st.button("SAVE AND CONNECT 🔗"):
        save_to_vault(st.session_state.api_vault)
