import streamlit as st
import google.generativeai as genai
from groq import Groq
from PIL import Image
import io, base64, time, json, os, sys
import fitz  # PyMuPDF
import pandas as pd
from docx import Document

# --- 0. إعدادات النظام والترميز ---
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

# --- 1. إعدادات الصفحة وتحكم الثيمات (القائمة الجانبية) ---
st.set_page_config(page_title="AI Architect | Work Pro", page_icon="💼", layout="wide")

with st.sidebar:
    st.markdown("## ⚙️ Settings")
    st.markdown("---")
    st.markdown("### 🎨 UI Aesthetics")
    theme_choice = st.selectbox(
        "Select Lighting Mode", 
        ["Dark (Cinematic)", "White (Clean)", "Automatic (Device)"],
        key="theme_selector"
    )
    st.session_state.theme = theme_choice
    st.markdown("---")
    st.info("💡 زر الثيمات يتحكم في مظهر التطبيق بالكامل.")

# منطق ألوان التصميم
if st.session_state.theme == "Dark (Cinematic)":
    bg_gradient, text_color, card_bg, border_color = "radial-gradient(circle at 20% 20%, #1a1a2e 0%, #0b0b0e 100%)", "#e0e0e0", "rgba(255, 255, 255, 0.02)", "rgba(255, 255, 255, 0.08)"
    sidebar_bg = "#0f0f14"
elif st.session_state.theme == "White (Clean)":
    bg_gradient, text_color, card_bg, border_color = "#ffffff", "#1a1a1a", "#f8f9fa", "#dee2e6"
    sidebar_bg = "#f0f2f6"
else:
    bg_gradient, text_color, card_bg, border_color = "transparent", "inherit", "rgba(128, 128, 128, 0.05)", "rgba(128, 128, 128, 0.1)"
    sidebar_bg = "inherit"

st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&display=swap');
    .stApp {{ background: {bg_gradient}; color: {text_color}; font-family: 'Inter', sans-serif; transition: 0.5s all; }}
    section[data-testid="stSidebar"] {{ background-color: {sidebar_bg} !important; border-right: 1px solid {border_color}; }}
    .result-card {{ background: {card_bg}; border: 1px solid {border_color}; border-radius: 20px; padding: 25px; margin-top: 20px; box-shadow: 0 10px 40px rgba(0,0,0,0.2); backdrop-filter: blur(10px); }}
    .stButton>button {{ background: linear-gradient(135deg, #eb4d4b 0%, #ff6b6b 100%); color: white; border-radius: 50px; font-weight: 600; width: 100%; }}
    .stTabs [aria-selected="true"] {{ color: #eb4d4b !important; border-bottom: 2px solid #eb4d4b !important; }}
    </style>
    """, unsafe_allow_html=True)

# --- 2. إدارة الحالة والمحرك ---
if 'api_vault' not in st.session_state:
    st.session_state.api_vault = load_from_vault()

def run_ai_logic(provider, key, model, prompt):
    try:
        if provider == "Gemini":
            genai.configure(api_key=key)
            return genai.GenerativeModel(model).generate_content(prompt).text
        elif provider == "Groq":
            c = Groq(api_key=key)
            return c.chat.completions.create(model=model, messages=[{"role": "user", "content": prompt}]).choices[0].message.content
    except Exception as e: return f"⚠️ Error: {str(e)}"

# --- 3. واجهة المستخدم الرئيسية ---
st.markdown("<h1 style='text-align:center; letter-spacing:-2px;'>AI ARCHITECT <span style='color:#eb4d4b'>ULTIMATE</span></h1>", unsafe_allow_html=True)

tabs = st.tabs(["📑 Analyzer", "🎨 Art Studio", "💼 Work Architect", "🔐 Key Vault"])

# --- TAB 1: Analyzer (كما هو) ---
with tabs[0]:
    st.markdown("### 📑 Deep Data Analysis")
    # ... (كود المحلل السابق) ...
    st.info("استخدم هذا التاب لتحليل ملفاتك وصورك.")

# --- TAB 2: Art Studio (للميدجورني) ---
with tabs[1]:
    st.markdown("### 🎨 Midjourney Art Studio")
    art_input = st.text_input("Enter your creative idea:")
    if st.button("Generate Art Prompt ✨"):
        # منطق التوليد...
        pass

# --- TAB 3: Work Architect (التاب الجديد لطلبات العمل الطبيعية) ---
with tabs[2]:
    st.markdown("### 💼 Professional Work Architect")
    st.write("حول طلباتك البسيطة إلى أوامر احترافية منظمة للحصول على أفضل النتائج في العمل.")
    
    

    col_a, col_b = st.columns([1, 1.2], gap="large")
    with col_a:
        task_type = st.selectbox(
            "What is the task type?",
            ["Email Drafting", "Report Summarization", "Code Debugging", "Marketing Content", "Strategic Planning", "Translation"]
        )
        basic_task = st.text_area("What do you want to do? (Basic description)", placeholder="e.g. Write an email to my boss about a 2-day leave...")
        audience = st.text_input("Who is the audience? (Optional)", placeholder="e.g. My Manager, Clients, Developers...")
        
        if st.button("CRAFT WORK PROMPT 🔨"):
            # بناء برومبت هندسي ذكي
            engineering_prompt = f"""
            Act as a Professional Prompt Engineer. I want you to turn the following basic task into a high-quality, 
            detailed AI prompt. Use the 'Role-Task-Context-Format' framework.
            
            Basic Task: {basic_task}
            Task Category: {task_type}
            Audience: {audience}
            
            The final prompt should be natural, professional, and tell the AI exactly how to think and respond.
            Return ONLY the engineered prompt in English and Arabic.
            """
            
            # استخدام المفتاح المتوفر
            key = st.session_state.api_vault["Gemini"]["key"] or st.session_state.api_vault["Groq"]["key"]
            if key:
                prov = "Gemini" if st.session_state.api_vault["Gemini"]["key"] else "Groq"
                mod = "gemini-2.0-flash" if prov == "Gemini" else "llama-3.3-70b-versatile"
                with st.spinner("Engineering your prompt..."):
                    pro_res = run_ai_logic(prov, key, mod, engineering_prompt)
                    st.session_state.work_pro_res = pro_res
            else:
                st.warning("⚠️ يرجى إضافة مفتاح في تاب Vault أولاً.")

    if 'work_pro_res' in st.session_state:
        with col_b:
            st.markdown("#### 🚀 Your Professional Prompt")
            st.markdown(f'<div class="result-card">{st.session_state.work_pro_res}</div>', unsafe_allow_html=True)
            st.markdown("📋 **Copy the prompt below to use with any AI:**")
            st.code(st.session_state.work_pro_res)

# --- TAB 4: Key Vault ---
with tabs[3]:
    st.markdown("### 🔐 Key Vault")
    # ... (كود الفولت كما هو) ...
    for p in ["Gemini", "Groq"]:
        st.session_state.api_vault[p]["key"] = st.text_input(f"{p} API Key:", value=st.session_state.api_vault[p]["key"], type="password", key=f"v_k_{p}")
    if st.button("SAVE AND CONNECT 🔗"):
        save_to_vault(st.session_state.api_vault)
