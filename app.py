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

def load_from_vault():
    if os.path.exists(KEYS_FILE):
        try:
            with open(KEYS_FILE, 'r') as f:
                data = json.load(f)
                return {p: data.get(p, {"key": "", "label": ""}) for p in ["Gemini", "Groq"]}
        except: pass
    return {p: {"key": "", "label": ""} for p in ["Gemini", "Groq"]}

# --- 1. محرك الإضاءة (Theme Engine) ---
if 'theme' not in st.session_state:
    st.session_state.theme = "Dark (Cinematic)"

with st.sidebar:
    st.markdown("### 🌓 UI Lighting Mode")
    theme_choice = st.selectbox("Select Theme", ["Dark (Cinematic)", "White (Clean)", "Automatic (Device)"])
    st.session_state.theme = theme_choice

# تطبيق الـ CSS بناءً على اختيار الإضاءة
if st.session_state.theme == "Dark (Cinematic)":
    main_bg, text_col, card_bg, border_col = "radial-gradient(circle at 20% 20%, #1a1a2e 0%, #0b0b0e 100%)", "#e0e0e0", "rgba(255,255,255,0.03)", "rgba(255,255,255,0.08)"
elif st.session_state.theme == "White (Clean)":
    main_bg, text_col, card_bg, border_col = "#ffffff", "#1a1a1a", "#f8f9fa", "#dee2e6"
else:
    main_bg, text_col, card_bg, border_col = "transparent", "inherit", "rgba(128,128,128,0.05)", "rgba(128,128,128,0.1)"

st.markdown(f"""
    <style>
    .stApp {{ background: {main_bg}; color: {text_col}; }}
    .result-card {{ background: {card_bg}; border: 1px solid {border_col}; border-radius: 20px; padding: 25px; margin-top: 20px; }}
    .stButton>button {{ background: #eb4d4b; color: white; border-radius: 50px; font-weight: 600; width: 100%; }}
    .account-tag {{ background: rgba(0, 210, 255, 0.1); color: #00d2ff; padding: 4px 12px; border-radius: 8px; font-size: 13px; font-weight: 600; }}
    </style>
    """, unsafe_allow_html=True)

# --- 2. إدارة الحالة ---
if 'api_vault' not in st.session_state:
    st.session_state.api_vault = load_from_vault()

# --- 3. وظائف المعالجة والذكاء ---
def process_any_file(file):
    ext = file.name.split('.')[-1].lower()
    try:
        if ext == 'docx': return "\n".join([p.text for p in Document(file).paragraphs])
        elif ext == 'xlsx': return f"Excel Data: {pd.read_excel(file).to_string()}"
        elif ext == 'pptx':
            prs = Presentation(file)
            return "\n".join([sh.text for s in prs.slides for sh in s.shapes if hasattr(sh, "text")])
        elif ext in ['txt', 'py']: return file.getvalue().decode('utf-8')
    except: return f"Error in {file.name}"
    return ""

def run_pure_ai(provider, key, model, prompt, images=None):
    try:
        if provider == "Google Gemini":
            genai.configure(api_key=key)
            return genai.GenerativeModel(model).generate_content([prompt] + (images if images else [])).text
        elif provider == "Groq":
            c = Groq(api_key=key)
            return c.chat.completions.create(model=model, messages=[{"role": "user", "content": prompt}]).choices[0].message.content
    except Exception as e: return f"⚠️ Error: {str(e)}"

# --- 4. واجهة المستخدم الرئيسية ---
st.markdown("<h1 style='text-align:center;'>AI ARCHITECT <span style='color:#eb4d4b'>PURE EDITION</span></h1>", unsafe_allow_html=True)

tabs = st.tabs(["📑 Analyzer", "🎨 Studio", "🔐 Key Vault", "📊 Status"])

# --- TAB: Key Vault ---
with tabs[2]:
    st.markdown("### 🔐 Secure Vault")
    for p in ["Gemini", "Groq"]:
        col1, col2 = st.columns([2, 1])
        with col1: st.session_state.api_vault[p]["key"] = st.text_input(f"{p} Key:", value=st.session_state.api_vault[p]["key"], type="password", key=f"k_{p}")
        with col2: st.session_state.api_vault[p]["label"] = st.text_input(f"Account Label:", value=st.session_state.api_vault[p]["label"], key=f"l_{p}", placeholder="e.g. My Account")
    if st.button("SAVE CONFIGURATIONS 💾"):
        save_to_vault(st.session_state.api_vault)
        st.success("تم الحفظ بنجاح!")

# --- TAB: Analyzer ---
with tabs[0]:
    c1, c2 = st.columns([1, 1.2], gap="large")
    with c1:
        choice = st.selectbox("Select Brain:", ["Google Gemini", "Groq"])
        acc_info = st.session_state.api_vault.get(choice.split()[0], {"key": "", "label": ""})
        
        if acc_info["key"]:
            st.markdown(f"📍 Connected: <span class='account-tag'>{acc_info['label']}</span>", unsafe_allow_html=True)
            try:
                if choice == "Google Gemini":
                    genai.configure(api_key=acc_info["key"])
                    models = [m.name.replace('models/', '') for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
                    active_model = st.selectbox("Model:", models, index=0)
                else:
                    active_model = st.selectbox("Model:", [m.id for m in Groq(api_key=acc_info["key"]).models.list().data])
            except: st.warning("المفتاح غير صحيح.")
            
            files = st.file_uploader("Upload Docs or Images", accept_multiple_files=True)
            user_q = st.text_area("Your Request:")
            if st.button("RUN ANALYSIS 🚀"):
                txt_ctx, img_ctx = "", []
                if files:
                    for f in files:
                        ext = f.name.split('.')[-1].lower()
                        if ext in ['jpg','png','jpeg']: img_ctx.append(Image.open(f))
                        elif ext == 'pdf':
                            pdf = fitz.open(stream=f.read(), filetype="pdf")
                            for page in pdf: img_ctx.append(Image.open(io.BytesIO(page.get_pixmap(matrix=fitz.Matrix(1,1)).tobytes("png"))))
                        else: txt_ctx += process_any_file(f)
                
                with st.spinner("Analyzing..."):
                    res = run_pure_ai(choice, acc_info["key"], active_model, txt_ctx + "\n" + user_q, img_ctx)
                    st.session_state.last_res = res
        else: st.info("يرجى إدخال المفتاح في تاب Key Vault.")

    if 'last_res' in st.session_state:
        with c2:
            st.markdown(f'<div class="result-card">{st.session_state.last_res}</div>', unsafe_allow_html=True)
            st.code(st.session_state.last_res)

# --- TAB: Status ---
with tabs[3]:
    st.markdown("### 📊 System Connection")
    for p, info in st.session_state.api_vault.items():
        st.write(f"**{p}** ({info['label']}): {'✅ Active' if info['key'] else '🔴 Offline'}")
